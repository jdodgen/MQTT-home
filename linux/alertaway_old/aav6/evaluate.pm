package evaluate;
# Copyright 2014,2018 by James E Dodgen Jr.  All rights reserved.

=for
This module is to evaluate the devices to see if they are in the correct state


1. manual override, done remote as in WeMo emulation or web interface
2. action of a sensor, like a water leak or motion
3. Time events like security lights
4. Default, what state it needs to be in when none of the above

steps:

gather up the information into a hash of hashes
keyed by device row_id

after hash is built then we evaluate and pick the best state
if the best state is different that current then we send a on/off zigbee command

some other rules and things to do

=cut

use Data::Dumper;
use strict;
use tools qw (:debug);
use cfg;
use QueueManager;
use db;
use filterPrint;
use valve;
use feature 'state';

my $momentary_delay = 0;
my $fp;
#use constant DBG => 1;

use constant QUEUE_TIMEOUT => 4;

my $reEvaluate=0;
sub task
{
    my ($trace_in, $api, $evaluate_pid) = @_;
    my $XbeeSendQueue = QueueManager::XbeeSendQueue();
    my $EmailQueue = QueueManager::EmailQueue();
    my $EvaluateQueue = QueueManager::EvaluateQueue({reader => 1});
    my $EvaluateQueue_enqueue = QueueManager::EvaluateQueue();
    my $dt = db::open(cfg::DBNAME);
    $fp = filterPrint->new();

    while (1)
    {
        my $cmd = $EvaluateQueue->dequeue(QUEUE_TIMEOUT); # just used mostly for an event
        #while ($Watchdog->queue_cnt())
        #{
            #DBG&&$fp->prt("flusing queue");
            #$EvaluateQueue->dequeue()
        #}

        if ($cmd && $cmd ne 'X')  # empty strings are set to this
        {
            next;
        }
        #$fp->filter();
        DBG&&DBG&&$fp->prt("STARTED");
        #next;   # for testing, turn off evaluate
        my $now = time;
        state $this_day = -1;
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now);
        if ($yday != $this_day)
        {
            $this_day = $yday;
            set_start_stop_times($dt);
        }

        my %devices;
        load_device_info($dt,\%devices);
        load_timers($dt,$now,\%devices);
        load_switch_actions($dt,\%devices);

        foreach my $d (keys %devices) # check state of each device
        {
            my $device = $devices{$d};
            #printf("device [%s]\n",$device->{port_name});
            #$fp->trace_if($device->{port_name} eq "pub");
            #$fp->filter($device->{al});
            my ($s, $ee, $rv) = $dt->get_rec("SELECT external_override, raw_value from devices where al = %s", $device->{al});

            DBG&&$fp->prt("checking device[%s] port[%s] raw_value [%s]", tools::location_string($device->{al}), $device->{port}, defined $device->{raw_value}?$device->{raw_value}:'??');
            DBG&&$fp->prt("external_override[%s] raw_value[%s]",  $ee, $rv) if ($s);
            if ($device->{port} eq 'HA8')  # not implemented ports
            {
               # DBG&&$fp->prt("ignoring %0x unimplemented port[%s]", $device->{al}, $device->{port});
                next;
            }
            #pretty_print_device($device) if($device->{logic} eq 'VALVE');
            my $override_wanted_device_state;
            my $action_wanted_device_state;
            my $timed_wanted_device_state;
            my $default_wanted_device_state = 0; # off    tristate
            $default_wanted_device_state = $device->{default_state} if ($device->{default_state}); # 1 (on) or -1 (none)

            #DBG&&$fp->prt("convert device states");
            my $device_current_state = convert_device_state($dt, $device->{logic}, $device->{ah},  $device->{al}, $device->{raw_value});
            my $toggle_current_state = convert_device_state($dt, $device->{logic}, $device->{ah},  $device->{al}, $device->{toggle_raw_value});
            if (defined $devices{$d}{override_state})  # tristate, none, on, off this is the check for not none
            {
                $override_wanted_device_state = $devices{$d}{override_state};
            }
            my $sensor;
            my $have_actions;
            ($have_actions, $action_wanted_device_state, $sensor)  = actions($dt, $device_current_state, $device, $now); # returns best action if any (undef)
            $timed_wanted_device_state = timed_event($devices{$d}, $now);  # returns a timed event that is active
            #DBG&&$fp->prt("checking in priority order");
            # now some logic to decide which to use in priority order
            #   override, sensor action, timed event, or device default
            #   returns are all tristate on off or don't care (undef)
            my $wanted_device_state;
            my $force = 0;
            if (defined $override_wanted_device_state)
            {
                DBG&&$fp->prt("using override[%s]", $override_wanted_device_state);
                $wanted_device_state = $override_wanted_device_state;
            }
            elsif ($have_actions)
            {
                DBG&&$fp->prt("using action[%s]", $action_wanted_device_state);
                $wanted_device_state = $action_wanted_device_state;
            }
            elsif (defined $timed_wanted_device_state)
            {
                my $last_report_time = $device->{last_report_time};
                DBG&&$fp->prt("using timed[%s]", $timed_wanted_device_state);
                $wanted_device_state = $timed_wanted_device_state;

                if ($last_report_time > ($now - 10) )  # have we seen it lately ?? if so trust it is correct
                {
                    # let it be checked
                }
                else # it has been a while ... so don't trust it
                {
                    $force = 1;
                }
            }
            else  # take the default
            {
                DBG&&$fp->prt("using default[%s]", $default_wanted_device_state);
                $wanted_device_state = $default_wanted_device_state;
            }

            DBG&&$fp->prt("device[%s:%s] states requested: override[%s] actions[%s] timedevents[%s] default[%s] wanted_state(result)[%s] device_current_state[%s] device raw[%s]",
                 tools::location_string($device->{al}), $device->{desc}, $override_wanted_device_state||'', $action_wanted_device_state||'',
                 $timed_wanted_device_state, $default_wanted_device_state, $wanted_device_state, $device_current_state, $device->{raw_value});
            if ($force == 1 or ($wanted_device_state > -1 && (! defined $device_current_state || $wanted_device_state != $device_current_state ||  $device->{logic} eq 'VALVE')))  # valve is complex need to run stat_change every time
            {
                DBG&&$fp->prt("STATE CHANGE");
                set_state($dt, $XbeeSendQueue, $device, $wanted_device_state, $device_current_state, $toggle_current_state, $sensor, $now);
            }
            DBG&&$fp->prt("");
        }
        if ($reEvaluate)
        {
            $EvaluateQueue_enqueue->enqueue(); # mostly for a quick turn off of a button event like an alarm
        }
        #$SIG{ALRM}=\&evaluate;
    }
}
use constant FLUFF_TIME => QUEUE_TIMEOUT*2;
sub timed_event
{
    my ($device, $now) = @_;
    #DBG&&$fp->prt("what is device?  %s", ref($$device));
    my $wanted_device_state = undef;
    my $stop_wanted_device_state;
    my $longest_stop_time = 0; # seconds in a day
    DBG&&$fp->prt("checking[%s]", tools::location_string($device->{al}));

    if ($device->{timed_events})
    {
        DBG&&$fp->prt("%s", Dumper $device->{timed_events});
        foreach my $a (keys (%{$device->{timed_events}}))
        {
             my $time_to_start = $device->{timed_events}{$a}{time_to_start};
             my $time_to_stop = $device->{timed_events}{$a}{time_to_stop};
             my $time_since_start = $now - $time_to_start;
             DBG&&$fp->prt("now - time_to_start %d", $time_since_start);
             if ($time_since_start < FLUFF_TIME) # inside start window
             {
                 DBG&&$fp->prt("Start timer needed");
                 $wanted_device_state = $device->{timed_events}{$a}{state} ? 1 : 0;
                 last;  #no need to find another
             }
             if ($time_to_stop > $longest_stop_time)
             {
                 $longest_stop_time = $time_to_stop;
                 $stop_wanted_device_state = $device->{timed_events}{$a}{state}?0:1; # note invert of start
             }
        }
        my $time_after_stop = $longest_stop_time - $now;
        DBG&&$fp->prt("longest_stop_time - now %d", $time_after_stop);
        if ($longest_stop_time && $time_after_stop < FLUFF_TIME) # with in stop window
        {
            DBG&&$fp->prt("Stop timer needed");
            $wanted_device_state = $stop_wanted_device_state;
        }
    }
    DBG&&$fp->prt("timers show that It should be [%s]", $wanted_device_state);
    return $wanted_device_state;
}

sub actions
{
    my ($dt,$device_current_state, $device, $now) = @_;
    my $wanted_device_state;
    my $wanted_sensor;
    if ($device->{actions}) # do we have actions for this device?
    {
        my $action_id;
        foreach $action_id (keys (%{$device->{actions}}))
        {
            DBG&&$fp->prt("action_id[%s]", $action_id);
            my $action = $device->{actions}{$action_id};
            my $sloc;
            my $oploc;
            if ($fp->on)
            {
                $sloc = tools::location_string($action->{sensor}{al});# if $trace;
                $oploc = tools::location_string($device->{al});# if $trace;
                DBG&&$fp->prt("sensor[%s-%s:%s] id[%s] on_or_off[%s] device[%s:%s-%s:%s] duration[%s] should be[%s], validated[%s]",
                         $sloc, $action->{sensor}{desc}, $action->{sensor}{logic},
                         $action->{sensor}{id}, $action->{sensor_on_or_off}||'?',
                         $oploc, $device->{port}, $device->{desc}||'', $device->{logic},
                         $action->{duration}, $action->{action_on_or_off},
                         $action->{sensor}{validated});
            }
            # we ignore lower priority actions
            my $device_should_be;
            my $is_on;
            my $changed;
            my $sensor_state =  sensor($fp,$action->{sensor}{logic}, $action->{sensor}{current_value},
                          $action->{sensor}{alarm_value_low}, $action->{sensor}{alarm_value_high});
            if ($action->{sensor}{logic} =~ /^MOMENTARY(\d)/) # these have priority
            {
                my $nbr = $1;
                DBG&&$fp->prt("checking MOMENTARY[%s] validated[%s] delta time[%s]",  $action->{sensor}{id}, $action->{sensor}{validated}, $now - $action->{sensor}{last_report_time});
                if ($action->{sensor}{last_report_time}+$momentary_delay < $now and $action->{sensor}{validated} ne 'DONE')
                {
                    DBG&&$fp->prt("UPDATE MOMENTARY sensor id[%s] DONE",  $action->{sensor}{id});
                    $dt->do("UPDATE sensor SET validated = 'DONE', current_value = %s WHERE id = %s", 1 - $nbr, $action->{sensor}{id});
                }
                elsif ($action->{sensor}{validated} eq 'DONE') # this has been worked
                {
                    DBG&&$fp->prt("priority or MOMENTARY bypassing [%s-%s:%s]  validated [%s]",
                        $sloc, $action->{sensor}{desc}, $action->{sensor}{logic},
                        $action->{sensor}{validated});
                }
                else
                {
                    $wanted_device_state = wanted_device_state($action->{sensor_on_or_off}, $sensor_state, $action->{action_on_or_off});
                    $wanted_sensor = $device->{actions}{$action_id}{sensor};

                    last if ($device_current_state != $wanted_device_state); # button press so bail
                }
            }
            else
            {
                 $wanted_device_state = wanted_device_state($action->{sensor_on_or_off}, $sensor_state, $action->{action_on_or_off});
                 $wanted_sensor = $device->{actions}{$action_id}{sensor};

                 DBG&&$fp->prt("for this action sensor[%s:%s] is %s device[%s:%s] should be[%s] and is currently[%s]",
                      $sloc, $action->{sensor}{logic}, $sensor_state, $oploc, $device->{logic}, $wanted_device_state, $action->{sensor}{current_value});

                 if ($action->{duration} eq "Follow" || $action->{sensor_on_or_off} == $sensor_state)
                 {
                    ##$op_rowid{$device->{rowid}} = 1;  # this is higher priority, ignore the rest  #############  should this be action?? #################
                 }
            }
            DBG&&$fp->prt("at end action_id[%s]", $action_id);
        }
        if (defined $wanted_device_state)
        {
            return (1, $wanted_device_state, $wanted_sensor);
        }
    }
    return 0;
}

sub set_state  # this might be better in its own thread, fired every minute or every change of state.
{
    my ($dt, $XbeeSendQueue, $device, $wanted_device_state, $device_current_state, $toggle_current_state, $sensor, $now) = @_;
    my $alpha_wanted_device_state =  $wanted_device_state?'ON':'OFF';
    DBG&&$fp->prt("[%0x] wanted[%s] current[%s] sensor id[%s]", $device->{al}, $wanted_device_state, $device_current_state, defined $sensor->{id}?$sensor->{id}:'?');

    if (!defined($device_current_state) || ($wanted_device_state != $device_current_state))
    {
        $dt->do("UPDATE devices SET current =  %s  WHERE ah = %s AND al = %s AND (port = %s OR port = %s)",
             $alpha_wanted_device_state, $device->{ah}, $device->{al}, $device->{port}, $device->{toggle});
    }
    if ($device->{logic} eq 'VALVE') # this one is very special and complex
    {
        #pretty_print_device($device);
        valve::check($XbeeSendQueue, $wanted_device_state, $device->{ah}, $device->{al}, $device->{na}, $device->{open_limit}, $device->{closed_limit}, $device_current_state, $toggle_current_state);
    }
    elsif (!defined($device_current_state) || ($wanted_device_state != $device_current_state))  # got a change or just not in correct state
    {
        DBG&&$fp->prt(" now doing xbeesendqueue");
        my $request = $wanted_device_state?'DEVICE_ON':'DEVICE_OFF';
        $XbeeSendQueue->enqueue({request => $request, ah => $device->{ah}, al =>  $device->{al}, na => $device->{na}, endpoint => $device->{endpoint},
              port => $device->{port}, toggle_port => $device->{toggle}, logic =>  $device->{logic}, profile_id =>  $device->{profile_id},  from => 'actions loop'});
        # the following will be going on MOMENTARY will need the time to stay on. Others
        # for the winning action?
        if ($sensor->{id})
        {
            if ($sensor->{logic} =~ /^MOMENTARY(\d)/ )
            {
                my $nbr = $1;
                if ($sensor->{last_report_time}+$momentary_delay < $now)
                {
                    DBG&&$fp->prt("UPDATE MOMENTARY sensor id[%s]",  $sensor->{id});
                    $dt->do("UPDATE sensor SET validated = 'DONE', current_value = %s WHERE id = %s", 1 - $nbr, $sensor->{id});
                    $reEvaluate=1;
                }
            }
            else
            {

                DBG&&$fp->prt("UPDATE validated DONE to sensor id[%s] not momentary",  $sensor->{id});
                $dt->do("UPDATE sensor SET validated = 'DONE' WHERE id = %s", $sensor->{id});
                $reEvaluate=1;
            }
        }
    }
}

sub sensor
{
    my ($fp, $logic, $value, $min, $max) = @_;
    DBG&&$fp->prt("logic [%s], value [%s], min [%s], max [%s]",   $logic||'?', (defined $value)?$value:'?', (defined $min)?$min:'?',
        $max||'????????????????????????????????????????????');
    my $state = 0;
    if ( ($logic eq "MOMENTARY1" && $value == 1)
      || ($logic eq "MOMENTARY0" && $value == 0)
      || ($logic eq "H2O" && $value <  $max)
      || (($logic eq "SW1" || $logic eq "SIG1") && $value == 1) #
      || (($logic eq "OPEN" || $logic eq "CLOSED") && $value == 0)
      || (($logic eq "SW0" || $logic eq "SIG0") && $value == 0)
      || (($logic eq "TMP36" || $logic eq "VOLT") ## range check sensors
                   && ($value > $min &&  $value < $max)))
    {
        $state = 1;
    }
    DBG&&$fp->prt("logic[%s] raw value[%s] min:max [%s:%s] result[%s]", $logic, $value, $min||'?', $max||'?', $state);
    return $state;
}

sub wanted_device_state
{
    my ($wanted_sensor_state, $current_sensor_state, $wanted_device_state) = @_;
    my $device_needed_state;
    if  ($wanted_sensor_state) # on
    {
        if ($current_sensor_state) #on
        {
            if ($wanted_device_state) # on
            {
                $device_needed_state = 1;
            }
            else #  or off
            {
                $device_needed_state = 0;
            }
        }
        else  # sensor currently off
        {
            if ($wanted_device_state) # on
            {
                $device_needed_state = 0;
            }
            else #  or off
            {
                $device_needed_state = 1;
            }
        }
    }
    else # wanted sensor off
    {
        if ($current_sensor_state) #on
        {
            if ($wanted_device_state) # on
            {
                $device_needed_state = 0;
            }
            else # wanted off
            {
                $device_needed_state = 1;
            }
        }
        else  # sensor currently off
        {
            if ($wanted_device_state) # on
            {
                $device_needed_state = 0;
            }
            else # wanted off
            {
                $device_needed_state = 1;
            }
        }

    }
    DBG&&$fp->prt("when sensor is %s we want device to be %s current sensor %s so device needs to be %s",
         $wanted_sensor_state,  $wanted_device_state, $current_sensor_state, $device_needed_state);
    return $device_needed_state;
}

sub convert_device_state
{
    my ($dt, $logic, $ah, $al, $value) = @_;
    #DBG&&$fp->prt("evaluate::convert_device_state: al[%0x]logic[%s]value[%s]", $al, $logic, $value);
    if (defined $value && $logic =~ /LOW|OPEN|CLOSED/)
    {
        $value = 1 - $value; # flip it
    }
    return $value;
}

my $device_info_last_dt;
my $device_info_sth;
my @device_info_fields = qw(rowid port_name ah al port current raw_value default_state override_state external_override last_report_time toggle logic desc volatle_raw_value endpoint profile_id na last_time_in closed_limit open_limit toggle_raw_value);
my $device_info_sql = <<EOF;
SELECT  devices.rowid, devices.port_name, devices.ah, devices.al, devices.port, devices.current, devices.raw_value,
    devices.default_state, devices.override_state, devices.external_override, devices.last_report_time,
    port_types.toggle_port, port_types.logic, port_types.desc,
    port_types.volatle_raw_value,
    wireless_devices.endpoint, wireless_devices.profile_id, wireless_devices.na, wireless_devices.last_time_in,
    closed_limit.current_value,  open_limit.current_value, toggle.raw_value
FROM devices
JOIN wireless_devices ON wireless_devices.ah = devices.ah
    AND wireless_devices.al = devices.al
JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
    AND port_types.port = devices.port
LEFT JOIN sensor AS closed_limit ON wireless_devices.ah = closed_limit.ah
    AND wireless_devices.al = closed_limit.al AND closed_limit.port = 'D7'  AND port_types.part_nbr = 'RBV2'
LEFT JOIN sensor AS open_limit ON wireless_devices.ah = open_limit.ah
    AND wireless_devices.al = open_limit.al AND open_limit.port = 'D4'  AND port_types.part_nbr = 'RBV2'
LEFT JOIN devices AS toggle ON toggle.ah = devices.ah
    AND toggle.al = devices.al AND toggle.port = port_types.toggle_port
EOF

sub load_device_info
{
    my ($dt, $devices) = @_;
    if (! $device_info_last_dt)
    {
        DBG&&$fp->prt("doing prepare, if you see this late in the run you have a memory leak");
        $device_info_last_dt = $dt;
        $device_info_sth = $dt->query_prepare($device_info_sql);
    }
    my @dev = $dt->loop_query_execute($device_info_sth, @device_info_fields);
    #DBG&&$fp->prt("dump dev ", Dumper @dev);
    foreach my $d (@dev)
    {
        my %device=();
        $device{rowid}=$d->{rowid};
        $device{ah}=$d->{ah};
        $device{al}=$d->{al};
        $device{port}=$d->{port};
        $device{current}=$d->{current};
        $device{raw_value}=$d->{raw_value};
        $device{toggle}=$d->{toggle};
        $device{logic}=$d->{logic};
        $device{desc}=$d->{desc};
        $device{volatle_raw_value}=$d->{volatle_raw_value};
        $device{endpoint}=$d->{endpoint};
        $device{profile_id}=$d->{profile_id};
        $device{default_state}=$d->{default_state};
        $device{override_state}=$d->{override_state};
        $device{external_override}=$d->{external_override};
        $device{last_report_time}=$d->{last_report_time};
        $device{na}=$d->{na};
        $device{port_name}=$d->{port_name};
        $device{last_time_in}=$d->{last_time_in};
        $device{closed_limit}=$d->{closed_limit};
        $device{open_limit}=$d->{open_limit};
        $device{toggle_raw_value}=$d->{toggle_raw_value};
        $devices->{$d->{rowid}}=\%device;
    }
}


my $timed_events_last_dt;
my $timed_events_sth;
my @timed_events_fields = qw(devices_rowid timed_events_rowid days time_to_start time_to_stop state);
my @timed_events_sql = <<EOF;
SELECT devices.rowid, timed_events.rowid, timed_events.days, timed_events.time_to_start, timed_events.time_to_stop,
    timed_events.state
FROM timed_events
JOIN devices ON devices.ah = timed_events.ah
     AND devices.al = timed_events.al
     AND devices.port = timed_events.port
WHERE timed_events.days LIKE strftime('%%%w%%','now' ,'localtime');
EOF


##LEFT JOIN actions ON actions.action_id =  timed_events.action_id
sub load_timers
{
    my ($dt, $now, $devices) = @_;
    # get timers that should be on now left joined with actions also if sensor is on/off
    if (! $timed_events_last_dt)
    {
        DBG&&$fp->prt("doing prepare, if you see this late in the run you have a memory leak");
        $timed_events_last_dt = $dt;
        $timed_events_sth = $dt->query_prepare(@timed_events_sql);
    }
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now);
    DBG&&$fp->prt("localtime %s:%s:%s ", $hour,$min,$sec);
    #my ($status, $d, $strftime) = $dt->get_rec("Select days, strftime('%%%w%%','now' ,'localtime') from timed_events");
    #DBG&&$fp->prt("days[%s] strftime[%s]", $d, $strftime) if ($status);
    #my $midnight = tools::midnight($now); # epoch last midnight
    my @timers = $dt->loop_query_execute($timed_events_sth, @timed_events_fields);
    #DBG&&$fp->prt("timers", Dumper @timers);
    foreach my $t (@timers) # found some timers for today
    {
        # check each one to see if it should be on
        my $device_rowid = $t->{devices_rowid};
        my $timed_events_rowid = $t->{timed_events_rowid};
        my $time_to_start = $t->{time_to_start};
        my $time_to_stop = $t->{time_to_stop};
        if ($time_to_start <= $now and $time_to_stop >= $now)  # should be ON acording to timer
        {
            # if a external override is in place we have to decide to remove it.
            # if the timer is just starting then remove it if the timer has been around for a while leve it in place
            if ($devices->{$device_rowid}{external_override} && $devices->{$device_rowid}{external_override} == 1)  # it is overridden
            {
                if (($time_to_start < $now && $time_to_start+20 > $now)   # just starting so remove override made before this timer
                    ||                                                      # or
                    ($time_to_stop >= $now && $time_to_stop+20 > $now)) # we are done with override of this timer
                {
                    DBG&&$fp->prt("removing external_override  if [%s<%s] and [%s>%s]", $time_to_start , $now, $time_to_start+20, $now);
                    DBG&&$fp->prt("removing external_override  or [%s>%s]", $time_to_stop+20, $now);
                    tools::remove_override($dt, $device_rowid);
                }
            }
            DBG&&$fp->prt("this timer should be on now, saving stuff away");
            my %event;
            $event{time_to_stop}=$time_to_stop;
            $event{time_to_start}=$time_to_start;
            $event{state}=$t->{state};
            $devices->{$device_rowid}{timed_events}{$timed_events_rowid}=\%event;
       }
    }
    if (!@timers)
    {
        DBG&&$fp->prt("NO TIMERS FOUND");
    }
}

my $actions_last_dt;
my $actions_sth;
my @actions_fields = qw(devices_rowid action_id sensor_ah sensor_al sensor_port
sensor_on_or_off action_on_or_off on_time off_time duration priority sensor_logic sensor_desc
sensor_current_value sensor_previous_value
alarm_value_low alarm_value_high sensor_id sensor_validated last_report_time);
my $actions_sql = <<EOF;
SELECT devices.rowid, actions.action_id, sensor.ah, sensor.al, sensor.port,
        actions.sensor_on_or_off, actions.action_on_or_off, actions.on_time, actions.off_time,
        actions.duration, actions.priority, port_types.logic, port_types.desc,
        sensor.current_value, sensor.previous_value, sensor.alarm_value_low,  sensor.alarm_value_high,
        sensor.id, sensor.validated, sensor.last_report_time
FROM actions
JOIN sensor ON sensor.ah = actions.ah
    AND sensor.al = actions.al AND sensor.port = actions.port
JOIN wireless_devices ON wireless_devices.ah = sensor.ah
    AND wireless_devices.al = sensor.al
JOIN devices ON devices.ah = actions.device_ah
    AND devices.al = actions.device_al
    AND devices.port =  actions.device_port
JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
    AND port_types.port = actions.port
WHERE actions.disabled = 0
EOF
sub load_switch_actions
{
    my ($dt, $devices) = @_;
    if (! $actions_last_dt)
    {
        DBG&&$fp->prt("doing prepare, if you see this late in the run you have a memory leak");
        $actions_last_dt = $dt;
        $actions_sth = $dt->query_prepare($actions_sql);
    }
    my @actions = $dt->loop_query_execute($actions_sth, @actions_fields);
    #DBG&&$fp->prt("query %s", Dumper \@actions);
    foreach my $a (@actions)
    {
        DBG&&$fp->prt("rowid[%s] action id[%s] sensor[%s] duration[%s]", $a->{devices_rowid}, $a->{action_id}, tools::location_string($a->{sensor_al}),$a->{duration});
        my %action;
        $action{sensor}{ah} = $a->{sensor_ah};
        $action{sensor}{al} = $a->{sensor_al};
        $action{sensor}{port}=$a->{sensor_port};
        $action{sensor_on_or_off}=$a->{sensor_on_or_off};
        $action{action_on_or_off}=$a->{action_on_or_off};
        $action{sensor}{current_value}=$a->{sensor_current_value};
        $action{sensor}{previous_value}=$a->{sensor_previous_value};
        $action{sensor}{alarm_value_low}=$a->{alarm_value_low};
        $action{sensor}{alarm_value_high}=$a->{alarm_value_high};
        $action{sensor}{validated}=$a->{sensor_validated};
        $action{sensor}{last_report_time}=$a->{last_report_time};
        $action{duration}=$a->{duration};
        $action{priority}=$a->{priority};
        $action{sensor}{logic}=$a->{sensor_logic};
        $action{sensor}{desc}=$a->{sensor_desc};
        $action{sensor}{id}=$a->{sensor_id};

        $devices->{$a->{devices_rowid}}{actions}{$a->{action_id}} = \%action;
        #DBG&&$fp->prt("device entry %s", Dumper $devices->{$a->{devices_rowid}}{actions});
    }

}

sub pretty_print_device
{
    if ($fp->on)
    {
        my ($device) = @_;
        foreach my $dpart (keys %{$device})
        {
            my $value = defined $device->{$dpart}?$device->{$dpart}:'undef';
            DBG&&$fp->prt("Device > %s = %s", $dpart,$value);
        }
        foreach my $a (keys %{$device->{actions}})
        {
            DBG&&$fp->prt("Device > action_id >  %s", $a);
            foreach my $apart (keys (%{$device->{actions}{$a}}))
            {
                my $value = defined  $device->{actions}{$a}{$apart}? $device->{actions}{$a}{$apart}:'undef';
                DBG&&$fp->prt("device > action > %s = %s", $apart,$value);
            }
            foreach my $s (keys %{$device->{actions}{$a}{sensor}})
            {
                my $value = defined  $device->{actions}{$a}{sensor}{$s}? $device->{actions}{$a}{sensor}{$s}:'undef';
                DBG&&$fp->prt("device > action > Sensor > %s = %s", $s, $value);

            }
        }
        foreach my $t (keys %{$device->{timed_events}})
        {
            DBG&&$fp->prt("device > timed_event id > %s", $t);
            foreach my $tpart (keys (%{$device->{timed_events}{$t}}))
            {
                my $value = defined  $device->{timed_events}{$t}{$tpart}? $device->{timed_events}{$t}{$tpart}:'undef';
                DBG&&$fp->prt("device > timed_event > %s = %s", $tpart, $value);
            }
        }
    }
}

sub set_start_stop_times
{
    my ($dt) = @_;
    my $cfg = tools::get_config($dt);
    my $midnight = tools::midnight(time); # epoch last midnight
    my ($sunrise_hour, $sunrise_minute, $sunset_hour, $sunset_minute) =  tools::sunRiseSet($cfg->{latitude}||0,$cfg->{longitude}||0);
    my @timed = $dt->tmpl_loop_query(
        "SELECT rowid, start_type, start_hour, start_minute, start_offset, stop_type, stop_hour, stop_minute, stop_offset FROM timed_events",
        qw(rowid start_type start_hour start_minute start_offset stop_type stop_hour stop_minute stop_offset));
    foreach my $t (@timed)
    {
        my $start_hour=0;
        my $start_minute=0;
        my $start_offset=0;
        my $stop_hour=0;
        my $stop_minute=0;
        my $stop_offset=0;
        if ($t->{start_type} eq "Fixed")
        {
            $start_hour = $t->{start_hour};
            $start_minute = $t->{start_minute};
        }
        elsif ($t->{start_type} eq "Sunset")
        {
            $start_hour = $sunset_hour;
            $start_minute = $sunset_minute;
            $start_offset = $t->{start_offset};
        }
        elsif ($t->{start_type} eq "Sunrise")
        {
            $start_hour = $sunrise_hour;
            $start_minute = $sunrise_minute;
            $start_offset = $t->{start_offset};
        }

        my $seconds_from_midnight =  tools::seconds_from_midnight($start_minute, $start_hour);
        my $time_to_start = $seconds_from_midnight + $midnight + $start_offset;

        if ($t->{stop_type} eq "Fixed")
        {
            $stop_hour = $t->{stop_hour};
            $stop_minute = $t->{stop_minute};
        }
        elsif ($t->{stop_type} eq "Sunset")
        {
            $stop_hour = $sunset_hour;
            $stop_minute = $sunset_minute;
            $stop_offset = $t->{stop_offset};
        }
        elsif ($t->{stop_type} eq "Sunrise")
        {
            $stop_hour = $sunrise_hour;
            $stop_minute = $sunrise_minute;
            $stop_offset = $t->{stop_offset};
        }
        $seconds_from_midnight =  tools::seconds_from_midnight($stop_minute, $stop_hour);
        my $time_to_stop = $seconds_from_midnight + $midnight + $stop_offset;
        my $status = $dt->do("UPDATE timed_events SET time_to_start = %s, time_to_stop = %s WHERE rowid = %s", $time_to_start, $time_to_stop, $t->{rowid});
    }
}

#
#
# test code
#
#

#use QueueManager;
#my $XbeeSendQueue = QueueManager::XbeeSendQueue();
#my $dt = db::open(cfg::DBNAME);
#evaluate($dt, $XbeeSendQueue);
1,





