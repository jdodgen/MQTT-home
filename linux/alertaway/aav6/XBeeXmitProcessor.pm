package XBeeXmitProcessor;
use Data::Dumper;
#use Time::HiRes qw (usleep);
use strict;
use cfg;
use ZigbeeHomeAutomation;
#use Carp 'cluck';
use filterPrint;
use tools qw (:debug);

my $api;

my $usleep_time = 100;
my $forever = 999999999;

my $digital_port_on = pack( 'C', 5); # turn on
my $digital_port_off = pack( 'C', 4); # turn off

my $now;

use constant START_MSG_SENT  => 1;
use constant START_ACKED  => 2;
use constant STOP_MSG_SENT  => 3;
use constant STOP_ACKED  => 4; ## never used, record is deleted when ack is back
#my $tracer;
my $zha;
my $fp;

#use constant DBG => 1;

sub task
{
    my ($trace_in, $api_in) = @_;
    $fp = filterPrint->new();
    DBG&&$fp->prt("XbeeSendQueue opening as reader = 1\n");
    my $XbeeSendQueue = QueueManager::XbeeSendQueue({reader => 1});

    # $|=1 ;
    $api = $api_in;
    # $trace=1;   #for testing
    my $dt = db::open(cfg::DBNAME);
    my $frame_id = 1;  # range will be 2-251
    my %saved_messages;
    $zha = ZigbeeHomeAutomation->new({dt => $dt, api => $api_in}); #tracer => $tracer,
    while (1)
    {
        $frame_id = 1 if ($frame_id > 250);
        $frame_id++;
        my $send = $XbeeSendQueue->dequeue;
        $now = time;
        my $hv = tools::hashValue($send);
        my $hashFound = 0;
        my $existing_frame_id;
        foreach my $key (keys %saved_messages) # search for duplicate message
        {
            if ($saved_messages{$key}{hashValue} eq $hv) # found a dupe
            {
                $hashFound = 1;
                $existing_frame_id = $key;
                last;
            }
        }
        if ($hashFound) # this message exists
        {
            my $seconds_since_first_sent = $now - $saved_messages{$existing_frame_id}{date};
            DBG&&$fp->prt("found duplicate, seconds_since_first_sent[%s]\n", $seconds_since_first_sent);
            if ($seconds_since_first_sent > 1) # looks like a new message tried, so update frame_id and send it
            {
                delete $saved_messages{$existing_frame_id};
                $saved_messages{$frame_id}{msg} = $send;
                $saved_messages{$frame_id}{date} = $now;
                $saved_messages{$frame_id}{hashValue} = $hv;
                DBG&&$fp->prt("found old duplicate [%s][%0X][%s]replaced and continuting ...", $send->{request}, $send->{al}, $hv);
            }
            else
            {
                DBG&&$fp->prt("found young duplicate message discarding[%s][%0X][%s]\n", $send->{request}, $send->{al}, $hv);
                next;
            }
        }
        else # new message, add it to hash and send it
        {
            $saved_messages{$frame_id}{msg} = $send;
            $saved_messages{$frame_id}{date} = $now;
            $saved_messages{$frame_id}{hashValue} = $hv;
            DBG&&$fp->prt("new message[%s][%0X][%s]\n", $send->{request}, $send->{al}, $hv);
        }

        # get all acks (0x8B) messages
        # remove any $saved_messages that have been acked
        # resend any messages that are old
        #$fp->filter($send->{al});
        ##my $trace = tools::is_trace(\%trace_hash,  $send->{al});
        DBG&&$fp->prt("request = %s %s\n", $send->{request}, $send->{from}?'['.$send->{from}.']':'');

        if ($send->{request} eq "BROADCAST_NODE_DISCOVERY")
        {
            broadcast_node_discovery();
        }
        elsif ($send->{request} eq "NODE_IDENTIFIER_REQUEST")
        {
            send_node_identifier_request();
        }
        elsif ($send->{request} eq "TRACE_HASH")
        {
            #$tracer->init($send->{trace_als});
            #%trace_hash = tools::hash_trace($send->{trace_als}, DEBUG);
            #DBG&&$fp->prt("trace_hash %s\n", Dumper \%trace_hash);
        }
        elsif ($send->{request} eq 'ZDO')
        {
            xbee_zdo($send->{ah}, $send->{al}, $send->{cluster_id}, $send->{payload});
        }
        elsif ($send->{request} eq 'XBEE_AT')
        {
            xbee_at($send->{cmd}, $send->{value});
        }
        elsif ($send->{request} eq 'XBEE_ALIVE_LED')
        {
            xbee_alive_led($send->{state});
        }
        elsif ($send->{request} eq 'IMAGE')
        {
            xbee_send_image_request($send->{ah}, $send->{al}, $send->{seq}, $send->{options});
        }
        elsif ($send->{request} eq 'IMAGEMORE')
        {
            xbee_send_imagemissing_request($send->{ah}, $send->{al}, $send->{seq}, $send->{missing});
        }
        elsif ($send->{request} eq 'IMAGEDONE')
        {
            send_image_done($send->{ah}, $send->{al}, $send->{seq});
        }
        elsif ($send->{request} eq 'delete')
        {
            send_image_deletes($send->{ah}, $send->{al}, $send->{deletes});
        }
        elsif ($send->{request} eq 'READ_REMOTE_XBEE_REGISTER')
        {
            read_remote_XBee_register($send->{ah}, $send->{al},  $send->{na}, $send->{reg});
        }
        elsif ($send->{request} eq 'PERMIT_JOINING')
        {
            xbee_permit_joining($send->{ah}, $send->{al}, $send->{na}, $send->{on});
        }
        elsif ($send->{request} eq 'READ_REMOTE_XBEE_REGISTER_BY_NET_ADDR')
        {
            read_remote_XBee_register_by_net_addr($send->{net_addr}, $send->{reg});
        }
        #elsif ($send->{request} eq 'PERFORM_ACTIONS')
        #{
            #actions($dt, $XbeeSendQueue, $DelayQueue, $send->{action}, $send->{ah}, $send->{al}, $send->{port});
        #}
        elsif ($send->{request} eq 'OPEN MOTORIZED VALVE')
        {
            turn_valve_motor_on($dt,  $send->{ah}, $send->{al}, $send->{na}, $send->{port}, $send->{toggle_port}, 'OPEN', $now);
        }
        elsif ($send->{request} eq 'CLOSE MOTORIZED VALVE')
        {
            turn_valve_motor_on($dt,  $send->{ah}, $send->{al}, $send->{na}, $send->{port}, $send->{toggle_port}, 'CLOSE', $now);
        }
        elsif ($send->{request} eq 'MOTORIZED VALVE RELAY OFF')
        {
            turn_valve_motor_off($dt, $send->{ah}, $send->{al},  $send->{na}, $send->{port}, $send->{toggle_port}, $send->{from});
        }
        elsif ($send->{request} eq 'TEST_ALARM') # testing an alarm or other output device
        {

            if ($send->{logic} eq "VALVE")
            {
               my ($port, $toggle_port) = simple_valve_process($dt,  $send->{ah}, $send->{al}, $send->{na}, $send->{port}); # was alarms
               $dt->do('UPDATE actions SET disabled = 1 WHERE  device_ah = %s AND device_al = %s AND device_port = %s',
                   $send->{ah}, $send->{al}, $port);
            }
            else # Normal HIGH LOW alarm
            {
                 my ($status, $logic, $duration, $toggle_port, $desc, $device_type, $endpoint, $profile_id) = $dt->get_rec(<<EOF, $send->{ah}, $send->{al}, $send->{port});
                   SELECT port_types.logic, port_types.alarm_value_low, port_types.toggle_port, port_types.toggle_port, device_types.part_type,
                   wireless_devices.endpoint
                   FROM wireless_devices
                   JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
                   JOIN device_types ON device_types.part_nbr = port_types.part_nbr
                   WHERE wireless_devices.ah = %s
                     AND wireless_devices.al = %s
                     AND port_types.port = %s
EOF
                DBG&&$fp->prt("TEST_ALARM query_status=%s, logic = %s, default duration = %s\n", $status, $logic, $duration);
                turn_action_on($dt, $send->{ah}, $send->{al}, $send->{na}, $send->{port},$ send->{toggle_port}, $endpoint, $profile_id, $logic, $now + $duration, 'HIGH LOW', $frame_id);
            }
            # clear_until_cleared_sensors($dt, $send->{ah}, $send->{al}, $send->{port}, $toggle_port);

        }
        elsif ($send->{request} eq 'DEVICE_ON')
        {
            DBG&&$fp->prt("DEVICE_ON [%04x:%04x]%s %s from[%s]\n", $send->{ah},$send->{al},$send->{port}, $send->{logic}, $send->{from}||'');
            turn_action_on($dt, $send->{ah}, $send->{al}, $send->{na}, $send->{port}, $send->{toggle_port}, $send->{endpoint}, $send->{profile_id}, $send->{logic}, $send->{state}, $frame_id);
        }
        elsif ($send->{request} eq 'FORCE_SAMPLE')
        {
            force_sample($api, $send->{ah}, $send->{al}, $send->{na}, $send->{port}, $send->{endpoint}, $send->{profile_id}, $frame_id);
        }
        elsif ($send->{request} eq 'DEVICE_OFF')
        {
            DBG&&$fp->prt("DEVICE_OFF [%04x:%04x]%s %s from[%s]\n", $send->{ah},$send->{al},$send->{port}, $send->{logic}, $send->{from}||'');
            turn_action_off($dt, $send->{ah},$send->{al}, $send->{na}, $send->{port}, $send->{toggle_port},  $send->{endpoint}, $send->{profile_id},  $send->{logic}, $frame_id);
        }
        elsif ($send->{request} eq 'HA_ENDPOINTS')
        {
            DBG&&$fp->prt("HA_ENDPOINTS [%04x:%04x]\n", $send->{ah},$send->{al});
            $zha->ha_endpoints($send->{ah},$send->{al}, $send->{na});
        }
        elsif ($send->{request} eq 'MATCH_DESCRIPTOR_RESPONCE')
        {
            DBG&&$fp->prt("MATCH_DESCRIPTOR_RESPONCE [%04x:%04x]\n", $send->{ah},$send->{al});
            $zha->match_descriptor_responce($send->{ah},$send->{al}, $send->{na},  $send->{profile_id});
        }
        elsif ($send->{request} eq 'HA_SIMPLE_DESC')
        {
            DBG&&$fp->prt("HA_SIMPLE_DESC [%04x:%04x] end_point = %s\n", $send->{ah},$send->{al}, $send->{endpoint});
            $zha->ha_simple_desc ($send->{ah},$send->{al}, $send->{na},  $send->{endpoint});
        }
        elsif ($send->{request} eq 'TOGGLEONOFF')
        {
            DBG&&$fp->prt("TOGGLEONOFF [%04x:%04x]\n", $send->{ah},$send->{al});
            $zha->turn_on_off($send->{ah}, $send->{al}, $send->{na}, $send->{endpoint}, $send->{profile_id}, 2, $frame_id);
        }
        elsif ($send->{request} eq 'GET_ON_OFF')
        {
            DBG&&$fp->prt("GET_ON_OFF [%04x:%04x]\n", $send->{ah},$send->{al});
            $zha->get_on_off($send->{ah},$send->{al}, $send->{na}, $send->{endpoint}, $send->{profile_id}, $frame_id);
        }
        else
        {
            DBG&&$fp->prt("unknown request\n");
        }
        #sleep 1;
   }
}

sub simple_valve_process
{
    my ($dt, $ah, $al, $na, $port_in, $open_or_close) = @_;
    my ($status, $logic, $duration, $port, $toggle_port, $desc) = $dt->get_rec(<<EOF, $ah, $al, $port_in);
       SELECT port_types.logic, port_types.alarm_value_low, port_types.port, port_types.toggle_port, port_types.toggle_port
       FROM wireless_devices
       JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
       WHERE wireless_devices.ah = %s
         AND wireless_devices.al = %s
         AND port_types.port = %s
EOF
    DBG&&$fp->prt("valve_process ah = %s al = %s port_in = %s port = %s toggle = %s forced open or  close = %s\n",
    $ah, $al, $port_in, $port, $toggle_port, $open_or_close||"N/A");
    if ($open_or_close)
    {
        if ($open_or_close eq 'OPEN')
        {
            turn_valve_motor_on($dt, $ah, $al, $na, $port, $toggle_port, 'OPEN',  $now + $duration);
        }
        else
        {
            DBG&&$fp->prt("VALVE to be closed port = %s\n", $port);
            turn_valve_motor_on($dt, $ah, $al, $na, $port, $toggle_port, 'CLOSE',  $now + $duration);
        }
    }
    else
    {
        if ($port_in eq $toggle_port)  # close the valve
        {
            DBG&&$fp->prt("VALVE to be closed port = %s toggle = %s\n", $port, $toggle_port);
            turn_valve_motor_on($dt, $ah, $al, $na, $port, $toggle_port, 'CLOSE',  $now + $duration);
        }
        else
        {
            turn_valve_motor_on($dt, $ah, $al, $na, $port, $toggle_port, 'OPEN',  $now + $duration);
        }
    }
    return ($port, $toggle_port);
}

sub turn_action_on
{
    my ($dt, $ah, $al, $na, $port, $toggle_port, $endpoint, $profile_id, $logic, $frame_id ) = @_;
    my $loc = tools::location_string($al);
    $fp->prt("[%0X:%0X] %s %s  port[%s] toggle_port [%s]\n", $ah, $al, $logic||'?',  $loc, $port, $toggle_port||'?');
    if ($port && $port =~ /^HA*/)  # zigbee home automation devices
    {
        my $ep = 0;
        #while ($ep++ < 0x100)
        {
            $zha->turn_on_off ($ah, $al, $na, $endpoint, $profile_id, $logic, 1, $frame_id);
            #printf "turn_action_on >>>>>>>>>>>>>>>>>>>>>>>>>>>>> testing endpoint[%0X]\n", $ep;
            #sleep 1;
        }
    }
    else  # typicaly XBee AlertAway devices
    {
        if ($logic eq 'HIGH' || $logic eq 'BINARY')
        {
            xbee_port_high($dt, $ah, $al, $na, $port, $now, $frame_id);
        }
        elsif ($logic =~ /LOW|OPEN|CLOSED/)
        {
            xbee_port_low($dt, $ah,$al,$na,$port,$now, $frame_id);
        }
        elsif ($logic eq 'VALVE') # opening valve
        {
            turn_valve_motor_on($dt, $ah, $al, $na, $port, $toggle_port, 'OPEN');
        }
    }
    # set_current_state($dt, $ah, $al, $port, $toggle_port, 'ON');
    DBG&&$fp->prt("%x:%x %s %s", $ah, $al, $port, $logic);
}

sub turn_action_off
{
    my ($dt, $ah, $al, $na, $port, $toggle_port, $endpoint, $profile_id, $logic, $frame_id) = @_;
    my $loc = tools::location_string($al);
    $fp->prt("%s %s  port %s toggle_port [%s]\n",$logic||'?',  $loc, $port, $toggle_port||'?' );
    if ($port && $port =~ /^HA*/)  # zigbee home automation devices
    {
        $zha->turn_on_off ($ah, $al, $na, $endpoint, $profile_id, $logic, 0, $frame_id)
    }
    else  # typicaly XBee AlertAway devices
    {
        if ($logic eq 'HIGH' || $logic eq 'BINARY')
        {
            xbee_port_low($dt, $ah, $al, $na, $port, $now, $frame_id);
        }
        elsif ($logic =~ /LOW|OPEN|CLOSED/)
        {
            xbee_port_high($dt, $ah,$al,$na,$port, $now, $frame_id);
        }
        elsif ($logic eq 'VALVE')
        {
             ## this needs to be different for the valves, heed to close valve, logic has it that "on" opens "off" closes
             turn_valve_motor_on($dt, $ah, $al, $na, $port, $toggle_port, 'CLOSE', $forever);
        }
    }
    # set_current_state($dt, $ah, $al, $port, $toggle_port, 'OFF');
    return;
}

sub turn_valve_motor_on
{
        my ($dt, $ah, $al, $na, $port, $toggle_port, $open_or_closed) = @_;
        my $x = $port;
        my $y = $toggle_port;
        if ($open_or_closed eq 'CLOSE')
        {
            #flip ports to revers polarity on motor
            $y = $port;
            $x = $toggle_port;
        }
        DBG&&$fp->prt("turn_valve_motor_on for: [%s-HIGH:%s-LOW] to %s valve\n", $x, $y, $open_or_closed);

        xbee_port_low($dt, $ah, $al, $na, $y, $now, 1);    # make sure other is off
        xbee_port_high($dt, $ah, $al, $na, $x, $now, 1);
}

sub turn_valve_motor_off # we turn both realys off just to be safe and easy
{
        my ($dt, $ah, $al, $na, $port, $toggle_port, $from) = @_;
        DBG&&$fp->prt("turn_valve_motor_off: [%0X:%0X]  ports [%s,%s] from[%s]\n", $ah, $al, $port, $toggle_port||"?", $from||'');
        xbee_port_low($dt, $ah, $al, $na, $port, $now,1);
        xbee_port_low($dt, $ah, $al, $na, $toggle_port, $now,1);
}

#sub set_current_state
#{
    #my ($dt, $ah, $al, $port, $toggle_port, $current) = @_;
    #$dt->do("UPDATE devices SET current =  %s WHERE ah = %s AND al = %s AND (port = %s OR port = %s)",
            #$current, $ah, $al, $port, $toggle_port);
#}

sub send_node_identifier_request
{
    my ($api, $ah, $al) = @_;
    $api->remote_at({sh => $ah, sl => $al}, 'NI');
}

sub xbee_port_high
{
    my ($dt, $ah, $al, $na, $port, $now, $fid) = @_;
    $api->remote_at({sh => $ah, sl => $al, na => $na, apply_changes => 1, frame_id  => $fid},
                    $port, $digital_port_on);
    $dt->do("UPDATE devices SET validated = %s, last_report_time = %s, frame_id = %s WHERE ah = %s AND al = %s AND port = %s",
            'NO', $now, $fid, $ah, $al, $port);
    $dt->do("UPDATE frames SET xmit_time = %s, ah = %s, al = %s, port = %s WHERE frame_id = %s", $now,  $ah, $al, $port, $fid);

    $fp->prt("[%0X:%0X:%0X]%s time %s fid=%s\n", $ah, $al, $na, $port, $now, $fid);
    return;
}

sub xbee_port_low
{
    my ($dt, $ah, $al, $na, $port, $now, $fid) = @_;
    $api->remote_at({sh => $ah, sl => $al, na => $na, apply_changes => 1, frame_id  => $fid},
                    $port, $digital_port_off);
    $dt->do("UPDATE devices SET validated = %s, last_report_time = %s, frame_id = %s WHERE ah = %s AND al = %s AND port = %s",
            'NO', $now, $fid, $ah, $al, $port);
    $dt->do("UPDATE frames SET xmit_time = %s, ah = %s, al = %s, port = %s WHERE frame_id = %s", $now,  $ah, $al, $port, $fid);
    $fp->prt("[%0X:%0X:%0X]%s time %s fid=%s\n", $ah, $al, $na, $port, $now, $fid);
}

sub xbee_permit_joining
{
    my ($ah, $al, $na, $on) = @_; # CB just causes the permit join to wake up for NJ minutes
    #my $fid = next_frame_id();
    if ($on)
    {
        $api->remote_at({sh => $ah, sl => $al, na => $na, apply_changes => 1},
                    'NJ', cfg::PERMIT_JOIN_TIME_ON);
    }
    else
    {
        $api->remote_at({sh => $ah, sl => $al, na => $na, apply_changes => 1},
                    'NJ', cfg::PERMIT_JOIN_TIME_OFF);
    }
    #$api->remote_at({sh => $ah, sl => $al, na => $na, frame_id  => $fid},
                    #'CB', cfg::CB2);
    DBG&&$fp->prt("[%0X:%0X]", $ah, $al);
}

sub broadcast_node_discovery
{
    DBG&&$fp->prt("(ND)");
    die "XBeeXmitProcessor: Failed to transmit ND node discovery"
    unless $api->at('ND'); # still have some newbys so lets see if they will answer node discovery
    #usleep($usleep_time);
}

#sub reboot_remote_XBee
#{
   #my ($addr_high, $addr_low) = @_;
   #die "XBeeXmitProcessor: Failed to transmit FR (reboot) request"
   #unless $api->remote_at(
      #{
      #sh        => $addr_high,
      #sl        => $addr_low,
      #apply_changes => 1,
      #frame_id  => 1
      #}, "FR");
      ## remote XBee software reset, it will now attempt to rejoin with a 0x95
      ##usleep($usleep_time);
#}

#sub xbee_send_image_request
#{
   #my ($addr_high, $addr_low, $seq, $options) = @_;

   #my $fid = $api->tx(
      #{
      #sh        => $addr_high,
      #sl        => $addr_low,
      #}, "image,$seq,$options");
   #DBG&&$fp->prt "XBeeXmitProcessor: sending image request to %0X : %0X  seq = %s  size = %s\n", $addr_high, $addr_low,$seq, $options if DEBUG;
   ##usleep($usleep_time);
#}

#sub xbee_send_imagemissing_request
#{
   #my ($addr_high, $addr_low, $seq, $more) = @_;

   #my $fid = $api->tx(
      #{
      #sh        => $addr_high,
      #sl        => $addr_low,
      #}, "imagemissing,$seq,$more");
       #DBG&&$fp->prt "XBeeXmitProcessor: sending imagemissing request to %0X : %0X  seq = %s  items = %s\n", $addr_high, $addr_low,$seq, $more if DEBUG;
       ##usleep($usleep_time);
#}

#sub send_image_deletes
#{
   #my ($addr_high, $addr_low, $deletes) = @_;

   #my $fid = $api->tx(
      #{
      #sh        => $addr_high,
      #sl        => $addr_low,
      #}, "delete,0,$deletes");
       #DBG&&$fp->prt "XBeeXmitProcessor: sending deletes request to %0X : %0X  to delete = %s\n", $addr_high, $addr_low,$deletes if DEBUG;
       ##usleep($usleep_time);
#}

#sub send_image_done
#{
  #my ($addr_high, $addr_low, $seq) = @_;

   #my $fid = $api->tx(
      #{
      #sh        => $addr_high,
      #sl        => $addr_low,
      #}, "imagedone,$seq");
       #DBG&&$fp->prt "XBeeXmitProcessor: sending imagedone request to %0X : %0X  seq = %s\n", $addr_high, $addr_low,$seq if DEBUG;
       ##usleep($usleep_time);
#}

sub force_sample
{
    my ($api, $addr_high, $addr_low, $na, $port, $endpoint, $profile_id, $frame_id) = @_;
    my $fid = 1;
     DBG&&$fp->prt("%0X:%0X:%0X  port [%s] profile_id[%s]\n", $addr_high, $addr_low, $na||0, $port, $profile_id||'');
    if ($port && $port =~ /^HA*/)  # zigbee HA home automation devices
    {
          if ($port eq 'HA6')  # on/off profile
          {
            $zha->get_on_off($addr_high, $addr_low, $na, $endpoint, $profile_id, $frame_id);
          }
          else
          {
              DBG&&$fp->prt("HA profile %s not implemented yet\n", $port);
          }
    }
    else # typicaly XBee AlertAway devices
    {
        DBG&&$fp->prt("force_xbee_sample [%X:%X]\n", $addr_high, $addr_low);

        die "XBeeXmitProcessor::force_sample Failed to transmit force_xbee_sample"
        unless $api->remote_at(
          {
          sh        => $addr_high,
          sl        => $addr_low,
          na        => $na,
          frame_id  => $fid
          }, 'IS');
          #usleep($usleep_time);
    }
    return $fid;
}

sub read_remote_XBee_register
{
   my ($addr_high, $addr_low, $na, $reg) = @_;
   DBG&&$fp->prt("[%X:%X] register[%s]\n", $addr_high, $addr_low, $reg);
   my $fid = 1;
   die "XBeeXmitProcessor: Failed to transmit remote request"
   unless $api->remote_at(
      {
      sh        => $addr_high,
      sl        => $addr_low,
      na        => $na,
      frame_id  => $fid
      }, $reg);
      #usleep($usleep_time);
      return $fid;
}

sub xbee_zdo
{
   my ($addr_high, $addr_low, $zdo_cluster_id, $zdo_payload) = @_;
   my $fid = 1;
   my $zdo_profile_id = 0;
   die "XBeeXmitProcessor: aborting, Failed to transmit ZDO"
   unless $api->ZBExp(
      {
      sh        => $addr_high,
      sl        => $addr_low,
      frame_id  => $fid
      }, $zdo_profile_id, $zdo_cluster_id, $zdo_payload);
      #usleep($usleep_time);
      return $fid;
}

sub read_remote_XBee_register_by_net_addr
{
   my ($net_addr, $reg) = @_;
   DBG&&$fp->prt("%X %s\n", $net_addr, $reg);
   my $fid = 1;
   die "XBeeXmitProcessor: aborting, Failed to transmit remote request"
   unless $api->remote_at(
      {
      sh        => 0,
      sl        => $net_addr,
      na        => $net_addr,
      frame_id  => $fid
      }, $reg);
      #usleep($usleep_time);
      return  $fid;
}

sub xbee_at
{
    my ($cmd, $value) = @_;
    die "XBeeXmitProcessor: Failed to transmit $cmd comand"
          unless $api->at($cmd, $value);    # reset XBee
    #usleep($usleep_time);
}

sub xbee_alive_led
{
    my ($state) = @_;
    die "XBeeXmitProcessor: Failed to transmit D0 4 request"
             unless $api->at('D0',$state?$digital_port_on:$digital_port_off);
    #usleep($usleep_time);
}

1;
