package xbee_reader;
use QueueManager;
use API ':xbee_flags';
use Data::Dumper;

use filterPrint;
my $fp = filterPrint->new();
#use constant DBG => 1;
use constant NUMBER_OF_TIMEOUTS_TO_FORCE_REBOOT => 45; # 20 second timeout gives 3 timeouts per minute * 15 minutes = 45 timeouts
sub xbee_reader  ## runs as a seperate process
{
    my ($trace_in, $api_in) = @_;
    my $api = $api_in;
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $PacketQueue = QueueManager::PacketQueue();
    my $XbeeSendQueue = QueueManager::XbeeSendQueue();
    my $timeout_count = 0;

    my $received_AT_COMMAND_RESPONSE_yet = 0;
    while ( 1 )
    {
        my ($timeout, $packet) = $api->read_packet();
        if ($timeout)    # timeout every 20 seconds by default
        {
            # DBG&&$fp->prt("hm:xbee_reader:null returned from xbee read:  status = $packet\n") if DEBUG;
            if ($timeout_count > NUMBER_OF_TIMEOUTS_TO_FORCE_REBOOT)
            {               
				xbee_not_responding_reboot($WorkerBeeQueue); # will not return
			}
			$timeout_count++;					
        }
        else
        {
            DBG&&$fp->prt("xbee_reader: enqueue packet\n");
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
    my ($trace_in, $api) = @_;
    my $PacketQueue = QueueManager::PacketQueue({reader => 1});
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $ProcessMsgQueue = QueueManager::ProcessMsgQueue();
    my $EvaluateQueue = QueueManager::EvaluateQueue();
    $|=1;
    #$fp = filterPrint->new();
    my $msg_in_cnt = 0;
    my $max_queue  = 0;
    my $timeout_count = 0;
    #my $reboot_xbee_count = 0;
    my $received_AT_COMMAND_RESPONSE_yet = 0;
    my $last_wakeup = 0;
    while ( 1 )
    {
        #my $rxin = $api->rx();
        #my ($error, $packet) = $api->read_packet();

        my $packet = $PacketQueue->dequeue();
        #$fp->filter();
        if (ref $packet eq 'HASH' && $packet->{request} && $packet->{request} eq "TRACE_HASH")
        {
            #$tracer->init($packet->{trace_als});
            #%trace_hash = tools::hash_trace($packet->{trace_als}, XBD_DEBUG);
            #prt("xbee_dispatch: trace_hash %s\n", tools::hexDumper('', \%trace_hash));
            next;
        }
        my ($error, $rxin);
        #prt "xbee_dispatch parsing package %s\n", Dumper \$packet if $trace;
        if ($packet)
        {
             #DBG&&$fp->prt("xbee_dispatch: packet  %s\n", unpack ("H*",$packet));
            ($error, $rxin) = $api->parse_packet($packet);
            if ($error)
            {
                DBG&&$fp->prt(":PARSE PACKET ERROR %s\n", $error);
                next;
            }
        }
        else
        {
           DBG&&$fp->prt(" error no packet? %s\n");
           next;
        }
        #$fp->filter($rxin->{al});
        DBG&&$fp->prt("api type[%X] sh[%X] sl[%X]\n", $rxin->{api_type}, $rxin->{sh}||"0", $rxin->{sl}||"0");
        DBG&&$fp->prt("%s", tools::hexDumper('', $rxin));
        #DBG&&$fp->trace_if('fe17c7b9' eq $rx->{al});

        if ($rxin->{api_type} == 0x90 || ($rxin->{api_type} == 0x91 && $rxin->{cluster_id} == 0x11)) # data packet
        {
             $rxin->{cmd} = "MSG";
             DBG&&$fp->prt(" Got a data packet api_type = %0x sl = %0x\n", $rxin->{api_type}, $rxin->{sl});
             next;
        }
        my $string_type =  XBEE_API_TYPE_TO_STRING->{$rxin->{api_type}};
        #prt "hm:xbee_dispatch:API type = %0x %s\n", $rxin->{api_type}, $string_type if DEBUG;
        if ($received_AT_COMMAND_RESPONSE_yet == 0 && $rxin->{api_type} == 0x88) # AT_COMMAND_RESPONSE
        {
             ## on occasion the sender gets out of sync and commands are not processed
             ## this is fixed by doing a reboot
             ## the worker bee process is waiting for this process to tell it things are fine
             ## if it does not get a message indicating that we got a reply it will reboot shortly
             $received_AT_COMMAND_RESPONSE_yet = 1;
             DBG&&$fp->prt("GOOD_XBEE_COMM sent\n");
             $WorkerBeeQueue->enqueue({request => 'GOOD_XBEE_COMM'});
        }
        elsif ($rxin->{api_type} == 0x8a)
        {
             DBG&&$fp->prt(" Modem Status: %s\n", Dumper $rxin);
        }
        elsif ($rxin->{api_type} == 0x97) #ack
        {
             DBG&&$fp->prt(" 0x97 ack:\n");
             #$EvaluateQueue->enqueue();
        }
        elsif ($rxin->{api_type} == 0x91)
        {
             DBG&&$fp->prt(" ZDO [0x91] %x:%x cluster_id = 0x%0x data %s\n", $rxin->{sh}, $rxin->{sl}, $rxin->{cluster_id},unpack("H*", $rxin->{data}));
        }
        if ($rxin->{sh})
        {
            DBG&&$fp->prt(" %s: %0x:%0x\n", $string_type, $rxin->{sh},$rxin->{sl});
        }
        elsif ($rxin->{remote_sh})
        {
            DBG&&$fp->prt(" %s: %0x:%0x\n", $string_type, $rxin->{remote_sh},$rxin->{remote_sl});
        }
        else
        {
            DBG&&$fp->prt(" %s\n", $string_type);
        }

        if ($rxin->{status})
        {
            DBG&&$fp->prt(" ... status = %s\n", $rxin->{status});
        }
        my $now = time;
        $rxin->{timestamp} = $now;
        $fp->prt("ProcessMsgQueue->enqueue");
        $ProcessMsgQueue->enqueue($rxin);
        undef $rxin;
        #if ($now - $last_wakeup > 2)
        #{
            #$DelayQueue->enqueue({queue => 'WakeUp'});
            #$last_wakeup = $now;
        #}
        $msg_in_cnt++;
        #$reboot_xbee_count=0;
        $timeout_count=0;
    }
    DBG&&$fp->prt(" exiting\n");
}

sub xbee_not_responding_reboot
{
   my ($WorkerBeeQueue) = @_;

   $WorkerBeeQueue->enqueue({request => 'REASON_STARTED', code => 1, descr => "reboot, xbee timeout"});
   DBG&&$fp->prt("xbee_dispatch:reboot_this_xbee: shuting down for reboot\n");
   shutDown();
}

1;
