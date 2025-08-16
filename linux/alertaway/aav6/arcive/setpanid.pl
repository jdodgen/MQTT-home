#!/usr/bin/perl -w
# Copyright 2011,2012,2013,2014 by James E Dodgen Jr.  All rights reserved.
use Data::Dumper;
#use forkQueue;
use POSIX ":signal_h";
use DBI;
use DBD::SQLite;
use DBTOOLS;

# use Device::XBee::API ':xbee_flags';
use API ':xbee_flags';
use XBeeZDO;
use Device::SerialPort;
use evaluate;
use ip_tools;
use strict;
use db;
use http_processor;
use route_collection;
use time_keeper;
use processManager;
use motion_manager;
use favicon;
use Net::FTPSSL;
#use image_grabber;
#use ZBcam;
use Time::HiRes qw (usleep);
use Carp;
use valve;
use tools qw (:debug);
use cfg;
use constant DEBUG => tools::DEBUG_HomeMonitor;

### use Devel::Size qw(total_size);

my $system_type="sys";
use constant HOURS24 => 86400;
use constant HOURS12 => 43200;

use constant START_MSG_SENT  => 1;
use constant START_ACKED  => 2;
use constant STOP_MSG_SENT  => 3;
use constant STOP_ACKED  => 4; ## never used, record is deleted when ack is back

my $api;
# $Data::Dumper::Indent = 0;

{
    ###  watchdogTimer();  ## Just for testing

    $SIG{USR1} = "shutDown";

    my $xbee_serial_port;
    my $handshake = "rts";
    my $api_mode_escape;
    my $baud;

    # ip_tools::set_ip_dhcp();


    my $on_rpi=0;
    #if (-d '/root/test') # test system, causes only test000.tar.gz to be downloaded
    #{
        #$system_type="test";
    #}
    #if (-d '/root/rpi_arch') # Raspberry pi versions
    #{
        #$xbee_serial_port = '/dev/ttyAMA0';
        #$baud = 115200;
        #$handshake = "rts";
        #$on_rpi=1;
        #require Device::BCM28set_ipdt35; # on the rpi we are using p1-15 to do a hw reset of the xbee to get things going,
        #Device::BCM2835::init()
              #|| die "Could not init library";
        ## Set RPi pin 11 to be an output
        #Device::BCM2835::gpio_fsel(&Device::BCM2835::RPI_GPIO_P1_15,
                                #&Device::BCM2835::BCM2835_GPIO_FSEL_OUTP);
    #}
    #else   # x86 computer with USB connected XBee
    {
        $xbee_serial_port = '/dev/ttyUSB0';
        $baud = 115200; # 38400;
    }
    # print Dumper $WorkerBeeQueue;

    # these two lines moved to alertaway_init.pl which runs as root.
    # db::create_or_copy( cfg::DBNAME, cfg::SAVE_DATABASE_AS);
    # my ($WorkerBeeQueue, $XbeeSendQueue, $TraceQueue, $EmailQueue, $DelayQueue, $ProcessMsgQueue, $PacketQueue) = QueueManager::create_message_queues();

    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $PacketQueue = QueueManager::PacketQueue();

    my ($starting_config, $dt) = initialize($WorkerBeeQueue);

    # Now spawn off the worker processes

    processManager::startAllNoXbee($dt, $starting_config->{trace}, $WorkerBeeQueue);

    $WorkerBeeQueue->enqueue({request => 'REASON_STARTED', code => 0, descr => "Unknown, Possible crash"});


    my $serial_port_device = Device::SerialPort->new($xbee_serial_port) || die "Could not open serial port [$xbee_serial_port] connected to the XBee ", $!;
     $serial_port_device->baudrate( $baud );
     $serial_port_device->databits( 8 );
     $serial_port_device->stopbits( 1 );
     $serial_port_device->parity( 'none' );
     $serial_port_device->read_char_time( 0 );        # don't wait for each character
     $serial_port_device->read_const_time( 2000 );    # 1000 == 1 second per unfulfilled "read" call
     $serial_port_device->handshake( $handshake );
    $api = API->new( { fh => $serial_port_device, api_mode_escape => 1 } ) || die " could not open XBee API ", $!;
    #my $api = Device::XBee::API->new( { fh => $serial_port_device, auto_reuse_frame_id => 1 } ) || die " could not open XBee API ", $!;
    printf("hm: XBee serial opened\n");

    my $reset_count = 0;
    while (1)
    {
        if ($on_rpi) # do a HW reset
        {
            Device::BCM2835::gpio_write(&Device::BCM2835::RPI_GPIO_P1_15, 1);
            Device::BCM2835::delay(500); # Milliseconds  $ must be 200 ms or more
            Device::BCM2835::gpio_write(&Device::BCM2835::RPI_GPIO_P1_15, 0);
            sleep 5;
        }
        my @saved_packets;
        while (1) # flush input queue
        {
          my ($t, $packet) = $api->read_packet();
          if ($t)
          {
              last;
          }
          printf(".");
          push @saved_packets, $packet;
        }
        print "\n";
        # now request the ID and wait for a reply
        die "Failed to transmit PAN_ID READ  request"
             unless $api->at('ID');    # echo back pan_id
        my ($t, $packet) = $api->read_packet();
        if ($t)
        {
             exit if ($reset_count++ > 30);
             printf("hm: Unable to access Xbee\n");
             next;
        }
        my ($error, $rxin) = $api->parse_packet($packet);
        $PacketQueue->enqueue($packet);
        printf("hm: XBee communicating, packet returned\n");
        foreach my $p (@saved_packets)
        {
            $PacketQueue->enqueue($p);
        }
        last;
    }
    my $XbeeSendQueue = QueueManager::XbeeSendQueue();
    if ($ARGV[0] && $ARGV[1] && $ARGV[2] && $ARGV[3]) # are we resetting the PAN ID?
    {
       print "setting coordinator values\n";
       my $pan_id = hex $ARGV[0];
       my $pan_id_16 = hex $ARGV[1];
       my $operating_channel = hex $ARGV[2];
       my $stack_profile = hex $ARGV[3];

       tools::set_coordinator_configuration($XbeeSendQueue,
            $pan_id, $pan_id_16, $operating_channel, $stack_profile);
    }

    $serial_port_device->read_const_time( 20000 );    # 1000 == 1 second per unfulfilled "read" call

    #my constant $all_nodes = pack( 'C', 1);
    #$XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'NR'});
    #die "Failed to reset network request"
    #    unless $api->at('NR', $all_nodes);    # network reset
    #sleep 4;pan

    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'SL'}); # lo part of id

    #die "Failed to transmit SL request"
    #    unless $api->at('SL');    # echo back pan_id
    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'SH'});
    #die "Failed to transmit SH requwatchdogTimer();est"
    #    unless $api->at('SH');    # echo back pan_id

    # $XbeeSendQueue->enqueue({request => 'SEND_NODE_DISCOVERY'});

    processManager::startAllWithXbee($dt, $api, $WorkerBeeQueue);
}
my $shut_down_in_progress = 0;
watchdogTimer();
sleep(2);
exit 0;


# The end of the main process

sub xbee_reader  ## runs as a seperate process
{
    my ($trace_in, $api_in) = @_;
    my $api = $api_in;
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $PacketQueue = QueueManager::PacketQueue();

    #my $tracer=Tracer->new({name => 'xbee_reader', trace => $trace_in, TraceQueue => $TraceQueue});
    my $timeout_count = 0;
    my $reboot_xbee_count = 0;
    my $received_AT_COMMAND_RESPONSE_yet = 0;
    while ( 1 )
    {
        my ($timeout, $packet) = $api->read_packet();
        if ($timeout)
        {
            # print "hm:xbee_reader:null returned from xbee read:  status = $packet\n" if DEBUG;
            if ($timeout_count > 100)
            {
                reboot_this_xbee($reboot_xbee_count, $WorkerBeeQueue);
                $reboot_xbee_count++;
                $timeout_count=0;
            }
            $timeout_count++;
            #printf("hm:xbee_reader:timed out, sending ND\n") if DEBUG;
            #$XbeeSendQueue->enqueue({request => 'SEND_NODE_DISCOVERY'});
        }
        else
        {
            #print "hm:xbee_reader: enqueue packet\n" if DEBUG;
            $PacketQueue->enqueue($packet);
            $reboot_xbee_count=0;
            $timeout_count=0;
        }
    }
}


# this is the main processing loop for reading from the xbee, all reading must be done here,
# this is running as a seperate process
sub xbee_dispatch
{
    my ($trace_in) = @_;
    my $PacketQueue = QueueManager::PacketQueue(my $reader = 1);
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $ProcessMsgQueue = QueueManager::ProcessMsgQueue();


    #my $tracer=Tracer->new({name => 'xbee_dispatch', trace => $trace_in, TraceQueue => $TraceQueue});
    my $msg_in_cnt = 0;
    my $max_queue  = 0;
    my $timeout_count = 0;
    my $reboot_xbee_count = 0;
    my $received_AT_COMMAND_RESPONSE_yet = 0;
    my $last_wakeup = 0;
    while ( 1 )
    {
        #my $rxin = $api->rx();
        #my ($error, $packet) = $api->read_packet();
        my $packet = $PacketQueue->dequeue();

        #if (!$error)
        {
            my ($error, $rxin) = $api->parse_packet($packet);
            if ($error)
            {
                printf("hm:xbee_dispatch:PARSE PACKET ERROR %s\n", $error) if DEBUG;
                next;
            }
            printf"hm:xbee_dispatch:Dumping %s", Dumper $rxin if DEBUG;
            #delete $rxin->{data};
            if ($rxin->{api_type} &&  $rxin->{sl} && $rxin->{sl} == 0x41664ee5)# && $rxin->{api_type} != 0x97)
            {
                printf"hm:xbee_dispatch:Dumping %x %x:%x\n", $rxin->{api_type}, $rxin->{sh}||"0", $rxin->{sl}||"0" if DEBUG;
                print Dumper $rxin if DEBUG;
            }
            if ($rxin->{api_type} == 0x90 || ($rxin->{api_type} == 0x91 && $rxin->{cluster_id} == 0x11)) # data packet
            {
                 $rxin->{cmd} = "MSG";
                 printf "hm:xbee_dispatch: Got a data packet api_type = %0X sl = %0X\n", $rxin->{api_type}, $rxin->{sl} if DEBUG;
                 next;
            }
            my $string_type =  XBEE_API_TYPE_TO_STRING->{$rxin->{api_type}};
            #printf "hm:xbee_dispatch:API type = %0X %s\n", $rxin->{api_type}, $string_type if DEBUG;
            if ($received_AT_COMMAND_RESPONSE_yet == 0 && $rxin->{api_type} == 0x88) # AT_COMMAND_RESPONSE
            {
                 ## on occasion the sender gets out of sync and commands are not processed
                 ## this is fixed by doing a reboot
                 ## the worker bee process is waiting for this process to tell it things are fine
                 ## if it does not get a message indicating that we got a reply it will reboot shortly
                 $received_AT_COMMAND_RESPONSE_yet = 1;
                 printf("hm:xbee_dispatch:GOOD_XBEE_COMM sent\n") if DEBUG;
                 $WorkerBeeQueue->enqueue({request => 'GOOD_XBEE_COMM'});
            }

            elsif ($rxin->{api_type} == 0x8a)
            {
                 printf "hm:xbee_dispatch:Modem Status: %s\n", Dumper $rxin if DEBUG;
            }
            elsif ($rxin->{api_type} == 0x91)
            {
                 # printf("hm:xbee_dispatch:ZDO [0x91] %x:%x cluster_id = 0x%0X data %s\n", $rxin->{sh}, $rxin->{sl}, $rxin->{cluster_id},unpack("H*", $rxin->{data})) if DEBUG;
            }
            if ($rxin->{sh})
            {
                printf("hm:xbee_dispatch:%s: %0X:%0X\n", $string_type, $rxin->{sh},$rxin->{sl}) if DEBUG;
            }
            elsif ($rxin->{remote_sh})
            {
                printf("hm:xbee_dispatch:%s: %0X:%0X\n", $string_type, $rxin->{remote_sh},$rxin->{remote_sl}) if DEBUG;
            }
            else
            {
                printf("hm:xbee_dispatch:%s\n", $string_type) if DEBUG;
            }

            if ($rxin->{status})
            {
                printf("hm:xbee_dispatch:... status = %s\n", $rxin->{status}) if DEBUG;
            }
            my $now = time;
            $rxin->{timestamp} = $now;
            $ProcessMsgQueue->enqueue($rxin);
            undef $rxin;
            #if ($now - $last_wakeup > 2)
            #{
                #$DelayQueue->enqueue({queue => 'WakeUp'});
                #$last_wakeup = $now;
            #}
            $msg_in_cnt++;
            $reboot_xbee_count=0;
            $timeout_count=0;
        }

    }
    printf("hm:xbee_dispatch:exiting\n") if DEBUG;
}

sub reboot_this_xbee
{
   my ($reboot_xbee_count, $WorkerBeeQueue, $XbeeSendQueue) = @_;

   if ($reboot_xbee_count > 10)
   {
       $WorkerBeeQueue->enqueue({request => 'REASON_STARTED', code => 1, descr => "reboot"});
       printf("hm:reboot_this_xbee: shuting down for reboot\n");
       shutDown();
       ## use this if not main thread # kill(POSIX::SIGUSR1, getppid());   # causes shutdown to be run in parent process, usualy fixes things
   }
   else
   {
       $WorkerBeeQueue->enqueue({request => "LOG",
                                 fmt => "timed out=$reboot_xbee_count, resetting XBee software to fix problem"});
       $XbeeSendQueue->enqueue({request => 'XBEE_AT_READ', cmd => 'FR'});
       sleep(10);
   }
}




#sub drop_and_email_delayed_image
#{
    #my ($now, $key, $image) = @_;
    #my $seconds = $now - $image->{start_time};
    #my $minutes = sprintf"%.2f",$seconds / 60;
    #printf("hm:drop_and_email_delayed_image:got complete image, in = %s minutes\n", $minutes) if DEBUG;
    #my ($image_path, $jpeg_size) = ZBcam::drop_image($key, $image->{name}, \@{$image->{data}});
    #if ($image->{email_info})
    #{
         #my $subject = $image->{email_info}{subject_head}."Delayed Picture";
         #my $body = sprintf"Hello\nHere is a picture from \"%s\" taken: \"%s\"\n[%s:%s:%s:%s]\n",
           #$image->{email_info}{camera_name},
           #scalar localtime($image->{email_info}{picture_date}),
           #$seconds, $minutes,
           #$image->{retries},
           #$jpeg_size;
         #$EmailQueue->enqueue({cmd => 'simple', subject => $subject,
                 #text_body => $body,
                 #to => $image->{email_info}{to},
                 #attach => [$image_path]})
    #}
#}

#sub check_and_request_missing_image_pieces
#{
    #my ($key, $seq, $image) = @_;
    #my @missing;
    #my $previous_last_requested = $image->{last_requested};
    #my $now = time;
    #printf"hm:check_and_request_missing_image_pieces: seq = %s pieces = %s\n", $seq, $image->{pieces} if DEBUG;   ### error here pieces seems to be null
    #for (my $i =1; $i <= $image->{pieces}; $i++)
    #{
      #if (! $image->{data}[$i])
      #{
          #push @missing, $i;
          #$image->{last_requested} = $i;
          #if ($i <= $previous_last_requested)
          #{
             #$image->{retries}++;
          #}
      #}
    #}
    #my ($ah, $al) = split /\:/, $key;
    #if (@missing)
    #{
      #my $string = convert_missing_to_string(@missing);
      ## print "hm:check_and_request_missing_image_pieces:.... requesting missing $string\n" if DEBUG;
      #$XbeeSendQueue->enqueue({request => 'IMAGEMORE', ah => $ah, al => $al, missing => $string, seq => $seq});
      #$image->{time} = $now;
      #return $key, $seq;
    #}
    #$XbeeSendQueue->enqueue({request => 'IMAGEDONE', ah => $ah, al => $al, seq => $seq});
    #return undef, undef;
#}

sub convert_missing_to_string
{
      my (@missing) = @_;
      my $string;
      my $start_range;
      my $last = shift @missing;
      push @missing, 9999999999; # dummy at the end
      foreach my $i (@missing)
      {
         if ($last + 1 == $i)
         {
             if (!$start_range)
             {
                 $start_range = $last;
             }
         }
         else
         {
             my $piece;
             if ($start_range)
             {
                 $piece = $start_range.'-'.$last;
             }
             else
             {
                 $piece = $last;
             }
             $start_range = undef;
             printf"hm:convert_missing_to_string:piece = [%s]\n", $piece if DEBUG;
             if ($string && length($string.$piece) > 70)
             {
                 last;
             }
             $string .= $piece.',';
         }
         $last = $i;
      }
      chop $string;
      printf"hm:convert_missing_to_string:%s lth= %s\n", $string, length($string) if DEBUG;
      return $string;
}


sub no_ni_problem
{
      my ($type, $addr_h, $addr_l, $WorkerBeeQueue) = @_;
      $WorkerBeeQueue->enqueue({request => "LOG", fmt => "no NI for %0X - %0X:%0X", parms => [$type, $addr_h, $addr_l]});
      ## reboot_remote_xbee($addr_h, $addr_l);
}



sub watchdogTimer
{
    ## setpriority(0,$$, 2); # run at lower than normal priority
    sleep(1);
    my $dt = db::open(cfg::DBNAME);
    my $DelayQueue = QueueManager::DelayQueue(my $read_write = 2);
    my $ProcessMsgQueue = QueueManager::ProcessMsgQueue();
    my $PacketQueue = QueueManager::PacketQueue();
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $XbeeSendQueue = QueueManager::XbeeSendQueue();
    my $TraceQueue = QueueManager::TraceQueue();
    my $count=0;
    my $led_state=0;
    my $toggle = 0;
    my @delayed; #keeps send_time, enqueue_queue, repeat to and the hash_to_send
              # if repeat = 1 or more decrement and remove when it hits zero
              # if repeat = 0 repeat forever then it is just updated in  delayed with a new time now + offset
    my $start_time = time;
    #put the repeat items in delayed
    $DelayQueue->enqueue({queue => 'WorkerBeeQueue', send_time => $start_time+10, repeat => 0, interval => 60, request => 'WATCHDOG WAKEUP'});
    $DelayQueue->enqueue({queue => 'HEALTH', send_time => $start_time+10, repeat => 0, interval => 20});
    #if ($on_rpi) # only used on daughter card attached to raspberry pi
    #{
        #$DelayQueue->enqueue({queue => 'XBee_heart_beat', send_time => $start_time, repeat => 0, interval => 3});
    #}
    $DelayQueue->enqueue({queue => 'DataQueue', cmd => 'watchdog', send_time => $start_time+10, repeat => 0, interval => 24});
    $DelayQueue->enqueue({queue => 'ProcessMsgQueue', reset => 1, send_time => $start_time+1200, repeat => 0, interval => 1200});


    # now we go to work
    while (1)
    {
        #print "hm::watchdog now waiting on DelayQueue\n" if DEBUG;
        while (1)
        {
            my $req = $DelayQueue->dequeue(2);   #note that this is setup with a time-out so it can process other time dependent stuff
            #printf"hm:watchdogTimer: awake reason = %s\n", $req?$req->{queue}:"TIMED OUT" if DEBUG;
            if ($req && $req->{queue} eq "restart_process")
            {
                print "hm:watchdogTimer: restart_process [".$req->{process}."]\n";
                processManager::killandrestart($dt, $req->{process});
                next;
            }
            if (!$req || $req->{queue} eq "WakeUp")
            {
                # print "hm:watchdogTimer: timed out, now going to processing our saved stuff\n" if DEBUG;
                $toggle = 0;   # speed up the check time
                last;
            }
            if ($req && $req->{queue} eq "PUSH_TOGGLE")
            {
                $toggle = 5;   # skip the evaluation for a while
                next;
            }
            printf"hm:watchdogTimer: putting into delayed = %s\n", $req->{queue} if DEBUG;
            my $replaced;
            foreach my $element (@delayed) ## look for a hole in array
            {
                if (! $element)
                {
                    $element = $req;
                    print "hm:watchdogTimer: replacing into delayed\n" if DEBUG;
                    $replaced = 1;
                    last;
                }
            }
            push @delayed, $req if (!$replaced);
        }

        my $now = time;

        if ($toggle-- < 1)
        {
            $toggle = 5;
            $ProcessMsgQueue->enqueue({evaluate => 1});
            print "hm:watchdogTimer: sent device evaluation message\n" if DEBUG;
        }
        # now scan $delayed for something to re-queue
        # or do internal like flesh the LED (heartbeat) and check the health

        foreach my $element (@delayed)
        {
            if ($element)
            {
                my $destination = $element->{queue};
                if ($element->{send_time} <= $now)  # looks like it is ready
                {
                    printf"hm:watchdogTimer: checking delay,  sending [%s]\n", $destination if DEBUG;
                    if ($destination eq 'PacketQueue')          {$PacketQueue->enqueue($element);}
                    elsif ($destination eq 'ProcessMsgQueue')   {$ProcessMsgQueue->enqueue($element);}
                    # elsif ($destination eq 'DataQueue')         {$DataQueue->enqueue($element);}
                    elsif ($destination eq 'WorkerBeeQueue')    {$WorkerBeeQueue->enqueue($element);}
                    elsif ($destination eq 'XbeeSendQueue')     {$XbeeSendQueue->enqueue($element);}
                    elsif ($destination eq 'TraceQueue')        {$TraceQueue->enqueue($element);}
                    elsif ($destination eq 'HEALTH')
                    {
                        if (processManager::checkHealth($dt, $WorkerBeeQueue)) # something nasty, so reboot to really clean things out
                        {
                          $WorkerBeeQueue->enqueue({request => 'REASON_STARTED', code => 1, descr => "reboot to fix dead process"});
                          $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Process died, causing reboot"});
                          print "hm:watchdogTimer: bad health a process has died, so shutting down\n" if DEBUG;
                          shutDown();
                          # this never returns
                        }
                    }
                    elsif  ($destination eq 'XBee_heart_beat')
                    {
                        $XbeeSendQueue->enqueue({request => 'XBEE_ALIVE_LED', state => $led_state});
                        $led_state = 1 - $led_state;
                    }

                    # now we decide if we delete or update
                    $element->{send_time} = $now + $element->{interval};
                    if (! $element->{repeat})  # zero
                    {
                        # print "hm:watchdogTimer:delay updated, forever\n" if DEBUG;
                    }
                    else # a value greater than zero
                    {
                        $element->{repeat}--;
                        printf"hm:watchdogTimer: delays left %s\n", $element->{repeat} if DEBUG;
                        if ($element->{repeat}) # hit zero
                        {
                           $element = undef; # remove from array
                           print "hm:watchdogTimer: delay removed\n" if DEBUG;
                        }
                    }
                }
            }
        }
    }
}

sub shutDown
{
  if ($shut_down_in_progress)
  {
      print "hm:shutDown: in progress, additional request ignored\n";
      return;
  }
  $shut_down_in_progress=1;


  printf STDERR ("hm:shutDown: shutting down for reboot\n");
  my $dt = db::open(cfg::DBNAME);
  sleep(10);
  db::backup($dt, cfg::SAVE_DATABASE_AS);
  processManager::killAll();
  print "hm:shutDown: exitcode 1\n";
  exit 1;
}


# this runs as a seperate process, it is non real-time in that provessing messages can take various amounts of time.

sub worker_bee
{
    my ($trace_in) = @_;
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue(my $reader = 1);
    my $XbeeSendQueue = QueueManager::XbeeSendQueue();
    my $EmailQueue = QueueManager::EmailQueue();
    my $fresh_started = 1;
    my $backup_db_frequency = 0;
    my $db_changed=0;
    my $call_home_loop_counter = 0;
    my $good_xbee_comm = 0;
    my $delay_time = time + 600;
    my $good_xbee_time = time + 60 * 3;
    my $dt = db::open(cfg::DBNAME);
    my $current_ip_address;
    my $primary_email="";
    #my  $tracer=Tracer->new({name => 'worker_bee', trace => $trace_in, TraceQueue => $TraceQueue});
    my $email_status_time = get_first_status_time();
    ##   for testing uset_ippload_database($tracer,$dt);
    my $get_network_frequency = 99999;  # force a net scan at first watchdog wakeup
    while ( 1 )
    {
        my $q = $WorkerBeeQueue->dequeue();
        if (!$q)
        {
            print "worker_bee null dequeue ?\n";
            next;
        }

        $call_home_loop_counter++;
        my $config = tools::get_config($dt);
        my $now = time;
        #my $msg; eval $raw;
        #my $q = $msg;
        printf("hm:worker_bee: processing [%s]\n", $q->{request}||Dumper \$q) if DEBUG;
        if ($q->{request} eq "RecordLastTimeIn") ## from camera processor for now
        {
            printf("hm:worker_bee: processing [%s]\n", $q->{request}||Dumper \$q);
            #process_packet::record_last_time_in($dt, $XbeeSendQueue, $WorkerBeeQueue,
                #$q->{sh}, $q->{sl}, $q->{time_in}, $q->{current_part_nbr});
        }
        elsif ($q->{request} eq "LOG")
        {
            my $msg = $q->{fmt};
            if ($q->{parms})
            {
                $msg = sprintf($q->{fmt}, @{$q->{parms}});
            }
            my ($status, $smallest_row, $count) = $dt->get_rec("select min(rowid), count(*) from errors");
            my $rows_to_keep = 50;
            if ($status == 1 && $count > $rows_to_keep)
            {
                my $rows_to_remove = $count - $rows_to_keep;
                $dt->do("delete from errors where rowid in (select rowid from errors order by time asc limit %s);", $rows_to_remove);
            }
            $dt->do("INSERT INTO errors (time, message) values (%s,%s)", time, $msg);
            printf("hm:worker_bee: logged error message  [%s]\n", $msg) if DEBUG;
        }
        elsif ($q->{request} eq 'REASON_STARTED')
        {

            printf("hm:worker_bee:Setting REASON_STARTED [%s] [%s]\n",  $q->{code}, $q->{descr}) if DEBUG;
            $db_changed=update_reason_started($dt, $q->{code}, $q->{descr});
            next;
        }
        elsif ($q->{request} eq 'SAVE_PROCESS')
        {
            $dt->do("INSERT or REPLACE INTO processes (name, pid) VALUES (%s,%s)", $q->{name}, $q->{pid});
            next;
        }
        elsif ($q->{request} eq 'IP_PROBLEM')
        {
            # need to decide to reset the IP address,
            # most likly if we are already DHCP we will just ignore
            # best check would be to see if it was ever good?
            # so when setting a IP we should then
        }
        elsif ($q->{request} eq 'WAN_ACTIVITY')
        {
            my ($status, $last_date) = $dt->get_rec("SELECT date FROM wan_activity WHERE ip_addr = %s", $q->{ip});
            if ($status == 0)
            {
                $dt->do('INSERT into wan_activity (ip_addr, hits, date) VALUES (%s,%s,%s)', $q->{ip}, 1, $now );
            }
            else
            {
                if ($last_date+30 < $now)  # ignore recent hits last 20 seconds?
                {
                    $dt->do('UPDATE wan_activity SET hits = hits + 1, date = %s WHERE ip_addr = %s', $now, $q->{ip});
                }
            }
        }
        elsif ($q->{request} eq 'DB_CHANGED')
        {
            $db_changed=1;
        }
        elsif ($q->{request} eq 'WATCHDOG WAKEUP')
        {
           $backup_db_frequency++;
           $get_network_frequency++;
           if ($backup_db_frequency > 19 && $db_changed == 1)    # every twenty sleep cycles we back up, if needed
           {
                db::backup($dt, cfg::SAVE_DATABASE_AS);
                printf("hm:worker_bee:database backup complete\n") if DEBUG;
                $backup_db_frequency = 0;
                $db_changed=0;
            }
            if ($get_network_frequency > 200)
            {
                $get_network_frequency = 0;
                route_collection::get($dt,$XbeeSendQueue);
            }

            printf "hm:worker_bee Daily checks now = %d > when %d\n",  $now, $email_status_time if DEBUG;
            if ($now > $email_status_time)  # time to send the daily status email as well as a few other late night tasks
            {
                printf "hm:worker_bee doing checks and email\n";
                $email_status_time = $email_status_time + HOURS24;  # set for the next time
                my $id = tools::system_string($config->{pan_id}, $config->{ident});
                email::email_daily_status($dt, $WorkerBeeQueue, $EmailQueue, "Daily status", "Good morning, here is your daily status");
                print "hm:worker_bee:midnight backup\n";# if DEBUG;
                #Tracer::cleanup($dt);
                db::backup($dt, cfg::SAVE_DATABASE_AS);
                upload_database($dt);
                route_collection::clean($dt);
                route_collection::get($dt,$XbeeSendQueue);
            }
            check_timers($now, $dt, $XbeeSendQueue);
            $EmailQueue->enqueue({cmd => 'reminder_check', event_time => 0});
        }
        elsif ($q->{request} eq 'BACKUP_NOW')
        {
            print "hm:worker_bee:backup now\n" if DEBUG;
            db::backup($dt, cfg::SAVE_DATABASE_AS);
            printf("hm:worker_bee:database backup complete\n") if DEBUG;
        }
        elsif ($q->{request} eq 'BACKUP_SOON')
        {
            $db_changed = 1;
            $backup_db_frequency = 10;
        }
        elsif ($q->{request} eq 'GOOD_XBEE_COMM')
        {
            printf("hm:worker_bee:processed GOOD_XBEE_COMM\n") if DEBUG;
            $good_xbee_comm = 1;
        }

       ## end of message processing, now do other non time critical checks


        # is it time to phone home?
        if ($config->{pan_id} && $call_home_loop_counter > 15) # must have this first
        {
          # printf"hm:worker_bee:pan_id = %0X\n", $pan_id if DEBUG;
          my $pe = $dt->trim($config->{primary_contact});
          my $cip = ip_tools::get_ip_addr($config, $WorkerBeeQueue);
          if ($config->{ip_set_status} != 0 || ($config->{connection_type} eq 'STATIC IP' && $cip ne  $config->{static_ip}))
          {
              my $ip_status = ip_tools::set_ip($dt);  ## try again
              if ($ip_status == 0)  # good it worked this time
              {
                  $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Retry of primary IP set now worked"});
                  printf("hm:worker_bee:Retry of primary IP set now worked\n") if DEBUG;
                  $dt->do("update config set ip_set_status = 0");
              }
          }
          print "hm:worker_bee: IP address = $cip\n" if DEBUG;
          #if (($primary_email ne $pe) # if it has changed then phone home now
              #|| (!$current_ip_address || $current_ip_address ne $cip)
              #|| $call_home_loop_counter > 15)
          {
              $call_home_loop_counter = 0;
              $primary_email = $pe;
              $current_ip_address = $cip;

              my ($status, $parms) = tools::phone_home($dt, $config, $cip, $system_type, $WorkerBeeQueue);
              if ($status)
              {
                  time_keeper::fix_time($dt, $parms->{time});
                  if ($parms->{send_db})
                  {
                      db::backup($dt, cfg::SAVE_DATABASE_AS);
                      upload_database($dt);
                  }
                  if ($parms->{reboot})
                  {
                     update_reason_started($dt, 8, "Phone home requested reboot");
                     kill(POSIX::SIGUSR1, getppid());  # causes graceful shutdown to be run in parent process
                  }
                  if ($parms->{pull_db}) # this is a request to pull a db from alertaway.com and use it. a little complex also causes a reboot.
                  {
                      download_database($dt);
                      kill(POSIX::SIGUSR1, getppid());  # causes graceful shutdown to be run in parent process
                  }
                  my $server_version = sprintf("%d",$parms->{version});
                  my $default_email =$dt->trim($parms->{default_email});
                  $dt->do('update config set server_version = %s, default_email = %s', $server_version, $default_email);
                  printf("hm:worker_bee:Server version = %d, local version = %d problem = %s problem version = %s\n",
                      $server_version, $config->{version_number}, $parms->{upgrade_problem}||'NONE', $parms->{problem_server_version_number}||'N/A') if DEBUG;

                  # now lets do somthing with the default email, if it exists.

                  if ($default_email ne '' && ($pe eq '' || $pe eq 'none')) # we have one from alertaway.com an no primary has been set so fix it
                  {
                     printf("hm:worker_bee:setting default email to primary [%s]\n", $default_email) if DEBUG;
                     $dt->do('update config set primary_contact = default_email');
                     $config->{primary_contact} =  $default_email;  # might need this below
                     $dt->do('insert or replace into  emails (contact, email_address) values ("Default email", %s)',  $default_email);
                  }
                  if ($fresh_started == 1)
                  {
                     my ($restart_code, $restart_descr) = tools::get_restart_reason($dt);
                     ## evaluate::email_to_contacts($tracer, $dt, "AlertAway starting", "Restart because of - $restart_descr");
                     # my $id = tools::system_string($config->{pan_id}, $config->{ident});
                     email::email_daily_status($dt, $WorkerBeeQueue, $EmailQueue, "Starting", "Restart because of - $restart_descr");
                     $fresh_started = 0;
                  }
                  if ($config->{upgrade_problem})
                  {
                      if ($server_version == $parms->{problem_server_version_number} && $now > ($config->{process_start_time} + (3600*24)))
                      {
                          # ignore for now, we will check back in 24 hours, this keeps us out of a reboot loop
                      }
                      else # an even newer version that the problem version
                      {
                          printf("hm:worker_bee:time to upgrade (problem), backing up and exiting process\n") if DEBUG;
                          $dt->do("INSERT INTO errors (time, message) values (%s,%s)", $now, "rebooting for software upgrade");
                          $db_changed = update_reason_started($dt, 3, "Software upgrade, from problem");
                          $db_changed=0;
                          $EmailQueue->enqueue({cmd => 'to_primary', subject => "AlertAway upgrade", event_time => 0,
                              msg => "AlertAway upgrade","The AlertAway Software is restarting to install a upgrade\nFrom version $config->{version_number}, to version $server_version\n"
                                   });

                          #evaluate::email_to_contacts($dt, $WorkerBeeQueue,  $XbeeSendQueue,
                          #"AlertAway upgrade","The AlertAway Software is restarting to install a upgrade\nFrom version $config->{version_number}, to version $server_version\n");
                          kill(POSIX::SIGUSR1, getppid());   # causes shutdown to be run in parent process
                          sleep 99;
                      }
                  }
                  elsif ($server_version > $config->{version_number})  # looks like it is upgrade time
                  {
                     printf("hm:worker_bee:time to upgrade, backing up and exiting process\n") if DEBUG;
                     $dt->do("INSERT INTO errors (time, message) values (%s,%s)", $now, "rebooting for software upgrade");
                     $db_changed = update_reason_started($dt, 4, "Software upgrade");
                     $EmailQueue->enqueue({cmd => 'to_primary', subject => "AlertAway upgrade", event_time => 0,
                         msg => "AlertAway upgrade, \"The AlertAway Software is restarting to install a upgrade\nFrom version $config->{version_number}, to version $server_version\n"});

                     # evaluate::email_to_contacts($dt, $WorkerBeeQueue,  $XbeeSendQueue, "AlertAway upgrade", "The AlertAway Software is restarting to install a upgrade\nFrom version $config->{version_number}, to version $server_version\n");
                     sleep 1;
                     kill(POSIX::SIGUSR1, getppid());  # causes graceful shutdown to be run in parent process
                     sleep 99
                  }
              }
              else
              {
                  my $time_to_fail = time - $now;
                  printf("hm:worker_bee:problem with phone home, nothing done time to fail %s\n", $time_to_fail) if DEBUG;
                  # next;
              }
          }
        }

        if ($now > $good_xbee_time && $good_xbee_comm == 0)  # not good looks like xbee sending is out of sync, best to reboot
        {
            printf("hm:worker_bee: xbee sending is out of sync, best to reboot\n") if DEBUG;
            $dt->do("INSERT INTO errors (time, message) values (%s,%s)", $now, "rebooting to fix xbee send problem");
            update_reason_started($dt, 9, "XBee comm problem");
            kill(POSIX::SIGUSR1, getppid());   # causes shutdown to be run in parent process
            sleep 99;
        }


        # current thought is to delay a short time after a restart just to give devices time to check in
        # so I need to use $now and well as the start time, a minute should do it
        # check three tables for problems sensor, wireless devices, and devices
        $delay_time=0;
        if ($now > $delay_time)
        {

            printf"hm:worker_bee: checking for lost devices\n" if DEBUG;
            my @devices =  $dt->tmpl_loop_query(<<EOF, (qw(rowid addr_h addr_l last_time_in loc desc allowed_away_time time_reported_gone network_addr parent_addr part_nbr)));
            SELECT wireless_devices.rowid, wireless_devices.ah, wireless_devices.al, wireless_devices.last_time_in,
                   wireless_devices.physical_location, device_types.desc,
                   device_types.allowed_away_time,wireless_devices.time_reported_gone,
                   wireless_devices.my_network_address,
                   wireless_devices.parent_network_address,
                   wireless_devices.part_nbr
            FROM wireless_devices
            JOIN device_types ON wireless_devices.part_nbr = device_types.part_nbr
EOF
            # print Dumper "hm:worker_bee:devices ", @devices, "\n" if DEBUG;

            my $problem_reporting_frequency = tools::get_config($dt)->{problem_reporting_frequency};
            my $allowed_prf_seconds = $problem_reporting_frequency * 60; # convert to seconds
            my $its_time_to_ignore = HOURS12;

            foreach my $d (@devices)
            {
                # printf"hm:worker_bee: lost check time is = $now\n";  printf"\t %s [%s]\n", $_, $d->{$_}||'?' for (keys $d) if DEBUG;
                if (!$d->{network_addr}) # while we are here lets do this
                {
                    route_collection::single($XbeeSendQueue, $d->{part_nbr}, $d->{addr_h}, $d->{addr_l});
                }

                if ($d->{allowed_away_time} > 0 && $d->{last_time_in} < ($now - $d->{allowed_away_time})) # looks like a device has gone away
                {
                    printf "hm:worker_bee: lost check gone too long\n" if DEBUG;
                    if ($d->{time_reported_gone})  # it has been reported gone
                    {
                       #printf "hm:worker_bee: lost check and has been reported\n" if DEBUG;
                       #my $seconds_since_last_report = $now - $d->{time_reported_gone};
                       #my $how_long_gone = $now - $d->{last_time_in}||$now;
                       #if (($seconds_since_last_report < $allowed_prf_seconds) || ($how_long_gone > $its_time_to_ignore))
                       #{

                            printf"hm:worker_bee: lost check recent enough\n" if DEBUG;
                            next; #  ignore for now, no need to bug them
                       #}
                    }
                    # else # Has not been reported yet yet
                    {
                    printf"hm:worker_bee: lost check updating time_reported_gone\n" if DEBUG;
                        my $status = $dt->do("UPDATE wireless_devices SET time_reported_gone = %s WHERE rowid = %s", $now, $d->{rowid});
                    }
                    printf "hm:worker_bee: lost check now we should email\n" if DEBUG;
                    my $time_string = localtime($d->{last_time_in});
                    my $loc =  tools::location_string($d->{loc}, $d->{addr_l});
                    my $subject = 'Lost connection to "'.$d->{desc}.'@'.$loc.'"';
                    my $msg = sprintf"%s @ %s has not reported in since: %s (%s)\n", $d->{desc}, $loc, $time_string, tools::how_long($now, $d->{last_time_in});
                    my $force = 1;
                    $EmailQueue->enqueue({cmd => 'to_primary', subject => $subject, msg => $msg, ah => $d->{addr_h},
                          al => $d->{addr_l}, event_time => $now||0});
                }
                elsif ($d->{time_reported_gone})
                {
                     printf"hmworker_bee: lost check it looks like it is back and we have reported it gone\n" if DEBUG;
                     my $status = $dt->do("UPDATE wireless_devices SET time_reported_gone = NULL WHERE rowid = %s", $d->{rowid});
                     my $loc =  tools::location_string($d->{loc}, $d->{addr_l});
                     my $msg = sprintf"%s @ %s is back\n", $d->{desc}, $loc;
                     my $force =1;
                     $EmailQueue->enqueue({cmd => 'to_primary', subject =>  $d->{desc}.'@'.$loc." now reconnected",
                          msg => $msg, ah => $d->{addr_h}, al => $d->{addr_l}, event_time => $now||0});
                     # evaluate::email_to_contacts($dt, $WorkerBeeQueue,  $XbeeSendQueue, $d->{desc}.'@'.$loc." now reconnected", $msg, $d->{addr_h}, $d->{addr_l}, undef, $force);
                }
                else
                {
                    printf"hm:worker_bee: lost check device is fine\n" if DEBUG;
                }
                #print "\n" if DEBUG;
            }
            undef @devices;
            # we are now checking for a proble where we are not getting back any acks for a device
            #my @devices =  $dt->tmpl_loop_query(<<EOF, (qw(rowid al ah loc desc)));
            #SELECT devices.rowid, devices.al, devices.ah, wireless_devices.physical_location, port_types.desc
            #FROM devices
            #JOIN wireless_devices ON wireless_devices.ah = devices.ah AND wireless_devices.al = devices.al
            #JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr AND port_types.port = devices.port
            #WHERE devices.try_count > 10
#EOF
            #foreach my $p (@devices)
            #{
                     #my $loc =  tools::location_string($d->{loc}, $d->{al});
                     #my $msg = sprintf"%s @ %s is back\n", $d->{desc}, $loc;
                     #my $force =1;
                     #evaluate::email_to_contacts($dt, $d->{desc}.'@'.$loc." now reconnected", $msg, $d->{ah}, $d->{al}, undef, $force);
            #}
        }
        else
        {
            printf("hm:worker_bee:waiting time left %s\n", $delay_time - $now) if DEBUG;
        }


    }
    printf("hm:worker_bee:exiting\n") if DEBUG;
}

sub check_timers
{
    my ($now, $dt, $XbeeSendQueue) = @_;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now);
    my $minutes_this_day = $min + ($hour * 60);
    my $time_start_of_day_seconds = $now - ($sec + (($min + ($hour * 60)) * 60));
    printf"hm:check_timers: now = %s, start of day = %s\n", scalar localtime($now), scalar  localtime($time_start_of_day_seconds) if DEBUG;
    my @timed_events = $dt->tmpl_loop_query(<<EOF, qw(ah al port toggle_port days hour minute duration logic));
    SELECT timed_events.ah, timed_events.al, timed_events.port, port_types.toggle_port, timed_events.days,
           timed_events.hour, timed_events.minute, timed_events.duration, port_types.logic
    FROM timed_events
    JOIN wireless_devices ON timed_events.ah = wireless_devices.ah
            AND timed_events.al = wireless_devices.al
    JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
            AND timed_events.port = port_types.port
EOF
    foreach my $t (@timed_events)
    {
        if ($t->{days} =~ /$wday/)  # this is a day we want
        {
            # print Dumper $t if DEBUG;
            my $time_when_should_start = (($t->{minute} + ($t->{hour} * 60)) * 60) + $time_start_of_day_seconds;
            my $time_when_to_stop = $time_when_should_start +  (($t->{duration}) * 60);
            printf"hm:check_timers: start_time = %s stop time = %s\n", scalar  localtime($time_when_should_start), scalar  localtime($time_when_to_stop) if DEBUG;
            if ($time_when_should_start < $now && $time_when_to_stop > $now)  # a valid time to do this
            {
                # when to turn off in TIME seconds now calculated
                printf"hm:check_timers:... turning ON --  for %s minutes\n", ($time_when_to_stop - $time_when_should_start) / 60 if DEBUG;
                $XbeeSendQueue->enqueue({request => 'DEVICE_ON', ah => $t->{ah}, al => $t->{al}, port => $t->{port}, toggle_port => $t->{toggle_port}, logic => $t->{logic}});
            }
        }
    }
}

sub update_reason_started
{
    my ($dt, $code, $descr) = @_;
    $dt->do("UPDATE reason_started SET next_code = %s, next_descr = %s", $code, $descr);
    db::backup($dt, cfg::SAVE_DATABASE_AS);
    return 0;
}

sub rotate_reason_started
{
    my ($dt) = @_;
    my ($status, $cnt) = $dt->get_rec("select count(*) from reason_started");
    if ($status == 0 || $cnt != 1)
    {
        $dt->do("DELETE FROM reason_started");
        $dt->do("INSERT INTO reason_started (code) VALUES (0)");
    }
    $dt->do("UPDATE reason_started SET code = next_code, descr = next_descr");
    return 0;
}


sub upload_database
{
    my ($dt) = @_;
    my constant $ftp_site = 'web1335.ixwebhosting.com';

    # gzip last backup
    my $pan_id = tools::get_config($dt)->{pan_id};
    my $local_path = "/dev/shm/${pan_id}.db.gz";
    my $remote_path = "/databases/${pan_id}.db.gz";
    my constant $ftp_user     = 'alerta';
    my constant $ftp_password = 'R1kjed';
    system ("gzip -c cfg::SAVE_DATABASE_AS > $local_path");
    my $ftps = Net::FTPSSL->new($ftp_site,
                              Port => 21,
                              Encryption => 'E',
                              xDebug => 1);
    if (!$ftps)
    {
       printf("hm:upload_database:could not open the ftp connection = $ftp_site\n") if DEBUG;
    }
    else
    {
      printf("hm:upload_database:ftp open worked\n") if DEBUG;
      if (!$ftps->login($ftp_user, $ftp_password))
      {
          printf("hm:upload_database:Could not login [%s]", $ftps->last_message()) if DEBUG;
      }
      else
      {
         printf("hm:upload_database:ftp login ok\n") if DEBUG;

         if (!$ftps->binary())
         {
             printf("hm:upload_database:Could not set binary [%s]", $ftps->last_message) if DEBUG;
         }

         printf("hm:upload_database:Now sending %s to %s", $local_path, $remote_path) if DEBUG;
         eval {local $SIG{__DIE__}; $ftps->put($local_path, $remote_path);};
         if ($@)
         {
             printf("hm:upload_database:die cause a fail in ftp send [%s]", $@) if DEBUG;
         }
         elsif (!$ftps)
         {
             printf("hm:upload_database:Problem sending remote file: %s [%s]", $local_path, $ftps->last_message) if DEBUG;
         }
         else
         {
            printf("hm:upload_database:database uploaded OK\n") if DEBUG;
         }
      }
      $ftps->quit();
   }
}

sub download_database
{
    my ($dt) = @_;

    # note all the tracing will be lost if this works

    my constant $ftp_site = 'web1335.ixwebhosting.com';

    # gzip last backup
    my $pan_id = tools::get_config($dt)->{pan_id};
    my $local_path = "/dev/shm/${pan_id}.db.gz";
    my $remote_path = "/databases/${pan_id}.db.gz";
    my constant $ftp_user     = 'alerta';
    my constant $ftp_password = 'R1kjed';

    my $ftps = Net::FTPSSL->new($ftp_site,
                              Port => 21,
                              Encryption => 'E',
                              xDebug => 1);
    if (!$ftps)
    {
       printf("hm:download_database:could not open the ftp connection = $ftp_site\n") if DEBUG;
    }
    else
    {
      printf("hm:download_database:ftp open worked\n") if DEBUG;
      if (!$ftps->login($ftp_user, $ftp_password))
      {
          printf("hm:download_database:Could not login [%s]", $ftps->last_message()) if DEBUG;
      }
      else
      {
         printf("hm:download_database:ftp login ok\n") if DEBUG;

         if (!$ftps->binary())
         {
             printf("hm:download_database:Could not set binary [%s]", $ftps->last_message) if DEBUG;
         }
         printf("hm:download_database:Now getting %s to %s", $remote_path, $local_path) if DEBUG;
         eval {local $SIG{__DIE__}; $ftps->get($remote_path, $local_path);};
         if ($@)
         {
             printf("hm:download_database:die cause a fail in ftp get [%s]", $@) if DEBUG;
         }
         elsif (!$ftps)
         {
             printf("hm:download_database:Problem getting remote file: %s [%s]", $local_path, $ftps->last_message) if DEBUG;
         }
         else
         {

            system ("gunzip -c $local_path > cfg::SAVE_DATABASE_AS");
            my $saved_dt = db::open(cfg::SAVE_DATABASE_AS);
            $saved_dt->do("UPDATE reason_started SET next_code = %s, next_descr = %s", 8,"Phone home DB download");
         }
      }
   }
   $ftps->quit();
}

sub get_first_status_time
{
    # this calculation is to set the status time to 2AM
    my $restart_hour = 12;


    my $time = time;
    ##### return $time + 240; ####   testing
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($time);
    my $restart_time;
    if ($hour == $restart_hour)  # it is 2AM
    {
        $restart_time = $time + (60 * 60 * 24);  # next restart is 24 hours from now;
    }
    elsif ($hour < $restart_hour) # 0 or 1AM
    {
        $restart_time = $time + (60 * 60 * ($restart_hour - $hour));
    }
    else  # 3AM or later
    {
        $restart_time = $time + (60 * 60 * (24 + $restart_hour - $hour));
    }
    printf("hm:get_first_status_time: status email at %s\n", scalar localtime($restart_time));# if DEBUG;
    return $restart_time;
}

sub initialize
{ # this is the startup stuff
    my ($WorkerBeeQueue) = @_;

    favicon::drop('/var/www/alertaway');
    http_processor::drop_index_html('/var/www/alertaway');
    ##my ($log, $pass, $uid, $gid) = getpwnam('www-data');

    system ('rm -r /var/www/alertaway/dvr /var/www/alertaway/admin');
    symlink '/alertaway/dvr.pl', '/var/www/alertaway/dvr';
    symlink '/alertaway/admin.pl', '/var/www/alertaway/admin';
    symlink '/alertaway/extern.pl', '/var/www/html/extern';

    mkdir "/dev/shm/snapshots";
    chmod 0777, "/dev/shm/snapshots ";
    system ('rm -r /var/www/alertaway/snapshots /var/www/html/snapshots /var/www/html/extern');
    symlink '/dev/shm/snapshots', '/var/www/alertaway/snapshots';
    symlink '/dev/shm/public_snapshots', '/var/www/html/snapshots';
    symlink '/alertaway/extern.pl', '/var/www/html/extern';
    #system ('chown -R www-data:www-data /var/www/');

    mkdir "public_snapshots";
    chmod 0777, "public_snapshots";
    my $dt = db::open(cfg::DBNAME);
    chmod 0777, "admin.pl";
    chmod 0777, "extern.pl";
    chmod 0777, "dvr.pl";
    ip_tools::save_port($dt);
    open my $ver, "</alertaway/version.txt";
    my $version_number_raw = <$ver>;
    close $ver;
    my ($version_number,  $upgrade_problem,  $problem_server_version_number) = split /\s/, $version_number_raw;
    my $starting_config = tools::get_config($dt);
    my  $cip = ip_tools::get_ip_addr($starting_config, $WorkerBeeQueue);
    my $cnt=0;
    motion_manager::rebuildImageTable();
    while (1) ## loop until we get the time from home
    {
      print "hm:initialize: phone home\n" if DEBUG;
      my ($status, $parms) = tools::phone_home($dt, $starting_config, $cip, $system_type, $WorkerBeeQueue);
      if ($status)
      {
          printf("hm:initialize: time returned from phone_home = %s\n", $parms->{time}) if DEBUG;
          time_keeper::set_time($dt, $parms->{time});
          last;
      }
      if ($cnt++ > 2)
      {
          $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Problem contacting AlertAway.com for correct date/time"});
          print "hm:initialize: Problem contacting AlertAway.com for time\n" if DEBUG;
          ## now we have a bad starting time so we should fix it and all the times that have been recorded,
          ## the times will be thrown off and this is a problem
          # we will use a offset time to correct this,
          last;
      }
    }

    my $now = time;
    #printf"hm:initialize:----- updating process starttime %s\n", $now if DEBUG;
    $dt->do("update config set version_number = %s, upgrade_problem = %s, problem_server_version_number = %s, process_start_time = %s, time_offset = 0",
           $version_number,  $upgrade_problem,  $problem_server_version_number, $now);

    my $ip_set_status = 0;
    my $ip_status = ip_tools::set_ip($dt); # 0 = primary worked, 1 = backup worked, 2 = both failed
    if ($ip_status == 0)
    {
        printf("hm:initialize: primary IP set worked\n") if DEBUG;
        $WorkerBeeQueue->enqueue({request => "LOG", fmt => "initialize::primary IP set worked"});
    }
    else ## Had IP problems, so log messages and set value to re-try later
    {
        $ip_set_status = 1;
        printf("hm:initialize: primary IP set had problems, status = %s\n", $ip_set_status);# if DEBUG;
        if ($ip_status ==  2)
        {
            $WorkerBeeQueue->enqueue({request => "LOG", fmt => "initialize::primary and secondary failed so default to DHCP"});
        }
        elsif ($ip_status ==  1)
        {
            $WorkerBeeQueue->enqueue({request => "LOG", fmt => "initialize::primary IP set failed, fell back to last working IP set"});
        }
    }
    #printf"hm:initialize:++++++ updating process starttime, again  %s\n", $now if DEBUG;
    $dt->do("update config set version_number = %s, upgrade_problem = %s, problem_server_version_number = %s, process_start_time = %s, ip_set_status = %s",
           $version_number,  $upgrade_problem,  $problem_server_version_number, $now, $ip_set_status);



    my $timezone = $starting_config->{timezone};
    if ($timezone && $timezone gt "")
    {
        $ENV{TZ}=$timezone;
        POSIX::tzset;
        printf("hm:initialize: setting time zone = %s\n", $timezone) if DEBUG;
    }
    else
    {
        printf("hm:initialize: no timezone set\n") if DEBUG;
    }

    my $date_string = localtime($now);
    printf("hm:initialize: DATE:  %s\n", $date_string) if DEBUG;
    $dt->do("INSERT or REPLACE INTO processes (name, pid) VALUES (%s,%s)", 'main', $$);
    rotate_reason_started($dt);
    tools::fix_last_time_in($dt, $now);
    $dt->do("UPDATE wireless_devices SET db_level = NULL, my_network_address = NULL, parent_network_address = NULL");
    #my $rid = $dt->last_insert_rowid();
    #printf STDERR "last_insert_rowid [%s]\n",$rid;
    return ($starting_config, $dt);
}
