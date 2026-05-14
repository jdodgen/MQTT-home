package client;
# Copyright 2021 by James E Dodgen Jr.  All rights reserved.
use Net::OpenSSH;
use Carp;
use Data::Dumper;
use db;
use strict;
#use html;
use cfg;
use tools;
use QueueManager;
#use http_processor;
use Text::CSV;
use extern;

use filterPrint;
use constant DBG => 1;
my $fp = filterPrint->new();

use constant SLEEPTIME => 30;
use constant MAXFAILS => 10000;

sub task
{
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $EvaluateQueue = QueueManager::EvaluateQueue();
    my $XbeeSendQueue = QueueManager::XbeeSendQueue();
    my $Watchdog = QueueManager::Watchdog();
    my $dt = db::open(cfg::DBNAME,{debug => 0});
    my $csv = Text::CSV->new();
    my $fail_count = 0;
    while (1)
    {
        my $cfg = tools::get_config($dt);
        my $pan_id = $cfg->{pan_id};
        my $hex_pan_id = sprintf("%x", $pan_id);
        DBG&&$fp->prt("starting SSH connection panid[$hex_pan_id]");
        my $ssh = Net::OpenSSH->new(cfg::FTP_SITE,
            port => cfg::FTP_PORT,
            user => cfg::FTP_USER,
            password => cfg::FTP_PASSWORD,
            master_opts => [-o => "StrictHostKeyChecking=no"]);
        if ($ssh->error) # open failed
        {
            printf "client:  Net::OpenSSH->new failed [%s]\n", $ssh->error;
            $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Client SSH new error [%s]", parms => [$ssh->error]});
            $fail_count++;
        }
        else
        {
            $fail_count = 0;
            my ($input, $out, $pid) = $ssh->open2("perl -I . aaclient.pl $hex_pan_id");
            if ($ssh->error) # open failed
            {               
                printf "client:  open2 failed [%s]\n", $ssh->error;
                $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Client open2 error [%s]", parms => [$ssh->error]});
                $fail_count++;
            }
            else
            {
				while (1)
				{
					my $request = readline($out);
					if ($ssh->error or !$request)
					{
						printf "client:  read error [%s]\n", $ssh->error;
						sleep(SLEEPTIME);
						last;
					}
					else
					{
						chomp $request;
						#DBG&&$fp->prt("read [$request]");
						my $status = $csv->parse ($request);
						DBG&&$fp->prt("raw [%s]", $request);
						my ($sequence, $cmd, @fields) = $csv->fields();
						 #my ($cmd, $data) = split(/\|/, $request);
						DBG&&$fp->prt("split seq[%s] cmd [%s] data[%s]", $sequence, $cmd, join ',',@fields);
						if ($cmd eq 'keepalive')
						{
							# just ignore
						}
						elsif ($cmd eq 'error')
						{
							$WorkerBeeQueue->enqueue({request => "LOG", fmt => "Client recieved error [%s]", parms => [@fields]});
						}
						elsif ($cmd eq 'toggle')
						{
							my ($location, $device, $value) = @fields;
							#my ($device, $value) = split(/\~/, $data);
							DBG&&$fp->prt("toggle [%s][%s]", $device, $value);
							use constant NOT_WEMO => 0;
							extern::do_extern_device($dt, $location, $device, $value, NOT_WEMO, $EvaluateQueue, $XbeeSendQueue);
							print $input "$sequence,ack\n";
						}
						elsif ($cmd eq 'devices')
						{
							# query devices with names and send them in a list
							external_devices_csv($dt, $sequence, $input, $csv);
							#my $send = "devices,".$devices."\n";
							#printf $input $send;
							#printf"[%s]\n",$send;
						}
						else
						{
							printf $input "$sequence,nak\n";
						}
					}
				}
			}
        }
        if ($fail_count > MAXFAILS)
        {
            DBG&&$fp->prt("SSH broke, really sick so requesting reboot");
            update_reason_started($dt, 8, "clent requested reboot SSH connect problems");
            $Watchdog->enqueue({request => 'Reboot'});
        }
        else
        {
            DBG&&$fp->prt("SSH broke, now sleeping and retrying]");
        }
        sleep(SLEEPTIME);
    }
   ;
}

sub external_devices_csv
{
    my ($dt, $sequence, $input, $csv) = @_;
    my @fields = qw(current logic port_name value physical_location);
    my @devices = $dt->tmpl_loop_query(
        <<EOF, @fields);
        --sql
        SELECT devices.current, port_types.logic, devices.port_name, devices.raw_value, wireless_devices.physical_location
        FROM devices
        JOIN wireless_devices ON wireless_devices.ah = devices.ah
           AND wireless_devices.al = devices.al
           AND wireless_devices.part_nbr = port_types.part_nbr
           AND devices.port = port_types.port
        JOIN device_types ON wireless_devices.part_nbr = device_types.part_nbr
        JOIN port_types   ON device_types.part_nbr = port_types.part_nbr
        WHERE devices.port_name IS NOT NULL
        --endsql
EOF
    my $last;    ##  OR port_types.type IS NULL
    # print Dumper $wireless_devices[2];
    my $dev="";
    foreach my $x (@devices)
    {
        $x->{port_on} = "ON";
        $x->{port_off} = "OFF";
        if ($x->{logic} eq "BINARY")
        {
            if ($x->{current})
            {
                 $x->{value} = $x->{current} eq 'ON'?'ON':'OFF';
            }
            else
            {
                 $x->{value} = "Unknown"; #$x->{default_state}?'ON':'OFF';
            }
        }
        if ($x->{logic} eq "VALVE")
        {
            $x->{port_on} = "OPEN";
            $x->{port_off} = "CLOSE";
            if ($x->{current})
            {
                 $x->{value} = $x->{current} eq 'ON'?'Should be Open':'Should be Closed';
            }
            else
            {
                 $x->{value} = $x->{default_state}?'Should be Open':'Should be Closed';
            }

        }
        elsif ($x->{logic} eq "SW1")
        {
            if (defined $x->{value} && $x->{value} == 0)
            {
               $x->{value} = "OPEN";
            }
            else
            {
               $x->{value} = "CLOSED";
            }
        }
        elsif ($x->{logic} eq "SW0")
        {
            if (defined $x->{value} && $x->{value} == 1)
            {
               $x->{value} = "OPEN";
            }
            else
            {
               $x->{value} = "CLOSED";
            }
        }
        elsif ($x->{logic} eq "SIG1")
        {
            if (defined $x->{value} && $x->{value} == 1)
            {
               $x->{value} = "TRUE";
            }
            else
            {
               $x->{value} = "FALSE";
            }
        }
        elsif ($x->{logic} eq "HIGH")
        {

            if (defined $x->{value} && $x->{value} == 1)
            {
               $x->{value} = "ON";
            }
            else
            {
               $x->{value} = "OFF";
            }
        }
        elsif ($x->{logic} eq "LOW")
        {
            if (defined $x->{value} && $x->{value} == 0)
            {
               $x->{value} = "ON";
            }
            else
            {
               $x->{value} = "OFF";
            }
        }
        elsif ($x->{logic} eq "SIG0")
        {
            if (defined $x->{value} && $x->{value} == 0)
            {
               $x->{value} = "TRUE";
            }
            else
            {
               $x->{value} = "FALSE";
            }
        }
        elsif ($x->{logic} eq "OPEN")
        {
            if (defined $x->{value} && $x->{value} == 0)
            {
               $x->{value} = "OPEN";
            }
            else
            {
               $x->{supress_row} = 1;
               $x->{value} = "";
            }
        }
        elsif ($x->{logic} eq "CLOSED")
        {
            if (defined $x->{value} && $x->{value} == 0)
            {
               $x->{value} = "CLOSED";
            }
            else
            {
               $x->{supress_row} = 1;
               $x->{value} = "";
            }
        }
        elsif ($x->{logic} eq "MOMENTARY1")
        {

            $x->{value} = "";
        }

        elsif ($x->{logic} eq "MOMENTARY0")
        {

            $x->{value} = "";
        }
        delete $x->{logic};
        delete $x->{current};

        $csv->combine(clean($x->{physical_location}),clean($x->{port_name}),clean($x->{value}),clean($x->{port_on}),clean($x->{port_off}));
        DBG&&$fp->prt($csv->string());
        print $input "$sequence,device,".$csv->string()."\n";
        #print "device,".$csv->string()."\n";
        #$dev .=  $csv->string()."|";
        #sprintf("%s^%s^%s^%s^%s~", clean($x->{desc}),clean($x->{port_name}),clean($x->{value}),clean($x->{port_on}),clean($x->{port_off}));
    }
    DBG&&$fp->prt('devices done');
    print $input "$sequence,devices done\n";
    #printf "devices,[%d] %s\n", length($dev)+9, $dev;
    return;
}

sub clean
{
    my ($s) = @_;
    $s =~ tr/|\n/  /;
    return tools::trim($s);
}

#print "running test\n";
#my $dt = db::open(cfg::DBNAME);
#my $devices = external_devices_csv($dt);
#print $devices;
#my @lines = split("~",$devices);
#foreach my $l (@lines)
#{
    #print "$l\n";
#}

#task();

1;
