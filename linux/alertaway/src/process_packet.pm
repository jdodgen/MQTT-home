package process_packet;

use API ':xbee_flags';
use Carp;
#use valve;
use Data::Dumper;
use strict;
use cfg;

use constant TEN_MINUTES => 600;
use constant HOURS12 => 43200;
use constant HOURS24 => 86400;

use tools qw (:debug);

my $WorkerBeeQueue;
my $ProcessMsgQueue;
my $XbeeSendQueue;
my $EmailQueue;
my $Watchdog;
my $EvaluateQueue;
my $dt;
my %dupe_check;
my $zha;

use filterPrint;
my $fp = filterPrint->new();
use constant DBG => 1;

sub task
{
    my ($trace_in, $api) = @_;

    # use Devel::Cycle;
    $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    $ProcessMsgQueue = QueueManager::ProcessMsgQueue({reader => 1});
    $XbeeSendQueue = QueueManager::XbeeSendQueue();
    $EmailQueue = QueueManager::EmailQueue();
    $Watchdog = QueueManager::Watchdog();
    $EvaluateQueue = QueueManager::EvaluateQueue();
    $dt = db::open(cfg::DBNAME);
#     my %part_types = $dt->query_row_per_hash("SELECT part_nbr, part_type FROM device_types");

    $zha = ZigbeeHomeAutomation->new({dt => $dt, api => $api});
    my %db_level_in;
    my %parent_addr_in;
    my $count = 0;
    my $rx;
    my $toggle = 0;
    my $first_0x13 = 0;
    while (1)
    {
        $rx = $ProcessMsgQueue->dequeue;
        #$fp->filter($rx->{al}, $rx->{sl});

        my $need_to_evaluate = 0;
        #DBG&&$fp->prt("%s", Dumper $rx);
        # $trace = tools::is_trace(\%trace_hash,  );
        #if ($rx->{api_type} && $rx->{api_type} > 0)
        #{
            #DBG&&$fp->prt( "process_packet:task: cluster %-4x API %-2x:%-30s %8x:%x\tdata[%s]\n", $rx->{cluster_id}||0, $rx->{api_type}||0, XBEE_API_TYPE_TO_STRING->{$rx->{api_type}||0}, $rx->{sh}||$rx->{remote_sh}||0, $rx->{sl}||$rx->{remote_sl}||0, substr(unpack("H*", $rx->{data}||''),0,30) );
        #}
        #if ($rx->{cluster_id} && $rx->{cluster_id} == 6)  # testing HA lightbulb
        #{
            ##DBG&&$fp->prt( "process_packet:task: cluster id 6 Dumper %s\n", Dumper $rx);
            ##$rx->{ni} = 'HA';
            ##$rx->{remote_sh} = $rx->{sh};
            ##$rx->{remote_sl} = $rx->{sl};
        #}
        $fp->prt("dequeued\n%s", tools::hexDumper('', $rx));
        #DBG&&$fp->prt("dequeued: sl[%s] al[%s] hex ni[%s]\n%s", tools::location_string($rx->{sl}||0), tools::location_string($rx->{al}||0), unpack("H*", $rx->{ni}), tools::hexDumper("read",$rx));
        #DBG&&$fp->trace_if('fe17c7b9' eq $rx->{al});
        if ($rx->{reset})
        {
            DBG&&$fp->prt("decabels and parent hash reset\n");
            %db_level_in=();
            %parent_addr_in=();
            #$XbeeSendQueue->enqueue({request => 'SEND_NODE_DISCOVERY'});
            next;
        }
        if ($rx->{request} && $rx->{request} eq "TRACE_HASH")
        {

            #%trace_hash = tools::hash_trace($rx->{trace_als}, DEBUG);
            DBG&&$fp->prt("process_packet: trace_hash %s\n", Dumper \$rx->{trace_als});
            next;
        }
        #if ($rx->{evaluate})
        #{
             #$Watchdog->enqueue({queue => 'PUSH_TOGGLE'});
             #print "process_packet:task: evaluate msg causing all_ports to be done\n" if DEBUG;
             #evaluate::evaluate($dt, $XbeeSendQueue, $EmailQueue);
             #next;
        #}


        #DBG&&$fp->prt( "dequeue [%s:%0#x] %s status=%s\n",
               #XBEE_API_TYPE_TO_STRING->{$rx->{api_type}}, $rx->{api_type}, tools::location_string($rx->{sl}||0), $rx->{status}||'N/A');

        #next;
        my $hash_key = $rx->{sh}.':'.$rx->{sl} if ($rx->{sh});
        if ($rx->{api_type} == 0x91)
        {
            if ($rx->{cluster_id} == 0x8032)
            {
                route_collection::save($dt, $rx, $XbeeSendQueue);
            }
            elsif ($rx->{cluster_id} == 0x0006)  # ON OFF cluster should be home automation zigbee, not xbee
            {
                #DBG&&$fp->prt("cluster_id 0x0006: \n%s\n", tools::hexDumper("", $rx));
                record_last_time_in(
                  $dt, $XbeeSendQueue,  $WorkerBeeQueue,
                  $rx->{sh},
                  $rx->{sl},
                  $rx->{na},
                  $rx->{timestamp},'ZHA');
                #if ($rx->{profile_id} == 0x104 && ($rx->{header}{cmd_id} == 0x0a || $rx->{header}{cmd_id} == 0x01)) # on off status
                if ($rx->{is_broadcast}) # use these to force a resample
                {
                    my @ha_ports = $dt->tmpl_loop_query(<<EOF,(qw(port logic na endpoint profile_id)));
                    SELECT port_types.port, port_types.logic, wireless_devices.na, wireless_devices.endpoint, wireless_devices.profile_id
                    FROM wireless_devices
                    JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
                    WHERE wireless_devices.ah = $rx->{sh} AND wireless_devices.al = $rx->{sl}
EOF
                    foreach my $p (@ha_ports)
                    {
                        $XbeeSendQueue->enqueue({request => 'FORCE_SAMPLE', ah => $rx->{sh}, al => $rx->{sl}, na => $p->{na},
                            port => $p->{port}, endpoint => $p->{endpoint}, profile_id => $p->{profile_id}});
                    }
                }
                elsif ($rx->{header}{cmd_id} == 0x0a || $rx->{header}{cmd_id} == 0x01)# on off status reply
                {
                    my ($current) = unpack('C',substr($rx->{payload}, -1,1));
                    # $need_to_evaluate +=
                    check_and_log($dt, $WorkerBeeQueue, $EmailQueue, $rx->{sh}, $rx->{sl}, $rx->{timestamp}, 'HA6', $current);
                    DBG&&$fp->prt("HA6 need_to_evaluate[%s]\n", $need_to_evaluate);
                    #$dt->do("UPDATE devices SET raw_value = %s, validated = %s, last_report_time = %s WHERE ah = %s AND al = %s AND port = %s",
                            #$current, 'ACK', $rx->{timestamp}, $rx->{sh}, $rx->{sl}, '6');
                    DBG&&$fp->prt("cluster 6 profile %0x reports  light is %s %s\n",  $rx->{profile_id}, $current, $current?'ON':'OFF');
                }
            }
            elsif ($rx->{cluster_id} == 0x92) # I/0 Data
            {
                $need_to_evaluate += evaluate_xbee_lines($rx);
            }
            elsif ($rx->{cluster_id} == 0x95) # Node Discovery Response
            {
                if ($rx->{device_type} && $rx->{device_type} == 0)
                {
                    $WorkerBeeQueue->enqueue({request => 'LOG', fmt => '0x95 reply from Coordinator', parms => [1]});
                }
                record_last_time_in(
                  $dt, $XbeeSendQueue,  $WorkerBeeQueue,
                  $rx->{remote_sh},
                  $rx->{remote_sl},
                  $rx->{remote_na},
                  $rx->{timestamp}, $rx->{ni}
                  );
                  DBG&&$fp->prt("NI 0x95 [%0x %0x]  NI [%s] parent 16 bit address [%s]\n",
                    $rx->{remote_sh}, $rx->{remote_sl},$rx->{ni}, $rx->{parent_address});
            }
            elsif ($rx->{cluster_id} == 0x13) # initialize cluster request from ZHA/Zll device
            {
                #DBG&&$fp->prt("cluster 0x13\n%s\n", tools::hexDumper("", $rx));
                my ($status, $part_nbr) = $dt->get_rec('SELECT part_nbr FROM wireless_devices WHERE wireless_devices.ah = %s AND wireless_devices.al = %s',
                     $rx->{sh}, $rx->{sl});

                #record_last_time_in(
                    #$dt,  $XbeeSendQueue,  $WorkerBeeQueue,
                    #$rx->{sh},
                    #$rx->{sl},
                    #$rx->{na},
                    #$rx->{timestamp},'ZHA');
                if (!$status) # this is a new HA part, no ports recorded
                {
                    $XbeeSendQueue->enqueue({request => 'HA_ENDPOINTS', ah => $rx->{sh}, al => $rx->{sl}, na => $rx->{na}});
                }

                #$XbeeSendQueue->enqueue({request => 'TOGGLEONOFF', ah => $rx->{sh}, al => $rx->{sl}, na => $rx->{na}});   ## testing

                #$XbeeSendQueue->enqueue({request => 'MATCH_DESCRIPTOR_RESPONCE', ah => $rx->{sh}, al => $rx->{sl}, na => $rx->{na}});

            }
            elsif ($rx->{cluster_id} == 0x8005) # initialize cluster request from HA_ENDPOINTS device
            {
                # for testing
                #DBG&&$fp->prt("0x8005 response \n%s\n", tools::hexDumper("", $rx));
                record_last_time_in(
                    $dt,  $XbeeSendQueue,  $WorkerBeeQueue,
                    $rx->{sh},
                    $rx->{sl},
                    $rx->{na},
                    $rx->{timestamp},'HA_ENDPOINTS');
                #$XbeeSendQueue->enqueue({request => 'TOGGLEONOFF', ah => $rx->{sh}, al => $rx->{sl}, na => $rx->{na}});
                foreach my $end_point (@{$rx->{active_endpoint}{list}})
                {
                  $XbeeSendQueue->enqueue({request => 'HA_SIMPLE_DESC', ah => $rx->{sh}, al => $rx->{sl}, na => $rx->{na}, endpoint => $end_point});
                }
            }
            elsif ($rx->{cluster_id} == 0x8004) # initialize cluster request from HA_SIMPLE_DESC device
            {
                # for testing
                #DBG&&$fp->prt("0x8004 responce\n%s\n", tools::hexDumper("", $rx));
                $zha->set_unit_type($rx);
                $XbeeSendQueue->enqueue({request => 'MATCH_DESCRIPTOR_RESPONCE', ah => $rx->{sh}, al => $rx->{sl}, na => $rx->{na}, profile_id => $rx->{profile_id}});
            }
            elsif ($rx->{cluster_id} == 0x8000) # Seems some ZLL devices send this out, might as well use it to report life
            {
                #DBG&&$fp->prt("cluster=0x8000 \n%s\n", tools::hexDumper("", $rx));
                record_last_time_in(
                    $dt,  $XbeeSendQueue,  $WorkerBeeQueue,
                    $rx->{sh},
                    $rx->{sl},
                    $rx->{na},
                    $rx->{timestamp},'ZHA');
            }
            else
            {
                DBG&&$fp->prt("Unknown 91 cluster [%-4X] API %-2x:%-30s %8x:%x\tdata[%s]\n",
                $rx->{cluster_id}||0, $rx->{api_type}||0, XBEE_API_TYPE_TO_STRING->{$rx->{api_type}||0}, $rx->{sh}||$rx->{remote_sh}||0, $rx->{sl}||$rx->{remote_sl}||0,
                substr(unpack("H*", $rx->{data}||''),0,30));
            }
        }
        elsif ( $rx->{api_type} == 0x92) # IO Data Sample Rx Indicator
        {
            $need_to_evaluate += evaluate_xbee_lines($rx);
        }
        elsif ($rx->{api_type} == 0x97 && $rx->{command} eq 'IS' && $rx->{status} == 0) # data sample rx indicator 97 = Remote AT Command Response
        {
            $need_to_evaluate += evaluate_xbee_lines($rx);
        }
        elsif ( $rx->{api_type} == 0x95) # NODE_IDENTIFICATION_INDICATOR
        {
            if (!$rx->{ni} || $rx->{ni} =~ /^\s*$/)
            {
                no_ni_problem($rx->{api_type}, $rx->{remote_sh},$rx->{remote_sl},$WorkerBeeQueue);
            }
            else
            {
                record_last_time_in(
                    $dt, $XbeeSendQueue,  $WorkerBeeQueue,
                    $rx->{remote_sh},
                    $rx->{remote_sl},
                    $rx->{remote_na},
                    $rx->{timestamp}, $rx->{ni}
                );
            }
            # print ($rx) if DEBUG;
        }

        elsif ( $rx->{api_type} == 0x88 && $rx->{data_as_int}) # AT_COMMAND_RESPONSE (local)
        {
            DBG&&$fp->prt("AT_COMMAND_RESPONSE 0x88 command=%s status=%d frame_id=%d data=[0x%0x]\n",
                   $rx->{command}, $rx->{status}, $rx->{frame_id}, $rx->{data_as_int});
            if ($rx->{command} eq "ND" && $rx->{is_ok}) # for now ignore the errors
            {
                # $rx->{api_data} = "removed";
                DBG&&$fp->prt("88-ND command %s",tools::hexDumper("", $rx));
                if (!$rx->{ni} || $rx->{ni} =~ /^\s*$/)
                {
                    no_ni_problem($rx->{api_type}, $rx->{sh},$rx->{sl}, $WorkerBeeQueue);
                }
                else
                {
                   record_last_time_in(
                    $dt,  $XbeeSendQueue,  $WorkerBeeQueue,
                    $rx->{sh},
                    $rx->{sl},
                    $rx->{na},
                    $rx->{timestamp}, $rx->{ni}
                    );
                }
                if ($rx->{my} && $rx->{my} != 0xfffe)
                {
                    $parent_addr_in{$hash_key} = $rx->{timestamp}+HOURS24; # tomorrow
                    #record_network_address($XbeeSendQueue, $dt,  $rx->{sh}, $rx->{sl}, $rx->{my}, $rx->{parent_network_address});
                    DBG&&$fp->prt("ND  reply 0x88[%0x %0x] NI [%s]\n",
                      $rx->{sh}, $rx->{sl}, $rx->{ni} || "NO NODE ID?");

                    #print tools::hexDumper("", $rx) if DEBUG;
                }
            }
            elsif  ($rx->{command} eq "ID" )
            {
               my $pan_id =  $rx->{data_as_int};
               DBG&&$fp->prt("PAN ID reply -- 0x%0X %d\n",  $pan_id||0, $pan_id||0);
               $dt->do("update config set pan_id = %s", $pan_id);
               # evaluate::email_to_contacts($dt, "AlertAway started", "The AlertAway Software has started, this is not a problem\nit could have been an automatic upgrade or just the home server being powered up\nIf you are getting lots of these messages please contact Rik at AlertAway for support", 0, 0, 0);
            }
            elsif  ($rx->{command} eq "OP" )
            {
               my $pan_id =  $rx->{data_as_int};
               #DBG&&$fp->prt("process_packet:task:pan_id_64 reply -- 0x%0X %d\n",  $pan_id||0, $pan_id||0); # if DEBUG;
               $dt->do("update config set pan_id_64 = %s", $pan_id);
             }
            elsif  ($rx->{command} eq "OI" )
            {
               my $pan_id =  $rx->{data_as_int};
               #DBG&&$fp->prt("process_packet:task:pan_id_16 reply -- 0x%0X %d\n",  $pan_id||0, $pan_id||0); # if DEBUG;
               $dt->do("update config set pan_id_16 = %s", $pan_id);
             }
            elsif  ($rx->{command} eq "CH" )
            {
               my $op_ch =  $rx->{data_as_int};
               #DBG&&$fp->prt("process_packet:task:operating_channel reply -- 0x%0X %d\n",  $op_ch||0, $op_ch||0); # if DEBUG;
               $dt->do("update config set operating_channel = %s", $op_ch);
             }
            elsif  ($rx->{command} eq "ZS" )
            {
               my $stack_prof =  $rx->{data_as_int};
               #DBG&&$fp->prt("process_packet:task:stack_profile reply -- 0x%0X %d\n",  $stack_prof||0, $stack_prof||0); # if DEBUG;
               $dt->do("update config set stack_profile = %s", $stack_prof);
            }
            elsif  ($rx->{command} eq "SL" )
            {
               $dt->do("update config set sl = %s", $rx->{data_as_int});
            }
            elsif ($rx->{command} eq 'HV' )
            {
                # noop   just sent to see if xbee alive
            }
            #elsif  ($rx->{command} eq "MY" )
            #{
               #DBG&&$fp->prt("process_packet:task: NETWORK ADDRESS reply -- 0x%0X\n",  $rx->{data_as_int}) if DEBUG;
               #$dt->do("UPDATE config SET network_address = %s", $rx->{data_as_int});
            #}
            #elsif  ($rx->{command} eq "SH" )
            {
               $dt->do("UPDATE config SET sh = %s", $rx->{data_as_int});
            }
        }
        #elsif ( $rx->{api_type} == 0x88 && $rx->{command} eq "ND") # this 0x88 might be a ZHA
        #{
            #$XbeeSendQueue->enqueue({request => 'HA_ENDPOINTS', ah => $rx->{sh}, al => $rx->{sl}, na => $rx->{na}});
        #}
        elsif ( $rx->{api_type} == 0x97)  ## REMOTE_AT_COMMAND_RESPONSE
        {
            DBG&&$fp->prt("REMOTE_AT_COMMAND_RESPONSE 0x97[%0x %0x] command=%s status=%d frame_id=%d\n",
                   $rx->{sh}, $rx->{sl}, $rx->{command}, $rx->{status}, $rx->{frame_id});
            # 0 = OK
            # 1 = ERROR
            # 2 = Invalid Command
            # 3 = Invalid Parameter
            # 4 = Remote Command Transmission Failed
            if ($rx->{is_ok}) # 1 is a good remote response 4 means bad one, like could not contact.
            {
                # check to see if a ack is back from a alarm off (see xmit package where it is set)
                if ($rx->{command} =~  /^(A|D)\d+$/)  # digital or analog ports, Ignore the other requests
                {
                    #my ($status,  $requested_state) = $dt->get_rec("SELECT raw_value  FROM devices WHERE ah = %s AND al = %s AND port = %s AND frame_id = %s",
                                   #$rx->{sh}, $rx->{sl}, $rx->{command}, $rx->{frame_id});
                    #if ($status == 1)
                    #{
                         # Note: only do this if the ack is the same
                    #}
                    #else
                    #{
                        #DBG&&$fp->prt("process_packet:task: ACK (good) back not matching record [%x:%x]%s fid %s\n", $rx->{sh}, $rx->{sl}, $rx->{command}, $rx->{frame_id}) if DEBUG;
                    #}
                    update_ack_packet($dt, $rx->{frame_id}, $rx->{status});
                }
                if ($rx->{command} eq 'WH' )
                {
                   DBG&&$fp->prt("WH cnd " . tools::hexDumper("", $rx));
                }
                elsif ($rx->{command} eq 'VR' )
                {
                    $dt->do("UPDATE wireless_devices SET firmware_version = %s WHERE al = %s AND ah = %s", $rx->{data_as_int}, $rx->{sl}, $rx->{sh});
                }
                elsif ($rx->{command} eq 'OP' ) # operating 64 bit pan id
                {
                     # set corrdinator  ID
                }
                elsif ($rx->{command} eq 'OI' ) # operating 16 bit pan id
                {
                     # set corrdinator  II
                }
                elsif ($rx->{command} eq 'CH' ) # operating 16 bit pan id
                {
                     # set corrdinator  SC  set scan channel bit mask
                }
                elsif ($rx->{command} eq 'ZS') # operating 16 bit pan id
                {
                     # set corrdinator  ZS
                }
                #elsif  ($rx->{command} eq "MP" )
                #{
                    #$parent_addr_in{$hash_key} = $rx->{timestamp}+HOURS24; # tomorrow
                    ##record_network_address($XbeeSendQueue, $dt,  $rx->{sh}, $rx->{sl}, $rx->{na}, $rx->{data_as_int});
                #}
                elsif  ($rx->{command} eq "NI" )
                {
                     DBG&&$fp->prt("NI came back %x:%x -- %s\n", $rx->{sh}, $rx->{sl}, $rx->{data});
                     record_last_time_in($dt, $XbeeSendQueue,  $WorkerBeeQueue,
                        $rx->{sh}, $rx->{sl}, $rx->{na},
                        $rx->{timestamp}, $rx->{data});  #data contains $part_nbr
                }
                elsif ($rx->{command} eq "DB" )   ## signal strength of remote device
                {
                     #print "process_packet:task:sig strenght\n" if DEBUG;
                     #print tools::hexDumper("", $rx) if DEBUG;
                     $db_level_in{$hash_key} = $rx->{timestamp}+86400; # tomorrow
                     record_signal_strength(
                        $dt,
                        $rx->{sh}, $rx->{sl},
                        $rx->{data_as_int}) if ($rx->{is_ok});
                }
            }
            elsif ($rx->{status} == 4)   # 4 means bad one, like could not contact.
            {
                DBG&&$fp->prt("0x97 status of  4  Remote Command Transmission Failed [%x:%x]%s fid %s\n",
                   $rx->{sh}, $rx->{sl}, $rx->{command}, $rx->{frame_id});
                if ($rx->{command} =~  /^(A|D)\d+$/)  # digital or analog ports, Ignore the other requests
                {
                    my ($status, $requested_state) = $dt->get_rec("SELECT raw_value  FROM devices WHERE ah = %s AND al = %s AND port = %s AND frame_id = %s",
                                   $rx->{sh}, $rx->{sl}, $rx->{command}, $rx->{frame_id});
                    if ($status == 1)
                    {
                         # Note: only do this if the ack is the same
                         DBG&&$fp->prt("frame_id found for 0x97 BAD transmission return \n");
                         $dt->do("UPDATE devices SET try_count = try_count + 1 WHERE ah = %s AND al = %s AND port = %s AND frame_id = %s",
                             $rx->{sh}, $rx->{sl}, $rx->{command}, $rx->{frame_id});
                    }
                    else
                    {
                        DBG&&$fp->prt("bad return 0x97  =4 back not matching record [%x:%x]%s fid %s\n",
                           $rx->{sh}, $rx->{sl}, $rx->{command}, $rx->{frame_id});
                    }
                }
            }
            else
            {
                DBG&&$fp->prt("ABOVE 0x97 Packet had really bad status = %s\n", $rx->{status});
            }
        }
        elsif ( $rx->{api_type} == 0x8B ) # Transmit Status returned from 0x10 0x11 status delivery_status=0 is success
        {
            update_ack_packet($dt, $rx->{frame_id}, $rx->{delivery_status});
            DBG&&$fp->prt("process_packet:task: TRANSMIT_STATUS 0x8B frame_id[%0x] ni[%s] status[%d]",
                        $rx->{uart_frame_id}, $rx->{ni}, $rx->{delivery_status});
        }
        elsif ( $rx->{api_type} == 0x8A ) # Modem Status
        {

                       DBG&&$fp->prt("MODEM_STATUS 0x8a status=%d\n", $rx->{status});
        }
        elsif ( $rx->{api_type} == 0x90 ) # Receive Packet
        {

 #            DBG&&$fp->prt"process_packet:task: RECEIVE_PACKET 0x90[%0x %s] options = %0x data=%s\n",
 #              $rx->{sh}, $rx->{sl}, $rx->{options}, $rx->{data};
        }
        else # something else ?
        {

            #            DBG&&$fp->prt"process_packet:task: api type = %0X\n", $rx->{api_type} if DEBUG;
            #            print tools::hexDumper("", $rx) if DEBUG;
        }
        if ($rx->{cluster_id} = 0x92 && $rx->{sh} && ($rx->{sh} < 0xffffffff && $rx->{sh} > 0))  # seems we get a ZDO 0 or ffffff thing back that we should ignore
        {

            #DBG&&$fp->prt "process_packet requesting DB from xbees only %s\n", tools::hexDumper('',$rx);
            if ((! exists $db_level_in{$hash_key}) || $db_level_in{$hash_key}+HOURS12 < $rx->{timestamp}) # empty
            {
                $db_level_in{$hash_key} = $rx->{timestamp};  # request sent
                $XbeeSendQueue->enqueue({request => 'READ_REMOTE_XBEE_REGISTER', ah => $rx->{sh}, al => $rx->{sl}, reg => "DB"});
            }

            #if ((! exists $parent_addr_in{$hash_key}) || $parent_addr_in{$hash_key}+HOURS12 < $rx->{timestamp})
            #{
                #$parent_addr_in{$hash_key} =  $rx->{timestamp}; # request sent
                #$XbeeSendQueue->enqueue({request => 'READ_REMOTE_XBEE_REGISTER', ah => $rx->{sh}, al => $rx->{sl}, reg => "MP"}); # parent network address
            #}
        }
        DBG&&$fp->prt("need_to_evaluate total[%s]\n", $need_to_evaluate);
        $EvaluateQueue->enqueue() if ($need_to_evaluate);
    }
    DBG&&$fp->prt("process_packet:task: exiting\n");
}

sub evaluate_xbee_lines
{
    my ($rx) = @_;
    my $need_to_evaluate = 0;
    #my $hash_key = $rx->{sh}.':'.$rx->{sl} if ($rx->{sh});
    #if (exists $dupe_check{$hash_key} && $dupe_check{$hash_key} + 2 >=  $rx->{timestamp}) # looks like a dupe send "switch debounce" check
    #{
        #DBG&&$fp->prt("evaluate_xbee_lines: dupe/debounce check so evaluation is ignored\n");
        #return 0; # ignore
    #}
    #$dupe_check{$hash_key} = $rx->{timestamp};
    my $current_part_nbr = record_last_time_in( $dt,  $XbeeSendQueue,  $WorkerBeeQueue,
            $rx->{sh}, $rx->{sl}, $rx->{na},
            $rx->{timestamp},  $rx->{ni});
    return 0 if (!$current_part_nbr);
    DBG&&$fp->prt("evaluate_xbee_lines: API %s data sample part number = %s, sl = %X\n",  $rx->{"api_type"},  $current_part_nbr, $rx->{sl});

    #if ($current_part_nbr && $current_part_nbr =~ "RBV")
    #{
        #valve::check($dt, $XbeeSendQueue, $rx, $current_part_nbr);
    #}
    if ( $rx->{analog_inputs} )
    {
        for ( my $i = 0 ; $i < 12 ; $i++ )
        {
            if ( defined $rx->{analog_inputs}[$i] )
            {

                  #DBG&&$fp->prt"process_packet:task: A%d = %d [%0X]\n", $i,
                    #$rx->{analog_inputs}[$i], $rx->{analog_inputs}[$i]; # if $trace;
                 $need_to_evaluate += check_and_log( $dt, $WorkerBeeQueue, $EmailQueue, $rx->{sh}, $rx->{sl},$rx->{timestamp}, "A" . $i,
                    $rx->{analog_inputs}[$i]);
                DBG&&$fp->prt("evaluate_xbee_lines: analog need_to_evaluate[%s]\n", $need_to_evaluate);
                ##if ( $i == 7 )    # voltage
                ##{
                ##    DBG&&$fp->prt"process_packet:task:voltage %s\n",
                ##      tools::convert_to_volts( $rx->{analog_inputs}[$i] ) if $trace;
            }
        }
    }
    if ( $rx->{digital_inputs} )
    {
        my $digital = $rx->{digital_inputs};

        #if ($rx->{sl} == 0x4154DE97)
        #{
        #    DBG&&$fp->prt("evaluate_xbee_lines: digital array", Dumper $digital);
        #}
        for ( my $i = 0 ; $i <= $#$digital ; $i++ )
        {
            if (defined $digital->[$i])
            {
                # print "process_packet:evaluate_xbee_lines:>>> digital $i " if $trace;
                $need_to_evaluate += check_and_log( $dt, $WorkerBeeQueue, $EmailQueue, $rx->{sh}, $rx->{sl}, $rx->{timestamp}, "D".$i, $digital->[$i]);
                DBG&&$fp->prt("evaluate_xbee_lines: digital [%s] value[%s] need_to_evaluate[%s]\n",  $i, $digital->[$i],$need_to_evaluate);
            }
            else
            {
                # print "process_packet:task:<<< digital $i undef\n" if $trace;
            }
        }
        ## print "process_packet:task:\n" if $trace;
    }
    #$Watchdog->enqueue({queue => 'PUSH_TOGGLE'});
    DBG&&$fp->prt("evaluate_xbee_lines: xbee mesg causing all_ports to be done\n");
    return $need_to_evaluate;
}

sub no_ni_problem
{
      my ($type, $addr_h, $addr_l, $WorkerBeeQueue) = @_;
      $WorkerBeeQueue->enqueue({request => "LOG", fmt => "no NI for %0x - %0x:%0x", parms => [$type||0, $addr_h||0, $addr_l||0]});
      ## reboot_remote_xbee($addr_h, $addr_l);
}

sub record_signal_strength
{
    my ( $dt, $addr_high_in, $addr_low_in, $db_level ) = @_;
    #DBG&&$fp->prt"hm:record_signal_strength: signal strength %d for = %0X\n", $db_level, $addr_low_in if $trace;
    my $status = $dt->do(<<EOF,  $db_level, $addr_high_in, $addr_low_in);
            UPDATE wireless_devices SET db_level = %s WHERE ah = %s AND al = %s
EOF
}

sub record_last_time_in
{
    my ( $dt, $XbeeSendQueue,  $WorkerBeeQueue, $addr_high, $addr_low, $na, $timestamp, $part_nbr_in) = @_;
    DBG&&$fp->prt("part nbr[%s]", $part_nbr_in||'?');
    #if (!$part_nbr_in)
    #{
        #$WorkerBeeQueue->enqueue({request => "LOG", fmt => "No NI?  %X:%X [%s]",  parms => [$addr_high, $addr_low, tools::whocalled()]});
    #}

    if (!$addr_high || !$addr_low)
    {
        $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Strange device found %X:%X",  parms => [$addr_high, $addr_low]});
    }

    #if ($addr_low_in == 0x406913D9) {  # debugging thing
    #   confess "recording coordinator as a device";
    #}
    my ( $status, $physical_location, $part_nbr, $last_time_in, $previous_time_in, $firmware_version, $part_type)
         = $dt->get_rec( <<EOF, $addr_high, $addr_low );
                 SELECT wireless_devices.physical_location,
                 wireless_devices.part_nbr, wireless_devices.last_time_in, wireless_devices.previous_time_in, wireless_devices.firmware_version, device_types.part_type
                 FROM wireless_devices
                 LEFT JOIN device_types ON wireless_devices.part_nbr = device_types.part_nbr
                 WHERE wireless_devices.ah = %s AND wireless_devices.al = %s
EOF
    if ($status == 0) ## not found so is it a new device?
    {

         if ($part_nbr_in && ($part_nbr_in eq 'ZHA' || $part_nbr_in eq ' ')) # home automation request ignore if not found
         {
            $zha->insert_ha($addr_high, $addr_low, $na, "ZHA", $timestamp, $timestamp);
            $XbeeSendQueue->enqueue({request => 'HA_ENDPOINTS', ah => $addr_high, al => $addr_low, na => $na});  # for HA devices
            return 0;
         }
         DBG&&$fp->prt("check for valid part number [%s]\n", $part_nbr_in||'?');
         my ($valid_part_nbr_status) = $dt->get_rec("select 1 from device_types where device_types.part_nbr = %s", $part_nbr_in||'PARTNUMBERWASUNDEF'); # check to see if it is real
         if ($valid_part_nbr_status) # looks good, so create the new device
         {
            DBG&&$fp->prt("found [%s]\n", $part_nbr_in||'?');
            my $loc_string = tools::location_string($addr_low);
            $status = $dt->do(<<EOF, $addr_high, $addr_low, $na, $loc_string, $part_nbr_in, $timestamp, $timestamp);
            INSERT INTO wireless_devices (ah, al, na, physical_location, part_nbr, last_time_in, previous_time_in, my_network_address)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'foobar');
EOF
            insert_port_rows($dt, $addr_high, $addr_low, $timestamp);
            $part_nbr = $part_nbr_in;
            $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"});

         }
         else # no part number or just bad
         {
             DBG&&$fp->prt("no records found requesing part_number\n");
             # $XbeeSendQueue->enqueue({request => 'HA_ENDPOINTS', ah => $addr_high, al => $addr_low, na => $na});  # for HA devices
             $XbeeSendQueue->enqueue({request => 'READ_REMOTE_XBEE_REGISTER', ah => $addr_high, al => $addr_low, reg => "NI"}); # request the device name, for AA devices
             $part_nbr = undef;
         }
    }
    else ## existing device
    {
       ## if (($part_nbr_in && $part_nbr_in eq 'ZHA') || ($part_nbr && $part_nbr eq 'ZHA'))  # home automation not complete
       if ($part_nbr && $part_nbr eq 'ZHA')  # home automation not complete
       {
            $XbeeSendQueue->enqueue({request => 'HA_ENDPOINTS', ah => $addr_high, al => $addr_low, na => $na});  # for HA devices
       }
       if ($timestamp == 0 || $timestamp > ($last_time_in + 10)) # avoiding excess updates, we know it is alive
        {
           DBG&&$fp->prt(" existing part %s[%s] last_time_in recorded\n",tools::location_string($addr_low),$part_nbr);
           $status = $dt->do(<<EOF,  $timestamp, $last_time_in,  $na, $addr_high, $addr_low);
            UPDATE wireless_devices SET last_time_in = %s, previous_time_in = %s, na = %s WHERE ah = %s AND al = %s
EOF
            if (!$firmware_version && ($part_type && $part_type ne 'HA')) # no firmware_verson yet, currently only needed for voltage calculation
            {
                 DBG&&$fp->prt(" no firmware verson for [%x:%x]\n", $addr_high,$addr_low);
                $XbeeSendQueue->enqueue({request => 'READ_REMOTE_XBEE_REGISTER', ah => $addr_high, al => $addr_low, reg => "VR"}) # request the firmware_version
            }
        }
        if ( $status == 0 )
        {
            DBG&&$fp->prt("record_last_time_in:error on update of wireless_devices\n");
        }
    }
    return $part_nbr;
}

sub update_ack_packet
{
    my ($dt, $frame_id, $status) = @_;
    DBG&&$fp->prt("task: frame_id found for 0x97 good  ack \n");
    if ($status == 0)
    {
        $dt->do("DELETE FROM frame_id_ack WHERE id = %s", $frame_id);
    }
}

sub insert_port_rows
{
    my ($dt, $addr_high, $addr_low, $timestamp) = @_;

    $dt->do(<<EOF, $timestamp, $addr_high, $addr_low);
       INSERT OR IGNORE INTO sensor (ah, al,port, alarm_value_low, alarm_value_high,
          current_value, notified, transition_time, last_range_state)
       SELECT wireless_devices.ah, wireless_devices.al,
          port_types.port, port_types.alarm_value_low, port_types.alarm_value_high,
          0, 0, %s, -1
       FROM wireless_devices
       JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
       WHERE wireless_devices.ah = %s AND wireless_devices.al = %s
         AND port_types.io_direction = 1
EOF

    $dt->do(<<EOF, $addr_high, $addr_low);
       INSERT OR IGNORE INTO devices (ah, al, port, default_state, current)
       SELECT wireless_devices.ah, wireless_devices.al,
          port_types.port, 0, 2
       FROM wireless_devices
       JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
       WHERE wireless_devices.ah = %s AND wireless_devices.al = %s
        AND port_types.io_direction = 0
        AND port_types.no_default_state IS NULL
EOF

    $dt->do(<<EOF, $addr_high, $addr_low);
       INSERT OR IGNORE INTO devices (ah, al, port, default_state, current)
       SELECT wireless_devices.ah, wireless_devices.al,
          port_types.port, -1, 2
       FROM wireless_devices
       JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
       WHERE wireless_devices.ah = %s AND wireless_devices.al = %s
        AND port_types.io_direction = 0
        AND port_types.no_default_state = 1
EOF

    $dt->do(<<EOF, $addr_high, $addr_low);
       INSERT OR IGNORE INTO devices (ah, al, port, default_state, current)
       SELECT wireless_devices.ah, wireless_devices.al,
          port_types.toggle_port, -1, 2
       FROM wireless_devices
       JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
       AND port_types.toggle_port <> 'NA'
       WHERE wireless_devices.ah = %s AND wireless_devices.al = %s
        AND port_types.io_direction = 0
EOF
}

# static and semi static queries
my $port_info;
my $port_info_sql = <<EOF;
SELECT wireless_devices.ah||'-'||wireless_devices.al||'-'||port_types.port,
port_types.desc,port_types.logic, wireless_devices.part_nbr
FROM port_types
JOIN wireless_devices ON port_types.part_nbr = wireless_devices.part_nbr
EOF

my $high_low_ranges;
my $high_low_ranges_time=0;
my $high_low_range_check_sql = <<EOF;
select key, max(alarm_value_low),min(alarm_value_high)
from
(select  ah||'-'||al||'-'||port AS key, alarm_value_low,alarm_value_high
from sensor
UNION
select  ah||'-'||al||'-'||port AS key, threshold_from, threshold_to
from alerts)
group by 1
EOF

my %io_direction;
my $io_direction_sql = <<EOF;
    SELECT wireless_devices.ah||'-'||wireless_devices.al||'-'||port_types.port, io_direction
        FROM wireless_devices
        JOIN port_types ON port_types.part_nbr = wireless_devices.part_nbr
    UNION
    SELECT wireless_devices.ah||'-'||wireless_devices.al||'-'||port_types.toggle_port, io_direction
        FROM wireless_devices
        JOIN port_types ON port_types.part_nbr = wireless_devices.part_nbr
        WHERE  port_types.toggle_port <> 'NA'
EOF

sub load_static_data
{
    my ($dt) = @_;
    $port_info = $dt->query_hash_of_hash($port_info_sql, qw(desc logic part_nbr));
    #DBG&&$fp->prt STDERR "process_packet: loaded port_info %s\n", tools::remove_nl(Dumper $port_info);
    %io_direction = $dt->query_row_per_hash($io_direction_sql);
    #DBG&&$fp->prt STDERR "process_packet: loaded  io_direction %s\n", tools::remove_nl(Dumper \%io_direction);
}

sub check_and_log
{
    my ($dt, $WorkerBeeQueue, $EmailQueue, $addr_high, $addr_low, $timestamp, $port, $in_value) = @_;
    DBG&&$fp->prt("%s %s raw value [%s]\n", tools::location_string($addr_low), $port, $in_value);
    my $changed_values_count = 0;
    # what we do,is to first save away into current value
    # then test to see if the actions match up with the current value of the sensor
    # then if the action is not what is expected we request the action
    # the mass check/request is done after each recept of a 0x92 packet
    # all actions are checked at one time, actions not acked yet are ignored
    # all sensors are expected to have a db entry, actions (io_direction of 0) are ignored if they do not have
    my $hash_key = $addr_high.'-'.$addr_low.'-'.$port;

    if (!$port_info) # these are static
    {
        load_static_data($dt);
    }
    if ($high_low_ranges_time + TEN_MINUTES < $timestamp) #  these may change if user has re-configured
    {
        $high_low_ranges_time = $timestamp;
        $high_low_ranges = $dt->query_hash_of_hash($high_low_range_check_sql, qw(min max));
        DBG&&$fp->prt("loaded high_low_ranges %s\n", tools::remove_nl(Dumper $high_low_ranges));
    }
    if (! exists($io_direction{$hash_key}))  #device has not had its first report in (Ignored) OR is a digital out_port
    {
        DBG&&$fp->prt("not found in io_direction hash, usualy when a new device appears [%s]\n", $hash_key);
        load_static_data($dt);
        $high_low_ranges = $dt->query_hash_of_hash($high_low_range_check_sql, qw(min max));
        return 0;
    }
    DBG&&$fp->prt("checking io_direction hash_key[%s] io_direction[%s]\n", $hash_key, $io_direction{$hash_key});
    if ($io_direction{$hash_key} == 0) # $io_direction is a 0 direction is outward, A DEVICE not a sensor
    {
        my($st, $val) = $dt->get_rec("select validated from devices where  ah = %s AND al = %s AND port = %s", $addr_high, $addr_low, $port);
        DBG&&$fp->prt("updating devices [%x:%x}%s value[%s] current validated[%s]\n", $addr_high, $addr_low, $port, $in_value, $val); #AND (raw_value <> %s OR raw_value = NULL) , $in_value
        $dt->do("UPDATE devices SET raw_value = %s, validated = %s, last_report_time = %s WHERE ah = %s AND al = %s AND port = %s",
           $in_value, 'IODS', $timestamp, $addr_high, $addr_low, $port);
        DBG&&$fp->prt("devices rows_changed[%s]\n", $dt->rows_changed());
        return $dt->rows_changed();
    }
    DBG&&$fp->prt("is a sensor\n");
    my ($sensor_status, $sensor_adjustment, $notified, $current_value, $transition_time, $last_report_time, $last_range_state, $firmware_version, $logic, $part_nbr, $desc, $validated) =
         $dt->get_rec( <<EOF, $addr_high, $addr_low, $port);
                        SELECT sensor.adjustment, sensor.notified, sensor.current_value,
                        sensor.transition_time, sensor.last_report_time, coalesce(sensor.last_range_state,-1), wireless_devices.firmware_version,
                        port_types.logic, port_types.part_nbr, port_types.desc, sensor.validated
                        FROM sensor
                        JOIN wireless_devices ON sensor.ah = wireless_devices.ah AND sensor.al = wireless_devices.al
                        JOIN port_types ON port_types.part_nbr = wireless_devices.part_nbr AND port_types.port = sensor.port
                        WHERE sensor.ah = %s AND sensor.al = %s AND sensor.port = %s
EOF

    if ( $sensor_status == 0 )    # not found, bad thing
    {
         DBG&&$fp->prt("ERROR sensor [%x:%s} not found?, should be there\n", $addr_low, $port);
         $WorkerBeeQueue->enqueue({request => "LOG", fmt => "check_and_log: sensor not found %X:%X-%s",  parms => [$addr_high, $addr_low, $port]});
         insert_port_rows($dt, $addr_high, $addr_low, $timestamp);  # try again?
    }
    else
    {
        if ($logic eq "VOLT")
        {
               #DBG&&$fp->prt "hash key: %s value = %s\n", $hash_key, $in_value;
               $in_value = tools::convert_to_volts($firmware_version, $in_value);
        }
        if ($port =~ "^D")
        {
              DBG&&$fp->prt("port[%s][%s][%s] raw value in[%s] db current value[%s] (%s %s %s)\n",
                    $port, $logic, $validated, $in_value,$current_value, $part_nbr, $desc, tools::location_string($addr_low));
        }
    }
    # now simply hole away the sensor data
    my $value_changed=0; ## used later to indicate a change in a sensor like on changed to off
    if ($in_value ne $current_value)
    {
        $transition_time = $timestamp;
        $value_changed = 1;
    }
    DBG&&$fp->prt("has value changed from sensor value?  [%s:%s]\n",$value_changed , $value_changed?'YES':'NO');

    # was there a change in value or --- a momentary?
    DBG&&$fp->prt("email:check  [%s:%s] in_value[%s] <> current_value[%s] notified?[%s]\n",
       tools::location_string($addr_low), $logic, $in_value , $current_value, $notified);
    my $current_sensor_state = evaluate::sensor($fp, $logic, $in_value, $high_low_ranges->{$hash_key}->{min}, $high_low_ranges->{$hash_key}->{max});
    DBG&&$fp->prt("in_value[%s] current_sensor_state[%s] last_range_state[%s]\n", $in_value, $current_sensor_state, $last_range_state);

    if ($last_range_state != $current_sensor_state) # looks like the value changed or button pressed
    {
        if (($current_sensor_state == 0) && $logic =~ /^MOMENTARY/) # we don't care when a MOMENTARY goes off[0], just when they are on[1]
        {
                DBG&&$fp->prt("MOMENTARY setting back to OFF, so no data base changes\n");
                $changed_values_count++;
        }
        else
        {
            $EmailQueue->enqueue({cmd => 'sensor_check', ah => $addr_high, al => $addr_low, port => $port,
                in_value => $in_value, current_value => $current_value,
                current_sensor_state => $current_sensor_state, event_time => time});
            DBG&&$fp->prt("UPDATE sensor[%0x:%0x][%s] IODS\n", $addr_high, $addr_low, $port);
            my $status = $dt->do("UPDATE sensor SET current_value = %s, previous_value = %s, last_report_time = %s, transition_time = %s, validated = 'IODS'
                       WHERE ah = %s AND al = %s AND  port = %s", $in_value, $current_value, $timestamp, $transition_time, $addr_high, $addr_low, $port);
            DBG&&$fp->prt("UPDATE sensor returned [%s] rows changed[%s] \n", $status, $dt->rows_changed());
            $changed_values_count++;
        }
     }
     return $changed_values_count;
}

1
