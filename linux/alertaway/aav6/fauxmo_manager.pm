package fauxmo_manager;
# Copyright 2017, 2023 by James E Dodgen Jr.  All rights reserved.

use DBI;
use DBD::SQLite;
use DBTOOLS;
use db;
use cfg;
use Filesys::Df;
use Data::Dumper;
# use Net::EmptyPort; # qw(empty_port check_port);
use strict;
use tools qw (:debug);
use filterPrint;

use constant DBG => 1;

my $fp = filterPrint->new();

my $port_nbr_base = 52004; # also status port

my $fauxmo_cfg = <<EOF;
{
    "FAUXMO": {
        "ip_address": "%s"
    },
    "PLUGINS": {
        "SimpleHTTPPlugin": {
            "DEVICES": [
                %s
            ]
        }
    }
}
EOF

sub task
{
    my ($trace_in) = @_;
    my $dt = db::open(cfg::DBNAME);
    my $cfg = tools::get_config($dt);
    my $port_nbr_base = $cfg->{wemo_port_base};  # was hard coded 52004; # also status port
    my $ip = ip_tools::get_ip_addr($cfg);
    my @rows = $dt->tmpl_loop_query(<<EOF,  ('rowid', 'location', 'port_name','ip_wemo_nbr'));
       SELECT devices.rowid, wireless_devices.physical_location, devices.port_name, coalesce(devices.ip_wemo_nbr,0)
       FROM devices
       JOIN wireless_devices ON wireless_devices.ah = devices.ah
           AND wireless_devices.al = devices.al
       WHERE devices.allow_wemo = 'checked' AND  devices.port_name > ''
EOF
    $fp->filter();
    if (@rows)
    {
        my @items;
        push @items, 'status:'.$port_nbr_base++;
        push @items, 'commission:'.$port_nbr_base;
        my $devices;
        foreach my $r (@rows)
        {
            my $port;
            if (! $r->{ip_wemo_nbr})
            {
                # need to assign a new ip port number to this device
                # also echo needs to now find it with a "discover devices" ether through alexa.amazon.com or just verbaly
                my ($status, $ip_wemo_nbr) = $dt->get_rec("SELECT coalesce(MAX(ip_wemo_nbr),0) from devices");
                $ip_wemo_nbr++;
                $dt->do("UPDATE devices SET ip_wemo_nbr = %s WHERE rowid = %s",  $ip_wemo_nbr, $r->{rowid});
                $port = $port_nbr_base + $ip_wemo_nbr;
            }
            else
            {
                $port = $port_nbr_base + $r->{ip_wemo_nbr};
            }
            #$devices .= device_json($ip, $cfg->{internal_http_port}, $r->{location},$r->{port_name}, $port).',';
            $devices .= device_json("localhost", $cfg->{internal_http_port}, $r->{location}, $r->{port_name}, $port).',';
        }
        chop $devices;  # remove trailng comma
        DBG&&$fp->prt(  "task: devices %s", $devices);
        my $config_file_path = "/tmp/fauxmo.json";
        open(FH, '>', $config_file_path) or die $!;
        #print FH sprintf($fauxmo_cfg,$ip, $devices);
        print FH sprintf($fauxmo_cfg,"auto", $devices);
        close FH;
        # config files created now we run fauxmo aamemo
        sleep 1;
        #DBG&&$fp->prt( "fauxmo_manager:task: run fauxmo now %s ", $devices);

        while (1)
        {

            exec('/usr/local/bin/fauxmo', '-c',  $config_file_path); # normal  '-vvv', for debug
            exit;
            # my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
            #$WorkerBeeQueue->enqueue({request => "LOG", fmt => "Fauxmo_manger: aamemo died"});

        }
    }
    else # looks like we have no memo devices so just sleep and wait for death
    {
        DBG&&$fp->prt( "fauxmo_manager:task: no memo items so sleeping");
        sleep; #forever
    }
}

my $fauxmo_device = <<EOF;  # wemo_port, name, ip_port,   name, ip_port,
                {
                    "port": %s,
                    "name": "%s",
                    "on_cmd": "http://%s:%s/extern?location=%s&device=%s&action=True",
                    "off_cmd": "http://%s:%s/extern?location=%s&device=%s&action=False",
                    "method": "GET",
                    "use_fake_state": true
                }
EOF

sub device_json
{
    my ($my_ip, $ip_port, $location, $device, $wemo_port) = @_;
    my $device = sprintf($fauxmo_device, $wemo_port, tools::trim($location." ".$device),
                $my_ip, $ip_port, urlencode($location), urlencode($device),
                $my_ip, $ip_port, urlencode($location), urlencode($device)); #, $ip_port, urlencode($name));
    #DBG&&$fp->prt($device);
    return $device;
}
sub urlencode {
    my $s = shift;
    #$s =~ s/ /+/g;
    $s =~ s/([^A-Za-z0-9\+-])/sprintf("%%%02X", ord($1))/seg;
    return $s;
}

#print device_json(23,"foobar for you",4567);


1;
