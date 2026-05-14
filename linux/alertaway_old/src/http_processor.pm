package http_processor;
# Copyright 2011,2020, 2024 by James E Dodgen Jr.  All rights reserved.
# now released under MIT Licence 2024 Jim Dodgen
use Data::Dumper;
use IO::Socket;
use HTML::Template;
use html;
use POSIX ":signal_h";
use POSIX ":sys_wait_h";
use strict;
use tools;
use processManager;
use evaluate;
use ip_tools;
use cfg;
use Filesys::Df;
use LWP::Simple;
use filterPrint;
use system_load;
use extern;
# use DateTime;

use constant FRESH_READ => 1;
use Crypt::Password;
my $message;
my $fp = filterPrint->new();
use constant DBG => 1;

sub process
{
    my ($method, $dt, $now, $main_pid, $WorkerBeeQueue, $XbeeSendQueue, $Watchdog, $EmailQueue, $EvaluateQueue, %form) = @_;
    $message = '';
    # $fp = filterPrint->new();
    $fp->filter();
    my $t;
    my $menu_submit;
    #DBG&&$fp->prt("process: method[%s] form = %s", $method, Dumper \%form);
    if ($method eq "main")
    {
        ($t,$menu_submit)=main_page($dt, $now, $XbeeSendQueue, $WorkerBeeQueue,  $Watchdog, %form);
    }
    elsif ($method eq "contacts")
    {
        ($t,$menu_submit)=contacts($dt, $now, $WorkerBeeQueue, %form);
    }
    elsif ($method eq "alerts")
    {
        ($t,$menu_submit)=alerts($dt, $now, $XbeeSendQueue, $WorkerBeeQueue, $Watchdog, $EmailQueue, %form);
    }
    #elsif ($method eq "commission")
    #{
        #($t,$menu_submit)=commission($dt, $XbeeSendQueue);
    #}
    elsif ($method eq "configuration")
    {
        ($t,$menu_submit)=config($dt, $now, $main_pid, $WorkerBeeQueue, $XbeeSendQueue, $Watchdog, %form);
    }
    #elsif ($method eq "Debug")
    #{
        #($t,$menu_submit)=debug($dt, $WorkerBeeQueue, %form);
    #}
    elsif ($method eq "location")
    {
       ($t,$menu_submit)=location($dt, $now, %form);
    }
    elsif ($method eq "system")
    {
        ($t,$menu_submit)=system_info($dt, $now, %form);
    }
    #elsif ($method eq "trace")
    #{
        #($t,$menu_submit)=trace_info($dt, $now, %form);
    #}
    $t->param( msg => $message) if ($t);
    #$EvaluateQueue->enqueue();
    #DBG&&$fp->prt("process: leaving");
    return ($t,$menu_submit);
}

sub alerts
{
    my ($dt, $now, $XbeeSendQueue, $WorkerBeeQueue, $Watchdog, $EmailQueue, %form) = @_;
    my $t = HTML::Template->new_scalar_ref( html::alerts(),
            ( xdebug => 1, xstack_debug => 1 ) );
    my $cfg = tools::get_config($dt,FRESH_READ);
    DBG&&$fp->prt("alerts: start state[%s]", $form{state}||'undef');
    if ( $form{state})
    {
        if ( $form{state} eq "Map alarm" )
        {
            $t->param( alarms_here => "here");
            if ($form{"SENSORTOALARM:sensor"})
            {
               my ($addr_high, $addr_low, $port) = split /\:/, $form{"SENSORTOALARM:sensor"};
               my ($part_nbr, $sensor_logic, $toggle_port) = get_part_info($dt, $addr_high, $addr_low, $port);
               if ($form{"SENSORTOALARM:alarm"})
               {
                    my @alarms = split /\,/, $form{"SENSORTOALARM:alarm"};
                    foreach my $a (@alarms)
                    {
                       my ($action_addr_high, $action_addr_low, $action_port, $logic, $devices_rowid) = split /\:/, $a;
                       my ($device_part_nbr, $device_logic, $device_toggle_port) = get_part_info($dt, $action_addr_high, $action_addr_low, $action_port);
                       my $duration = 2;
                       if (must_follow($sensor_logic))
                       {
                          $duration = 'Follow';
                       }
                       my $status = $dt->do("INSERT INTO actions (ah, al, port, part_nbr, logic, toggle_port,
                       device_ah,device_al, device_port, device_part_nbr, device_logic, device_toggle_port,
                       duration, priority, disabled, sensor_on_or_off, action_on_or_off) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,5,0,1,1)",
                        $addr_high, $addr_low, $port, $part_nbr, $sensor_logic, $toggle_port,
                        $action_addr_high, $action_addr_low, $action_port, $device_part_nbr, $device_logic, $device_toggle_port, $duration);
                        my $rid = $dt->last_insert_rowid();
                        DBG&&$fp->prt("alerts: last_insert_rowid rid[%s]",$rid);
                    }
               }
            }
        }
        elsif ( $form{state} eq "Set timer" )
        {
            $t->param( timers_here => "here");  # html positioning tag
            if (exists $form{"TIMED:alert"} && exists $form{"TIMED:days"})
            {
                my $start_hour = 0;
                my $start_minute = 0;
                my $start_offset =0;
                my $stop_hour = 0;
                my $stop_minute = 0;
                my $stop_offset =0;
                if ($form{"TIMED:start"} eq "Fixed")
                {
                    $start_hour = $form{"TIMED:starthour"};
                    $start_minute = $form{"TIMED:startminute"};
                }
                else
                {
                    $start_offset = $form{"TIMED:startoffset"};
                }
                if ($form{"TIMED:stop"} eq "Fixed")
                {
                    $stop_hour = $form{"TIMED:stophour"};
                    $stop_minute = $form{"TIMED:stopminute"};
                }
                else
                {
                    $stop_offset = $form{"TIMED:stopoffset"};
                }
                my ($addr_high, $addr_low, $port, $devices_rowid) = split /\:/, $form{"TIMED:alert"};
                my $status = $dt->do(
                         "INSERT INTO timed_events (ah, al, port, days, start_type, stop_type, start_hour, start_minute, start_offset,  stop_hour, stop_minute, stop_offset,  state) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            $addr_high, $addr_low, $port,$form{'TIMED:days'},$form{"TIMED:start"},$form{"TIMED:stop"},
                            $start_hour,$start_minute,$start_offset,$stop_hour,$stop_minute,$stop_offset,
                            $form{'TIMED:state'});
                evaluate::set_start_stop_times($dt);
            }
            else
            {
                $t->param(timer_msg => "Timed alert failed, missing device or days?");
            }
        }
        elsif ( $form{state} =~ /^Remove\s*Timer\:(\d*)$/ )
        {
            $t->param( timers_here => "here");
            my $rowid = $1;
            $dt->do("DELETE FROM timed_events WHERE rowid = %s", $rowid);
        }
        elsif ($form{state} eq "Test" && $form{"SENSORTOALARM:alarm"})
        {
          my @alarms = split /\,/, $form{"SENSORTOALARM:alarm"};
          foreach my $a (@alarms)
          {
             my ($action_addr_high, $action_addr_low, $action_port, $logic, $devices_rowid  ) = split /\:/, $a;
             $dt->do("UPDATE actions SET disabled = 1  WHERE device_ah = %s AND device_al = %s AND device_port = %s",
                   $action_addr_high, $action_addr_low, $action_port);
             $XbeeSendQueue->enqueue({request => 'TEST_ALARM',
               ah => $action_addr_high, al => $action_addr_low, port => $action_port, logic => $logic}) if($XbeeSendQueue);
          }
        }
        #elsif ( $form{state} =~ /Enable:(\d*)$/ )
        #{
            #my $rowid = $1;
            #my ($stat, $ah, $al, $port) = $dt->get_rec("SELECT ah, al, port FROM actions WHERE rowid = %s", $rowid);
            #if ($stat == 1)
            #{
               #$dt->do("UPDATE actions SET disabled = 0 WHERE rowid = %s", $rowid);
               ##$dt->do("DELETE FROM sensor_activity WHERE ah = %s AND al = %s AND port = %s", $ah, $al, $port);
               #$Watchdog->enqueue({queue => 'WakeUp'});
            #}
        #}
        elsif ( $form{state} =~ /Update\s*Alert:(\d*)$/)
        {
            $t->param(alarms_here => "here");
            my $rowid = $1;
            my $priority = $form{"SENSORTOALARM:priority:${rowid}"};
            my $sensor_on_or_off = $form{"SENSORTOALARM:sensor_action:${rowid}"} eq 'ON'?1:0;
            my $action_on_or_off = $form{"SENSORTOALARM:action_action:${rowid}"} eq 'ON'?1:0;
            if ($form{"SENSORTOALARM:duration:${rowid}"} eq "Clear")
            {
                $priority = 11;
            }
            $dt->do("UPDATE actions SET duration = %s, priority = %s, sensor_on_or_off = %s, action_on_or_off = %s WHERE rowid = %s",
            $form{"SENSORTOALARM:duration:${rowid}"}, $priority, $sensor_on_or_off, $action_on_or_off, $rowid);
        }
        elsif ( $form{state} =~ /Remove\s*Alert:(\d*)$/ )
        {
            $t->param( alarms_here => "here");
            my $rowid = $1;
            $dt->do("DELETE FROM actions WHERE rowid = %s", $rowid);
            my ($stat, $ah, $al, $port) = $dt->get_rec("SELECT ah, al, port FROM actions WHERE rowid = %s", $rowid);
            #$dt->do("DELETE FROM sensor_activity WHERE ah = %s AND al = %s", $ah, $al);
        }
        elsif ( $form{state} eq "Map Contact" )
        {
            $t->param( contacts_here => "here");
            if ($form{"SENSORTOCONTACT:sensor"})
            {
               my ($addr_high, $addr_low, $port ) = split /\:/, $form{"SENSORTOCONTACT:sensor"};
               if ($form{"SENSORTOCONTACT:contact"})
               {
                  my @contacts = split /\,/, $form{"SENSORTOCONTACT:contact"};
                  foreach my $each_name (@contacts)
                  {
                    my $status = $dt->do(
                      "INSERT OR REPLACE INTO alerts (ah, al, port, contact, threshold_from, threshold_to, last_range_state) VALUES (%s,%s,%s,%s,'0','999', '0')",
                    $addr_high, $addr_low, $port, $each_name);
                  }
                  $EmailQueue->enqueue({cmd => 'refresh', event_time => 0});
               }
            }
        }
        elsif ( $form{state} =~ /Update\s*Contact:(\d*)$/ )
        {
            $t->param( contacts_here => "here");
            my $rowid = $1;
            my $sensor_on_or_off = $form{"SENSORTOCONTACT:sensor_action:${rowid}"};
            $dt->do("UPDATE alerts SET threshold_from = %s, threshold_to = %s, last_date = 0  WHERE rowid = %s",
            $form{"SENSORTOCONTACT:threshold_from:${rowid}"}, $form{"SENSORTOCONTACT:threshold_to:${rowid}"},$rowid);
        }
        elsif ( $form{state} =~ /Remove\s*Contact:(\d*)$/ )
        {
            $t->param( contacts_here => "here");
            my $rowid = $1;
            $dt->do("DELETE FROM alerts WHERE rowid = %s", $rowid);
            $EmailQueue->enqueue({cmd => 'refresh', event_time => 0});
        }
        elsif ( $form{state} eq "Map Camera" )
        {
            $t->param( cameras_here => "here");
            my $date_string = localtime($now);
            if ($form{"SENSORTOCAMERA:sensor"})
            {
               my ($addr_high, $addr_low, $port ) = split /\:/, $form{"SENSORTOCAMERA:sensor"};
               if ($form{"SENSORTOCAMERA:camera"})
               {
                   if ($form{"SENSORTOCAMERA:camera"} =~ /UnMapSensor/)
                   {
                      # remove the old alerts for this contact
                      my $status = $dt->do("DELETE FROM alert_pictures WHERE ah = %s AND al = %s AND port = %s",
                           $addr_high, $addr_low, $port);
                   }
                   else
                   {
                     my @cameras = split /\,/, $form{"SENSORTOCAMERA:camera"};
                     foreach my $each_name (@cameras)
                     {
                        my $status = $dt->do(
                          "INSERT OR REPLACE INTO alert_pictures (ah, al, port, camera_name, repeat_count, repeat_delay) VALUES (%s,%s,%s,%s,0,0)",
                           $addr_high, $addr_low, $port, $each_name);
                     }
                   }
               }
            }
        }
        elsif ( $form{state} =~ /^Update\s*Options\:(\d*)$/ )
        {
            $t->param( cameras_here => "here");
            my $rowid = $1;
            $dt->do("UPDATE alert_pictures SET repeat_count = %s, repeat_delay = %s WHERE rowid = %s",
            $form{"${rowid}:repeat_count"}, $form{"${rowid}:repeat_delay"}, $rowid);
        }
        $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if($WorkerBeeQueue);
    }

    DBG&&$fp->prt("alerts: getting contacts");
    my @contacts_name_only = $dt->tmpl_loop_query(
    "SELECT DISTINCT contact FROM emails ORDER BY contact",
        ( "contact" ));
    $t->param( contacts_name_only => \@contacts_name_only);
    DBG&&$fp->prt("alerts: getting sensors");
    my @sensors = $dt->tmpl_loop_query(<<EOF,(qw (ah al port desc devices_device_types_desc port_types_desc)));
        SELECT wireless_devices.ah, wireless_devices.al, port_types.port,
            coalesce(wireless_devices.physical_location,device_types.desc)||" &rarr; "||coalesce(sensor.location,
            port_types.desc),
            port_types.desc, port_types.desc
            FROM wireless_devices
            JOIN device_types ON wireless_devices.part_nbr =  device_types.part_nbr
            JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
              AND port_types.type = "S"
            LEFT JOIN sensor ON wireless_devices.ah = sensor.ah
              AND wireless_devices.al = sensor.al
              AND port_types.port = sensor.port
            ORDER BY 4
EOF

    $t->param( sensors => \@sensors);
    DBG&&$fp->prt("alerts: getting alarms");

    #devices_device_types_desc port_types_desc device_types.desc, port_types.desc,

    my @alarms = $dt->tmpl_loop_query(<<EOF,(qw (ah al port logic desc devices_device_types_desc port_types_desc devices_rowid)) );
        SELECT wireless_devices.ah, wireless_devices.al, port_types.port, port_types.logic,
            coalesce(wireless_devices.physical_location,device_types.desc)||" &rarr; "||coalesce(devices.port_name,port_types.desc),
            device_types.desc, port_types.desc,
            devices.rowid
            FROM wireless_devices

            JOIN device_types ON wireless_devices.part_nbr =  device_types.part_nbr
            JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
              AND port_types.type = "A"
            JOIN devices ON devices.ah = wireless_devices.ah
              AND devices.al = wireless_devices.al
              AND devices.port = port_types.port
            ORDER BY 5
EOF

    $t->param( alerts => \@alarms);
    my $date_string = localtime($now);
    $t->param( time_now => $date_string);
    DBG&&$fp->prt("alerts: getting mapped_alarms");
    my @mapped_alarms = $dt->tmpl_loop_query(<<EOF,(qw (rowid sensor_desc action_desc duration priority disabled sensor_on_or_off action_on_or_off logic)) );
    SELECT actions.rowid, sensd.desc||"@"||sensw.physical_location||" &rarr; "||sensp.desc,
           alarmd.desc||"@"||alarmw.physical_location||" &rarr; "||alarmp.desc, actions.duration,actions.priority,actions.disabled,
           sensor_on_or_off, action_on_or_off, sensp.logic
    FROM actions
    JOIN wireless_devices AS sensw ON sensw.ah =  actions.ah
         AND sensw.al =  actions.al
    JOIN device_types AS sensd  ON  sensw.part_nbr = sensd.part_nbr
    JOIN port_types AS sensp ON sensp.part_nbr = sensw.part_nbr
        AND sensp.port = actions.port
    JOIN wireless_devices AS alarmw ON alarmw.ah =  actions.device_ah
         AND alarmw.al =  actions.device_al
    JOIN device_types AS alarmd  ON  alarmw.part_nbr = alarmd.part_nbr
    JOIN port_types AS alarmp ON alarmp.part_nbr = alarmw.part_nbr
        AND alarmp.port = actions.device_port
EOF

    foreach my $a (@mapped_alarms)
    {
        if ($a->{sensor_on_or_off} == 1)
        {
            $a->{sensor_on_checked} = "CHECKED";
        }
        else
        {
            $a->{sensor_off_checked} = "CHECKED";
        }
        if ($a->{action_on_or_off} == 1)
        {
            $a->{action_on_checked} = "CHECKED";
        }
        else
        {
            $a->{action_off_checked} = "CHECKED";
        }
        delete $a->{sensor_on_or_off};
        delete $a->{action_on_or_off};
        if (must_follow($a->{logic}))
        {
            $a->{sensor_on_or_off} = 1;
        }
        else
        {
            $a->{momentary} = 1;
        }
        delete $a->{logic};
    }
    $t->param( mapped_alarms => \@mapped_alarms);

    DBG&&$fp->prt("alerts: getting timed alerts");
    my @timed_alerts = $dt->tmpl_loop_query(<<EOF,(qw (rowid desc days starthour startminute stophour stopminute startoffset stopoffset starttype stoptype state)) );
    SELECT timed_events.rowid,
        coalesce(wireless_devices.physical_location,device_types.desc)||" &rarr; "||coalesce(devices.port_name,port_types.desc),
           timed_events.days,
           timed_events.start_hour, timed_events.start_minute, timed_events.stop_hour, timed_events.stop_minute,
           timed_events.start_offset, timed_events.stop_offset, start_type, stop_type, timed_events.state
    FROM timed_events
    JOIN wireless_devices ON wireless_devices.ah =  timed_events.ah
         AND wireless_devices.al =  timed_events.al

    JOIN device_types  ON  wireless_devices.part_nbr = device_types.part_nbr
    JOIN port_types ON port_types.part_nbr = wireless_devices.part_nbr
        AND port_types.port = timed_events.port
    JOIN devices ON devices.ah = wireless_devices.ah
              AND devices.al = wireless_devices.al
              AND devices.port = port_types.port
    ORDER BY wireless_devices.physical_location, timed_events.start_hour, timed_events.start_minute, timed_events.stop_hour
EOF
    foreach my $a (@timed_alerts)
    {
        DBG&&$fp->prt("alert %s",Dumper $a);
        if ($a->{starttype} eq 'Fixed')
        {
            $a->{start} = sprintf ("%02d:%02d", $a->{starthour},$a->{startminute});
        }
        else
        {
            $a->{start} = $a->{starttype};
            if  ($a->{startoffset} > 0)
            {
                $a->{start} = sprintf ("%s minutes after %s", , $a->{startoffset},$a->{starttype});
            }
            elsif ($a->{startoffset} < 0)
            {
                $a->{start} = sprintf ("%s minutes before %s", , $a->{startoffset}*-1,$a->{starttype});
            }
        }
        if ($a->{stoptype} eq 'Fixed')
        {
            $a->{stop} = sprintf ("%02d:%02d", $a->{stophour},$a->{stopminute});
        }
        else
        {
            $a->{stop} = $a->{stoptype};
            if  ($a->{stopoffset} > 0)
            {
                $a->{stop} = sprintf ("%s minutes after %s", , $a->{stopoffset},$a->{stoptype});
            }
            elsif ($a->{stopoffset} < 0)
            {
                $a->{stop} = sprintf ("%s minutes before %s", , $a->{stopoffset}*-1,$a->{stoptype});
            }
        }
        delete $a->{starthour};
        delete $a->{startminute};
        delete $a->{stophour};
        delete $a->{stopminute};
        delete $a->{startoffset};
        delete $a->{stopoffset};
        delete $a->{starttype};
        delete $a->{stoptype};

        $a->{state} = $a->{state}?'ON':'OFF';
        my $alpha_days = "";
        my $day_cnt = 0;
        foreach my $d (split ",", $a->{days})
        {
            if ($d == 0) { $alpha_days .= 'Sun,'; }
            elsif ($d == 1) { $alpha_days .= 'Mon,'; }
            elsif ($d == 2) { $alpha_days .= 'Tue,'; }
            elsif ($d == 3) { $alpha_days .= 'Wed,'; }
            elsif ($d == 4) { $alpha_days .= 'Thu,'; }
            elsif ($d == 5) { $alpha_days .= 'Fri,'; }
            elsif ($d == 6) { $alpha_days .= 'Sat,'; }
            $day_cnt++;
        }
        #if ($day_cnt == 7)
        #{
            #$a->{days} = "Every day"
        #}
        #else
        {
          chop $alpha_days;
          $a->{days} = $alpha_days;
        }
    }
    $t->param( timed_alerts => \@timed_alerts);

    DBG&&$fp->prt("alerts: getting mapped_contacts");
     my @mapped_contacts = $dt->tmpl_loop_query(<<EOF,(qw (rowid sensor_desc contact threshold_from threshold_to last_range_state logic)) );
    SELECT DISTINCT alerts.rowid, sensd.desc||"@"||sensw.physical_location||" &rarr; "||sensp.desc,
           emails.contact, alerts.threshold_from, alerts.threshold_to, alerts.last_range_state, sensp.logic
    FROM alerts
    JOIN wireless_devices AS sensw ON sensw.ah =  alerts.ah
         AND sensw.al =  alerts.al
    JOIN device_types AS sensd  ON  sensw.part_nbr = sensd.part_nbr
    JOIN port_types AS sensp ON sensp.part_nbr = sensw.part_nbr
        AND sensp.port = alerts.port
    JOIN emails ON alerts.contact = emails.contact
EOF
    foreach my $a (@mapped_contacts)
    {
        my $logic = $a->{logic};
        if ($logic eq 'TMP36')
        {
            $a->{variable} = 1;
        }
        #if ($a->{sensor_on_or_off} && $a->{sensor_on_or_off} eq 'ON')
        #{
            #$a->{sensor_on_checked} = "CHECKED";
        #}
        #else
        #{
            #$a->{sensor_off_checked} = "CHECKED";
        #}
        if ($logic =~ /MOMEN/)
        {
            $a->{state} = 'N/A';
        }
        else
        {
            if ($a->{last_range_state})
            {
                $a->{state} = 'In Range';
            }
            else
            {
                $a->{state} = 'Out of range';
            }
        }
        delete $a->{last_range_state};
        delete $a->{logic};
    }
    $t->param( mapped_contacts => \@mapped_contacts);
    if ($cfg->{'dvr_ip'})
    {
        $t->param( have_cameras => 1);
        my $simpleNVRip = $cfg->{'dvr_ip'};
        my $simpleNVRport = $cfg->{'dvr_port'};
        my $list_url = 'http://'.$simpleNVRip.':'.$simpleNVRport.'/list';
        #printf("http list url [%s]\n", $list_url);
        DBG&&$fp->prt("alerts: getting list of cameras");
        my $reply = LWP::Simple::get($list_url);
        if ($reply)
        {
            #print("http got [$reply] from NVR\n");
            my @cameras;
            foreach my $cam (split /,/, $reply)
            {
                my %fld_set;

                $fld_set{"CAMERA"}= $cam;
                push (@cameras, \%fld_set);
            }
            $t->param( cameras_name_only => \@cameras );
        }
        my @mapped_cameras = $dt->tmpl_loop_query(<<EOF,(qw (rowid sensor_desc camera repeat_count repeat_delay)) );
        SELECT DISTINCT alert_pictures.rowid, sensd.desc||"@"||sensw.physical_location||" &rarr; "||sensp.desc,
               alert_pictures.camera_name, repeat_count, repeat_delay
        FROM alert_pictures
        JOIN wireless_devices AS sensw ON sensw.ah =  alert_pictures.ah
             AND sensw.al =  alert_pictures.al
        JOIN device_types AS sensd  ON  sensw.part_nbr = sensd.part_nbr
        JOIN port_types AS sensp ON sensp.part_nbr = sensw.part_nbr
            AND sensp.port = alert_pictures.port
EOF
        $t->param( mapped_cameras => \@mapped_cameras);
    }
   return $t;
}

sub config
{
    my ($dt, $now, $main_pid, $WorkerBeeQueue, $XbeeSendQueue, $Watchdog, %form) = @_;
    my $passmsg;
    my $t = HTML::Template->new_scalar_ref( html::configuration(),
            ( xdebug => 1, xstack_debug => 1 ) );

    my $prior_cfg;
    #printf "http_processor:config: %s\n", Dumper \%form;
    if ($form{state})
    {
            $prior_cfg = tools::get_config($dt,FRESH_READ);
            if ( $form{state} eq "Update" || $form{state} eq "Reboot")
            {

                my $sql = <<EOF;
                UPDATE config SET primary_contact = %s, problem_reporting_frequency = %s, connection_type = %s,
                external_http_port = %s, static_ip = %s, subnet_mask = %s, gateway = %s, dns1 = %s, dns2 = %s, metric_units = %s, ident = %s,
                dvr_ip = %s, dvr_port = %s, dvr_user = %s, dvr_password = %s, wemo_port_base = %s
EOF
                my $status = $dt->do($sql,
                    $form{"CONFIG:contact"}, $dt->trim($form{"CONFIG:freq"}),  $dt->trim($form{"CONFIG:contype"}),  $dt->trim($form{"CONFIG:port"}),
                    $dt->trim($form{"CONFIG:ip"}), $dt->trim($form{"CONFIG:mask"}),  $dt->trim($form{"CONFIG:gw"}), $dt->trim($form{"CONFIG:dns1"}),
                    $dt->trim($form{"CONFIG:dns2"}),$form{"CONFIG:metric_units"}||"no", $form{"CONFIG:ident"},
                    $dt->trim($form{"CONFIG:zmip"}), $dt->trim($form{"CONFIG:zmport"}), $dt->trim($form{"CONFIG:zmuser"}), 
                    $dt->trim($form{"CONFIG:zmpass"}), $dt->trim($form{"CONFIG:wemo"}));

                DBG&&$fp->prt("status $status %s",$form{"CONFIG:ident"});
                tools::create_htpasswd($dt);
                if ($form{"CONFIG:password"})
                {
                    $dt->do("UPDATE config SET password = %s", $form{"CONFIG:password"});
                    #if ($form{"CONFIG:password"} ne $form{"CONFIG:password_again"})
                    #{
                        #$passmsg = "Passwords do not match";
                    #}
                    #else
                    #{
                         #my $digest = Crypt::Password::password($form{'CONFIG:password'});
                         #$dt->do("UPDATE config SET password = %s", $digest);
                         #DBG&&$fp->prt("digest [%s]", $digest);
                         #$passmsg = "Password set";
                    #}
                }
                if ($WorkerBeeQueue)
                {
                    $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"});
                    if  ( $form{state} eq "Reboot")
                    {
                       DBG&&$fp->prt("reboot requested");
                       $WorkerBeeQueue->enqueue({request => 'REASON_STARTED', code => 4, descr => "User requested reboot"});
                       $WorkerBeeQueue->enqueue({request => "LOG", fmt => "User requested reboot"});
                       $WorkerBeeQueue->enqueue({request => "BACKUP_NOW"});
                       $Watchdog->enqueue({request => 'Reboot'});
                       $message .= "sent reboot request";
                       #if ($main_pid)
                       #{
                          #kill(POSIX::SIGUSR1, $main_pid);   # causes shutdown to be run in parent process
                           #$message .= "killing main process $main_pid for reboot";
                       #}
                       #else
                       #{
                           #$message .= "Not killing main process for reboot";
                       #}
                    }

                }
            }
            elsif ($XbeeSendQueue)
            {
                if( $form{state} eq "Trace on")
                {
                    $WorkerBeeQueue->enqueue({request => 'TRACE_ON'});
                }
                elsif( $form{state} eq "Trace off")
                {
                    $WorkerBeeQueue->enqueue({request => 'TRACE_OFF'});
                }
                elsif  ($form{state} eq "Get Coordinator" && $XbeeSendQueue)
                {
                    DBG&&$fp->prt("Get Coordinator");
                    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'OP'}); # operating 64 bit id
                    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'OI'}); # operating 16 bit id
                    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'CH'}); # operating channel
                    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'ZS'}); # stack profile
                }
                elsif  ($form{state} eq "Set Coordinator")
                {
                    tools::set_coordinator_configuration($XbeeSendQueue,
                           $prior_cfg->{pan_id_64}, $prior_cfg->{pan_id_16},
                           $prior_cfg->{operating_channel}, $prior_cfg->{stack_profile});


                    #my $pan_id_64 = pack( 'Q>',  int $prior_cfg->{pan_id_64});
                    #$XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'ID', value => $pan_id_64});

                    #$dt->do("update config set pan_id = %s", $prior_cfg->{pan_id_64});
                    ## set the mask to current operating_channel
                    #my $mask = 1 << ($prior_cfg->{operating_channel} - 0xb);
                    #my $operating_channel = pack( 'n',  $mask);
                    #$XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'SC', value => $operating_channel});

                    #my $stack_profile = pack( 'n',  int $prior_cfg->{stack_profile});
                    #$XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'ZS', value => $stack_profile});
                    #$XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'WR'});

                    #my $pan_id_16 = pack( 'n',  int $prior_cfg->{pan_id_16});
                    #$XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'II', value => $pan_id_16});
                    # $dt->do("update config set pan_id_16 = 0, pan_id_64 = 0, operating_channel = 0, stack_profile = 0");
                }
            }
     }
    if ($WorkerBeeQueue)
    {
        $t->param(display_reboot => 1);
    }
    my $cfg = tools::get_config($dt,FRESH_READ);

    my $curripmsg   = check_ip_address($cfg->{static_ip});
    my $currmaskmsg = check_ip_address($cfg->{subnet_mask});
    my $currgwmsg   = check_ip_address($cfg->{gateway});
    my $currdns1msg = check_ip_address($cfg->{dns1});
    my $currdns2msg = check_ip_address($cfg->{dns2});
    #if (!$passmsg)
    #{
        #if ($cfg->{password})
        #{
            #$passmsg = "Password on file";
        #}
        #else
        #{
            #$passmsg = "No password on file";
        #}
    #}
    #$t->param( passmsg => $passmsg);

    my $needed_connection_type = $cfg->{connection_type};
    my $is_good_static = 1;
    if (($curripmsg||$currmaskmsg||$currgwmsg||$currdns1msg||$currdns2msg||$curripmsg) # one or more are bad so cannot use them to set a static IP address
        ||
        ($dt->trim($cfg->{static_ip})   eq ""  ||
           $dt->trim($cfg->{subnet_mask}) eq ""  ||
           $dt->trim($cfg->{gateway})     eq ""  ||
           $dt->trim($cfg->{dns1})        eq ""))
    {
        $is_good_static = 0;
        $needed_connection_type = "DHCP";   # will not work as static
    }

    if ($cfg->{connection_type} ne $needed_connection_type)
    {
        $cfg->{connection_type} = $needed_connection_type;
        $dt->do("UPDATE config SET connection_type = %s", $needed_connection_type);
        $message .= "No vaild static IP information, DHCP rules inforced";
    }

    # now we need to check and see if we should attempt to change the network connection
    if ($prior_cfg)  # we did a update, something could have changed
    {
        if ($cfg->{connection_type} eq $prior_cfg->{connection_type} && $cfg->{connection_type} eq 'DHCP') # no change in type
        {
             # fine leave things alone, nothing to do
        }
        elsif ($cfg->{connection_type} eq 'DHCP')  # looks like we have changed from static to DHCP, pretty safe
        {
            ip_tools::set_ip($dt); # ok change it to DHCP, about as safe as it gets
        }
        elsif ($is_good_static == 1)  # we have a static IP passed muster
        {
           # print Dumper $prior_cfg;
           # now before we apply this new address we should save away the working address
           # first check to see if anything changed
           if ( $prior_cfg->{connection_type} eq  $cfg->{connection_type} &&
                $prior_cfg->{dns1} eq  $cfg->{dns1} &&
                $prior_cfg->{dns2} eq  $cfg->{dns2} &&
                $prior_cfg->{static_ip} eq  $cfg->{static_ip} &&
                $prior_cfg->{subnet_mask} eq  $cfg->{subnet_mask} &&
                $prior_cfg->{gateway} eq  $cfg->{gateway})
           {
               # they are the same, ok do nothing
           }
           else # different, so save, apply and test
           {
               my $status = $dt->do(<<EOF, $prior_cfg->{connection_type},$prior_cfg->{external_http_port},$prior_cfg->{static_ip},$prior_cfg->{subnet_mask},$prior_cfg->{gateway},$prior_cfg->{dns1},$prior_cfg->{dns2});
               UPDATE config SET lw_connection_type = %s, lw_external_http_port = %s, lw_static_ip = %s,
                      lw_subnet_mask = %s, lw_gateway = %s, lw_dns1 = %s, lw_dns2 = %s
EOF
               # now we can can change the connection and test to see if it worked
               my $fell_back = ip_tools::set_ip($dt); # ok change it,
               if ($fell_back == 1) # does not look like the address is very good
               {
                   $message .= "This set of static IP address information does not work, reverted to prior values";
               }
               else
               {
                   DBG&&$fp->prt("new address worked");
                   # it worked so, make it the (lw) last working
                   $dt->do(<<EOF);
                   UPDATE config
                   SET lw_connection_type = connection_type,
                       lw_external_http_port = external_http_port,
                       lw_static_ip = static_ip,
                       lw_subnet_mask = subnet_mask,
                       lw_gateway = gateway,
                       lw_dns1 = dns1,
                       lw_dns2 = dns2
EOF

               }
           }
        }
      }
    $cfg = tools::get_config($dt,FRESH_READ);
    DBG&&$fp->prt("http_processor::config: fresh read %s", Dumper $cfg);
    $t->param( curripmsg   => $curripmsg);
    $t->param( currmaskmsg => $currmaskmsg);
    $t->param( currgwmsg   => $currgwmsg);
    $t->param( currdns1msg => $currdns1msg);
    $t->param( currdns2msg => $currdns2msg);

    $t->param( currident   => $cfg->{ident});
    $t->param( password    => $cfg->{password});
    $t->param( currprimary => $cfg->{primary_contact});
    $t->param( currfreq    => $cfg->{problem_reporting_frequency} );
    $t->param( currwemo    => $cfg->{wemo_port_base} );
    $t->param( currcontype => $cfg->{connection_type});
    $t->param( currport    => $cfg->{external_http_port} );
    $t->param( currip      => $cfg->{static_ip});
    $t->param( currmask    => $cfg->{subnet_mask});
    $t->param( currgw      => $cfg->{gateway});
    $t->param( currdns1    => $cfg->{dns1});
    $t->param( currdns2    => $cfg->{dns2});
    $t->param( dvrip    => $cfg->{dvr_ip});
    $t->param( dvrport  => $cfg->{dvr_port});
    $t->param( dvruser  => $cfg->{dvr_user});
    $t->param( dvrpass  => $cfg->{dvr_password});
    $t->param( currunits   => $cfg->{metric_units});
    $t->param( currpid64   => sprintf "0x%0X", $cfg->{pan_id_64}||0);
    $t->param( currpid16   =>  sprintf "0x%0X", $cfg->{pan_id_16}||0);
    $t->param( curroperch   =>  sprintf "0x%0X", $cfg->{operating_channel}||0);
    $t->param( currstackpro   =>  sprintf "0x%0X", $cfg->{stack_profile}||0);
    my @contacts = $dt->tmpl_loop_query(
    "SELECT contact, email_address FROM emails ORDER BY 1,2",
        (  "contact", "email" ));
    $t->param( contacts => \@contacts );

   #printf "http_processor::conf: html form  returned %s\n", Dumper $t;
   return ($t,"Update");
}

sub commission
{
    my ($dt, $XbeeSendQueue) = @_;
    DBG&&$fp->prt("sending");
    http_processor::permit_join($dt, $XbeeSendQueue);  # testing with out the 1 , 1); # the 1 causes only CB2 to be sent to routers
    $XbeeSendQueue->enqueue({request => 'HA_ENDPOINTS', ah => 0xffffffff, al => 0xffffffff, na => 0xffff});  # for HA devices

    #$message .= "Commissioning permision being sent";
    #return main_page($dt, $XbeeSendQueue);
}

# extern accepts commands from external events like wemo
sub extern
{
    my ($dt, $now, $WorkerBeeQueue, $XbeeSendQueue, $EmailQueue, $EvaluateQueue, %form) = @_;
    #my $t = HTML::Template->new_scalar_ref( html::extern(),
    #        ( xdebug => 1, xstack_debug => 1 ) );
    $fp->prt("name[%s] action[%s]", $form{name}, $form{action});
    my $result = 'OK';
    if ($form{name} eq "status")
    {
        DBG&&$fp->prt("email status to default user");
        email::email_daily_status($dt, $WorkerBeeQueue, $EmailQueue, "Alexa sent you status","This has been sent beacuse you asked Alexa to turn on status");
    }
    elsif ($form{name} eq "commission")
    {
        DBG&&$fp->prt("commission"); # zigbee commision
        http_processor::permit_join($dt, $XbeeSendQueue); # testing without the 1 , 1); # the 1 causes only CB2 to be sent to routers
    }
    else # normal extern commands like WeMo
    {
        use constant ONLY_WEMO => 1;
        extern::do_extern_device ($dt, $form{location}, $form{device}, $form{action}, ONLY_WEMO, $EvaluateQueue, $XbeeSendQueue); # 1 means screened for wemo
    }
    return $result;
}



sub location
{
    my ($dt, $now, %form) = @_;
    my $t = HTML::Template->new_scalar_ref( html::location(),
            ( xdebug => 1, xstack_debug => 1 ) );
    my $cfg = tools::get_config($dt,FRESH_READ);
    my $tz = $cfg->{timezone};
    if ($form{state} )
    {

        if ($form{state} eq "Set Timezone" )
        {
            $tz = $form{timezone};
            my $rc = $dt->do("UPDATE config SET timezone = %s", $tz);
            my $cmd = "sudo ".cfg::TIMEDATECTL." --no-ask-password --no-pager set-timezone  ".$tz."";
            DBG&&$fp->prt("%s", $cmd);
            #system(cfg::TIMEDATECTL,"--no-ask-password","set-timezone",$tz);
            my $trash = `$cmd`;
        }
        elsif ($form{state} eq "Set Geo Location")
        {
            DBG&&$fp->prt("setting geo %s:%s", $form{latitude}, $form{longitude});
            my $rc = $dt->do("UPDATE config SET latitude = %s, longitude = %s", $form{latitude}, $form{longitude});
        }
    }
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
    my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
    $cfg = tools::get_config($dt,FRESH_READ);
    my ($sunrise_hour, $sunrise_minute, $sunset_hour, $sunset_minute) =  tools::sunRiseSet($cfg->{latitude}||0,$cfg->{longitude}||0);
    my $riseSet = sprintf("Sunrise: %02d:%02d Sunset %02d:%02d", $sunrise_hour, $sunrise_minute, $sunset_hour, $sunset_minute);
    $t->param( month =>  $abbr[$mon]);
    $t->param( day =>  sprintf("%02d",$mday));
    $t->param( year =>  $year + 1900);
    $t->param( hour =>  sprintf("%02d",$hour));
    $t->param( minute =>  sprintf("%02d",$min));
    $t->param( timezone =>  $tz);
    $t->param( latitude =>  $cfg->{latitude});
    $t->param( longitude =>  $cfg->{longitude});
    $t->param( riseset => $riseSet);
    my @zones;
    my $get_zones = cfg::TIMEDATECTL." list-timezones";
    foreach my $zone (split "\n", `$get_zones`)
    {
         #print "[$zone]\n";
         my %rowdata;
         $rowdata{loc} = $zone;
         push(@zones, \%rowdata)
    }
    $t->param(zones =>  \@zones);
    return $t;
}

sub xtimezone
{
    my ($dt, $now, $WorkerBeeQueue, %form) = @_;
    my $t = HTML::Template->new_scalar_ref( html::timezone(),
            ( xdebug => 1, xstack_debug => 1 ) );
    if ($form{state} )
    {
        if ($form{state} eq "Set Time Zone" )
        {
           $dt->do("UPDATE config SET timezone = %s", $form{timezone});
        }
        $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if($WorkerBeeQueue);
    }
    my $cfg = tools::get_config($dt,FRESH_READ);
    my $offset = $cfg->{timezone} * 3600;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmt(time + $offset);
    my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );

    $t->param( timezone =>  $cfg->{timezone});
    return $t;
}

sub contacts
{
    my ($dt, $now, $WorkerBeeQueue, %form) = @_;
    my $t = HTML::Template->new_scalar_ref(html::contacts(), (xdebug => 1, xstack_debug => 1 ));
    if ($form{state} )
    {
        if ($form{state} eq "Add contact")
        {
            if ($form{"ADDCONTACT:contact"} && $form{"ADDCONTACT:email"})
            {
               my $email = $dt->trim($form{"ADDCONTACT:email"});
               if ($email  =~ /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i)
               {
                  my $status = $dt->do(
                    <<EOF, $dt->trim($form{"ADDCONTACT:contact"}), $email, $form{"ADDCONTACT:short"} );
                   INSERT OR REPLACE INTO emails (contact, email_address, requires_short_messages) VALUES (%s, %s, %s)
EOF
               }
               else
               {
                   $t->param(msg => "Invalid email address");
                   $t->param(addemail => $email);
                   $t->param(addcontact => $form{"ADDCONTACT:contact"});
               }
            }
            else
            {
               $t->param(msg => "Both fields need to be entered");
               $t->param(addemail => $form{"ADDCONTACT:email"});
               $t->param(addcontact => $form{"ADDCONTACT:contact"});
           }
        }
        elsif ( $form{state} =~ /^Remove contact\s*(\d*)/ )
        {
            my $rowid = $1;
            my ( $status, $contact, $email, $short ) = $dt->get_rec(
                 "select contact, email_address, requires_short_messages from emails where rowid = %s",
                   $rowid
            );
            $t->param( addcontact => $contact );
            $t->param( addemail   => $email );
            $t->param( addshort   => $short );
            $dt->do( "delete from emails where rowid =  %s", $rowid );
        }
        $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if($WorkerBeeQueue);
    }
    my @contacts = $dt->tmpl_loop_query(
    "SELECT rowid, contact, email_address, requires_short_messages FROM emails ORDER BY contact",
        ( "rowid", "contact", "email", "short" ));
    $t->param( contacts => \@contacts );
    return $t;
}

#sub trace_info
#{
    #my ($dt, $now, %form) = @_;
    #my $t = HTML::Template->new_scalar_ref(html::trace_list(), (xdebug => 1, xstack_debug => 1 ));

    #my $smallest;
    #my $where="";
    #my $delem = ':';
    #my $curr_ss_filter = "all";
    #if ($form{state})
    #{
        #if ($form{state} eq "More")
        #{
           #my $start_here = $form{"start_at"}  + 1;
           #$where = "WHERE trace_parms.seq < $start_here";
           #$curr_ss_filter = $form{"subsystem_filter"};
        #}
        #elsif ($form{state} eq "Clear")
        #{
            #$dt->do("DELETE FROM trace_parms");
        #}
    #}
    #my $second_where = "";
    #if  ($curr_ss_filter ne "all")
    #{
        #if ($where eq "")
        #{
             #$second_where = "WHERE ";
         #}
         #else
         #{
             #$second_where = " AND ";
         #}
         #$second_where .= "trace_name.name = '$curr_ss_filter'";
    #}

    #my @sub_systems = $dt->tmpl_loop_query(<<EOF, (qw(name)));
#select trace_name.name
#from trace_name
#ORDER BY trace_name.name
#EOF
    #push @sub_systems, {name => "all"};
    #$t->param(sub_systems => \@sub_systems );

    #my @items =  $dt->tmpl_loop_query(<<EOF, (qw(seq name fmt parms)));
#select trace_parms.seq, trace_name.name, trace_fmt.fmt, trace_parms.parms
#from trace_parms
#join trace_name on trace_name.name_key = trace_parms.name_key
#join trace_fmt on trace_fmt.fmt_key = trace_parms.fmt_key
#$where
#$second_where
#ORDER BY trace_parms.seq DESC
#LIMIT 100
#EOF

    #foreach my $r (@items)
    #{
        #my @parms = ();
        #if ($r->{parms})
        #{
            #@parms = split $delem, $r->{parms};
        #}
        #$r->{msg} = sprintf "\t".$r->{fmt}."\n", @parms,"","","","","";
        #delete $r->{parms};
        #delete $r->{fmt};
        #$smallest=$r->{seq};
    #}
    #$t->param(curr_ss_filter => $curr_ss_filter);
    #$t->param(start_at => $smallest);
    #$t->param( items => \@items );
    #return $t;
#}


sub system_info
{
    my ($dt, $now, $WorkerBeeQueue, %form) = @_;
    my $config = tools::get_config($dt,FRESH_READ);
    my $t = HTML::Template->new_scalar_ref( html::systems_info(),
            ( xdebug => 1, xstack_debug => 1 ) );
            my ($restart_code, $restart_descr) = tools::get_restart_reason($dt);
    $t->param(restart_descr => $restart_descr);
    $t->param(restart_code => $restart_code);
    $t->param(run_time => tools::how_long($now, $config->{process_start_time})); #decimal hours
    $t->param(sysid => tools::system_string($config->{pan_id}, $config->{ident}, 1));
    $t->param(version => $config->{version_number});
    $t->param(server_version => $config->{server_version});
    my ($stat, $version) = $dt->get_rec('SELECT sqlite_version()');
    $t->param(sqlite => $version);

    #my $motion = df('/motion');
    my $total = df('/');

    my $text .= sprintf "STORAGE\nTotal free %d.2 Gb\nUPTIME load averages for 1,5,15 minutes\n%s", $total->{bfree} / 1000000 , `uptime`;

    my $pid_lines="Process info:\n";
    my @processes = $dt->tmpl_loop_query("select name, pid from processes order by pid", ("name", "pid"));
    foreach my $p (@processes)
    {
        my $ps;

        $ps= sprintf "ps --pid %s h  o vsz", $p->{pid};

        my $ps_result = `$ps`;
        $ps_result =~ /\s*(\d+)/;
        my $memory = $1;
        $memory = sprintf "%.1f", $memory / 1024;
        $pid_lines .= sprintf "%s\(%s) = %s Mb\n", $p->{name}, $p->{pid}, $memory;
    }
    #`free -m` =~ /\nMem:\s*(\d*)\s*.*\n.*cache\:\s*(\d*)\s*/;

    my $meminfo = `cat /proc/meminfo`;
    $meminfo =~ /MemTotal\:\s*(\d*)/;
    my $total_memory = sprintf "%d.2", $1/1000;
    $meminfo =~ /MemAvailable\:\s*(\d*)/;
    my $mem_avail = sprintf "%d.2", $1/1000;
    my $in_use_memory = sprintf "%d.2", $total_memory - $mem_avail;

    $t->param(text => "MEMORY (in Mb) total = $total_memory in_use = $in_use_memory\n".$pid_lines.$text);
    system_load::get($t);
    return $t;
}

sub main_page
{
    my ($dt, $now, $XbeeSendQueue, $WorkerBeeQueue,  $Watchdog, %form) = @_;
    #DBG&&$fp->prt("main_page: form = %s", Dumper \%form);
    my $config = tools::get_config($dt,FRESH_READ);
    my $t = HTML::Template->new_scalar_ref( html::main_page(),
            ( xdebug => 1, xstack_debug => 1 ) );
    #printf "http_processor::main_page: %s\n", Dumper \%form;
    if ($form{state})
    {
        # print $form{state}."\n";
        if ($form{state} eq 'Clear log')
        {
            ## print 'clearing the log\n';
            $dt->do('delete from errors');
        }
        elsif ($form{state} eq 'Commission ON' )
        {
            http_processor::permit_join($dt, $XbeeSendQueue, 1);
            $message .= "Commission ON sent";
        }
        elsif ($form{state} eq 'Commission OFF' )
        {
            http_processor::permit_join($dt, $XbeeSendQueue, 0);
            $message .= "Commission OFF sent";
        }
        elsif ($form{state} eq 'Broadcast Node Discovery' )
        {
            $XbeeSendQueue->enqueue({request => 'BROADCAST_NODE_DISCOVERY'});
            $message .= "BROADCAST NODE DISCOVERY sent";
        }
        elsif ($form{state} eq 'Refresh' && $XbeeSendQueue)
        {
            route_collection::clean($dt);
            route_collection::get($dt,$XbeeSendQueue);
        }
        elsif ($form{state} =~ /^Remove\s*(\d*)/ )
        {
            my $rowid = $1;
            # ok clean out all for this one
            my ($status, $ah, $al, $loc) = $dt->get_rec("SELECT ah, al, physical_location FROM wireless_devices WHERE rowid = %s", $rowid);
            if ($status == 1)
            {
               delete_device($dt, $ah, $al);
            }
            else
            {
                DBG&&$fp->prt("remove failed for rowd[%s]", $rowid);
            }
        }
        elsif ($form{state} eq 'Update' )
        {
            my $need_fauxmo_restart = 0;
            my $have_some_faxmo = 0;
            my $got_port_name_rowid = 0;
            my $got_location_rowid = 0;
            my $port_name = "";
            my $location = "";
            #DBG&&$fp->prt("main_page:update: form = %s", Dumper \%form);
            foreach my $key ( keys %form )
            {
                #DBG&&$fp->prt("key before [%s]",$key);
                my ($rowid, $field) = split /\:/, $key;
                DBG&&$fp->prt("split [%s][%s]",$rowid, $field);
                if ($rowid && $field)
                {
                   #DBG&&$fp->prt("UPDATE >  %s:%s [%s]", $rowid, $field, $form{$key});
                   my $value = $form{$key};

                    if ($field eq "loc")
                    {
                        my ($status, $trash) = $dt->get_rec(<<EOF,$rowid, $value);
                        SELECT physical_location FROM wireless_devices
                        WHERE rowid = %s
                        AND coalesce(physical_location,'') = %s
EOF
                        DBG&&$fp->prt("Loc: check for change [%d][%s]", $status, $value);
                        if ($status == 0)  # it changed, so make sure that it's moved device(s) have unique name under the other locations
                        {
                            # look at all this locs current children and see if they are the same as any of the "new" locations children
                            ($status,my $cnt) = $dt->get_rec(<<EOF, $rowid, $rowid, $value);
                                SELECT count()
                                FROM wireless_devices
                                JOIN devices ON wireless_devices.al = devices.al AND wireless_devices.ah = devices.ah
                                WHERE wireless_devices.rowid == %s
                                AND (devices.port_name NOT NULL OR devices.port_name != "")
                                AND devices.port_name IN
                                    (SELECT devices.port_name
                                    FROM wireless_devices
                                    JOIN devices ON wireless_devices.al = devices.al AND wireless_devices.ah = devices.ah
                                    WHERE wireless_devices.rowid <> %s
                                    AND wireless_devices.physical_location = %s)
EOF

                            DBG&&$fp->prt("cnt [%s]", $cnt);
                            if ($cnt) # too bad :( found one
                            {
                                $message = "ERROR: New location [$value] has a device of the same name";
                            }
                            else # ok, all is well
                            {
                                $dt->do("UPDATE wireless_devices SET physical_location = %s WHERE rowid = %s", $value, $rowid);
                                $need_fauxmo_restart++;
                            }
                        }
                    }
                    elsif ($field eq "port_name")
                    {
                        my ($status, $trash) = $dt->get_rec(<<EOF, $rowid, $value);
                        SELECT port_name
                        FROM devices
                        WHERE rowid = %s
                        AND coalesce(port_name,'') = %s
EOF
                        DBG&&$fp->prt("port_name: check for change [%d][%s]", $status, $value);
                        if ($status == 0)  # looks like the device changed so let see if it is unique within this location
                        {
                            my ($status, $cnt) = $dt->get_rec(<<EOF,  $rowid, $rowid, $value);
                                SELECT count()
                                FROM devices
                                JOIN wireless_devices ON wireless_devices.al = devices.al AND wireless_devices.ah = devices.ah
                                WHERE devices.rowid == %s
                                AND coalesce(wireless_devices.physical_location,"x") IN
                                    (SELECT coalesce(wireless_devices.physical_location, "x")
                                    FROM wireless_devices
                                    JOIN devices ON wireless_devices.al = devices.al AND wireless_devices.ah = devices.ah
                                    WHERE devices.rowid <> %s
                                    AND devices.port_name = %s)
EOF

                            if ($cnt) # this would cause a dup
                            {
                                $message .= "ERROR combination of device name and location and must be unique";
                            }
                            else
                            {
                                $dt->do("UPDATE devices SET port_name = %s WHERE rowid = %s", $form{$key}, $rowid);
                                $need_fauxmo_restart++;
                            }
                        }
                    }
                   #if ($field eq 'trace')
                   #{
                       #my $val = checked_value($form{$key});
                       #DBG&&$fp->prt("trace [%s]", $val);
                       #$dt->do('UPDATE wireless_devices set trace = %s WHERE rowid = %s', $val, $rowid);
                   #}
                    elsif ($field eq 'allow_wemo')
                    {
                        my ($status, $allow_wemo) = $dt->get_rec(<<EOF, $rowid);
                       SELECT coalesce(allow_wemo,"") FROM devices
                        WHERE devices.rowid = %s
EOF
                        my $val = checked_value($form{$key});
                        DBG&&$fp->prt("test allow_wemo current[%s] new[%s]", $allow_wemo||"", $val);
                        $have_some_faxmo++ if ($val eq 'checked' || $allow_wemo  eq 'checked');
                        if  ($allow_wemo ne $val)
                        {
                            DBG&&$fp->prt("updating allow_wemo");
                            $dt->do("UPDATE devices SET allow_wemo = %s WHERE rowid = %s", $val, $rowid);
                            $need_fauxmo_restart++;
                        }
                    }
                    elsif ($field eq 'invert_wemo' )
                    {
                       my ($status, $invert_wemo) = $dt->get_rec(<<EOF, $rowid);
                       SELECT coalesce(invert_wemo,"") FROM devices
                        WHERE devices.rowid = %s
EOF
                        my $val = checked_value($form{$key});
                        DBG&&$fp->prt("test invert_wemo [%s][%s]", $invert_wemo||"", $val);
                        if  ($invert_wemo ne $val)
                        {
                            DBG&&$fp->prt("updating invert_wemo");
                            $dt->do("UPDATE devices SET invert_wemo = %s WHERE rowid = %s", $val, $rowid);
                            $need_fauxmo_restart++;
                        }
                    }
                    elsif ($field eq "adj")
                    {
                       my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                       UPDATE sensor
                          SET adjustment = %s
                          WHERE rowid = %s
EOF
                    }
                    elsif ($field eq "high")
                    {
                       my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                       UPDATE sensor
                          SET alarm_value_high = %s
                          WHERE rowid = %s
EOF
                    }
                    elsif ($field eq "low")
                    {
                       my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                       UPDATE sensor
                          SET alarm_value_low = %s
                          WHERE rowid = %s
EOF
                    }
                    elsif ($field eq "sensor_desc")
                    {
                        my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                        UPDATE sensor
                            SET location = %s
                            WHERE rowid = %s
EOF
                    }
                   elsif ($field eq "override_state")
                   {
                        my ($s, $ah, $al, $na, $port, $device_type, $invert_wemo, $endpoint, $profile_id, $override_state, $new_override) = $dt->get_rec(<<EOF, $rowid);
                         SELECT devices.ah, devices.al, wireless_devices.na, devices.port, device_types.part_type,
                         coalesce(devices.invert_wemo,''), wireless_devices.endpoint, wireless_devices.profile_id, coalesce(override_state,-1), external_override
                           FROM devices
                           JOIN wireless_devices
                           ON wireless_devices.ah = devices.ah
                            AND wireless_devices.al = devices.al
                           JOIN device_types
                                ON device_types.part_nbr = wireless_devices.part_nbr
                           WHERE devices.rowid = %s
EOF
                        my $new_override = $dt->trim($form{$key});
                        next if ($override_state == $new_override);
                        if ($new_override == -1) ## no override
                        {
                            tools::remove_override($dt, $rowid);
                        }
                        else
                        {
                            my $status = $dt->do("update devices set override_state = %s,  external_override = null where rowid = %s", $new_override, $rowid);
                        }
                        $XbeeSendQueue->enqueue({request => 'FORCE_SAMPLE', ah => $ah, al => $al, na => $na, port => $port, device_type => $device_type, endpoint => $endpoint, profile_id => $profile_id });
                    }
                    elsif ($field eq "default_state")
                    {
                        my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                        UPDATE devices
                            SET default_state = %s
                            WHERE rowid = %s
EOF
                    }
                    my ($restart_code, $restart_descr) = tools::get_restart_reason($dt);
                    $t->param(restart_descr => $restart_descr);
                    $t->param(restart_code => $restart_code);
                    $t->param(run_time => tools::how_long($now, $config->{process_start_time})); #decimal hours
                    $t->param(sysid => tools::system_string($config->{pan_id}, $config->{ident}, 1));
                    $t->param(version => $config->{version_number});
                    #$t->param(server_version => $config->{server_version});
                }
            }
            DBG&&$fp->prt("Done with fields");
            if ($have_some_faxmo && $need_fauxmo_restart)
            {
                DBG&&$fp->prt("doing fauxmo restart ");
                $Watchdog->enqueue({request => 'restart_process', process => 'fauxmo_manager'}) if ($Watchdog);
            }
        }
        $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if ($WorkerBeeQueue);
    }

    my ($one_or_more_missing, @wireless_devices) = get_devices_status($dt, $now, 0);
    my ($restart_code, $restart_descr) = tools::get_restart_reason($dt);
    $t->param(restart_descr => $restart_descr);
    $t->param(restart_code => $restart_code);
    #printf "------------------  config start time? %s\n",  $config->{process_start_time};
    $t->param(run_time => tools::how_long($now, $config->{process_start_time})); #decimal hours
    $t->param(sysid => tools::system_string($config->{pan_id}, $config->{ident}, 1));
    $t->param(version => $config->{version_number});
    $t->param( wireless_devices => \@wireless_devices );
    # my @error_log = $dt->tmpl_loop_query("SELECT datetime(time,'unixepoch'), message FROM errors ORDER BY id DESC",(qw (time message)) );
    my @error_log = $dt->tmpl_loop_query("SELECT datetime(time,'unixepoch','localtime'), message FROM errors ORDER BY id DESC",(qw (time message)) );
    $t->param( error_log => \@error_log);
    return ($t,"Update");
}

#sub debug
#{
    #my ($dt, $WorkerBeeQueue, %form) = @_;
    #my $config = tools::get_config($dt,FRESH_READ);
    #my $t = HTML::Template->new_scalar_ref( html::debug(),
            #( xdebug => 1, xstack_debug => 1 ) );
    #DBG&&$fp->prt("%s", Dumper \%form);
    #if ($form{state})
    #{
        #foreach my $key ( keys %form )
        #{
            #my ($rowid, $field) = split /\:/, $key;

            #if ($rowid && $field)
            #{
               #DBG&&$fp->prt("%s:%s [%s]", $rowid, $field, $form{$key});

               #if ($field eq 'trace')
               #{
                   #my $val = checked_value($form{$key});
                   #DBG&&$fp->prt("trace [%s]", $val);
                   #$dt->do('UPDATE wireless_devices set trace = %s WHERE rowid = %s', $val, $rowid);
               #}
             #}
         #}
         ##if( $form{state} eq "Trace on")
         ##{
            ##$WorkerBeeQueue->enqueue({request => 'TRACE_ON'});
         ##}
         ##elsif( $form{state} eq "Trace off")
         ##{
            ##$WorkerBeeQueue->enqueue({request => 'TRACE_OFF'});
         ##}
     #}

    #my (@wireless_devices) = get_debug_status($dt);
    #$t->param( wireless_devices => \@wireless_devices );
    #return ($t,"Update");
#}

sub checked_value
{
    my ($text) = @_;
    return 'checked' if ($text =~ /checked/);
    return '';
}


sub get_devices_status
{
    my ($dt, $now, $short_version) = @_;
    my $one_or_more_missing = 0;
    my $filter = '';
    if ($short_version)
    {
        $filter = 'WHERE port_types.type = "S" OR port_types.logic = "BINARY" OR port_types.logic = "VALVE"';
    }
    my $metric_units = tools::get_config($dt,FRESH_READ)->{metric_units};
    my @fields = qw( drowid port_desc srowid ah al na trace physical_location parent_network_address adjustment alarm_low alarm_high
    value current part_desc allowed_time_away part_nbr last_time_in previous_time_in logic port default_state override_state external_override db_level parent_db_level router
    parent_part_desc port_type problem_time allow_wemo invert_wemo port_name);

    my @wireless_devices = $dt->tmpl_loop_query(
        <<EOF, @fields);
        SELECT  wireless_devices.rowid,
        coalesce(port_types.desc, device_types.desc, "Unknown port"),
        coalesce(sensor.rowid,devices.rowid),
        wireless_devices.ah,
        wireless_devices.al,
        wireless_devices.na,
        wireless_devices.trace,
        wireless_devices.physical_location,
        wireless_devices.parent_network_address,
        sensor.adjustment,
        sensor.alarm_value_low,
        sensor.alarm_value_high,
        coalesce(sensor.current_value, devices.raw_value),
        devices.current,
        coalesce(device_types.desc,"Unknown device"),
        coalesce(device_types.allowed_away_time,1),
        coalesce(device_types.part_nbr,"???"),
        wireless_devices.last_time_in,
        wireless_devices.previous_time_in,
        coalesce(port_types.logic,"Unknown"),
        coalesce(sensor.port,devices.port),
        coalesce(devices.default_state,0),
        coalesce(devices.override_state,-1),
        devices.external_override,
        wireless_devices.db_level,
        parent.db_level,
        coalesce(parent.physical_location, config.network_address),
        parent_device_types.desc,
        coalesce(port_types.type,'U'),
        coalesce(sensor.transition_time,0),
        devices.allow_wemo,
        devices.invert_wemo,
        devices.port_name
        FROM wireless_devices
        left JOIN device_types ON wireless_devices.part_nbr = device_types.part_nbr
        left JOIN port_types   ON device_types.part_nbr = port_types.part_nbr

        LEFT JOIN sensor  ON wireless_devices.ah = sensor.ah
           AND wireless_devices.al = sensor.al
           AND wireless_devices.part_nbr = port_types.part_nbr
           AND sensor.port = port_types.port

        LEFT JOIN devices ON wireless_devices.ah = devices.ah
           AND wireless_devices.al = devices.al
           AND wireless_devices.part_nbr = port_types.part_nbr
           AND devices.port = port_types.port

        LEFT JOIN wireless_devices AS parent ON parent.na = wireless_devices.parent_network_address
           AND wireless_devices.parent_network_address <> 65534
        LEFT JOIN device_types AS parent_device_types   ON parent.part_nbr = parent_device_types.part_nbr
        LEFT JOIN config ON  wireless_devices.parent_network_address = config.network_address
        $filter
        ORDER BY wireless_devices.rowid, port_types.rowid
EOF
    my $last;    ##  OR port_types.type IS NULL
    # print Dumper $wireless_devices[2];
    foreach my $x (@wireless_devices)
    {
        if ($x->{last_time_in} == 0)
        {
            $x->{last_time_in_cooked} = "N/A";
            $x->{previous_time_in_cooked} = "N/A";
        }
        else
        {
            $x->{last_time_in_cooked} = tools::how_long($now,$x->{last_time_in});
            $x->{previous_time_in_cooked} = tools::how_long($x->{last_time_in} , $x->{previous_time_in});
        }
        if ($x->{port_type} eq 'A')  # stops range info from being displayed
        {

        }
        if ($x->{problem_time})
        {
           $x->{problem_date} = localtime($x->{problem_time});
        }
        if ($x->{last_time_in} > 0 && $now - $x->{last_time_in} >  $x->{allowed_time_away})
        {
            $x->{alert} = 1;
            $one_or_more_missing = 1;
            $x->{last_time_in} .= '<br>DEVICE<br>AS GONE<br>MISSING';
        }
        delete $x->{allowed_time_away};
        $x->{problem_time} = tools::how_long($now, $x->{problem_time});


        delete $x->{last_time_in};
        delete $x->{previous_time_in};
        if ($x->{ah} =~ /^\d+?$/)
        {
            $x->{addr_high_hex} = sprintf "%0X", $x->{ah};
            $x->{allow_loc} = 1;
        }
        else
        {
            $x->{allow_loc} = 0;
            $x->{addr_high_hex} = $x->{ah};
        }
        $x->{addr_low_hex} = sprintf "%0X", $x->{al};
        $x->{na_hex} = sprintf "%0X", $x->{na} if $x->{na};
        #$x->{physical_location}  = tools::location_string($x->{physical_location}, $x->{al});
        $x->{strength} = db_level_html($x->{db_level});


        # printf "parent_network_address = [%X]\n", $x->{parent_network_address} ;
        if (defined $x->{parent_network_address})
        {
            if ($x->{parent_network_address} == 65534)
            {
                $x->{router} = "MESH";
            }
            elsif ($x->{parent_network_address} == 0)
            {
                 $x->{router} = "COORDINATOR";
            }
        }
        $x->{parent_network_address} = sprintf '%X', $x->{parent_network_address} if (defined $x->{parent_network_address});
        $x->{na} = sprintf '%X', $x->{na} if (defined $x->{na});
        if (defined $x->{parent_db_level})
        {
            $x->{router} .= '<br>'.$x->{parent_part_desc}.'<br>'.db_level_html($x->{parent_db_level}, -2, '(Strength)');
        }
        delete $x->{parent_db_level};
        delete $x->{parent_part_desc};
        if ($last->{ah}
              && $last->{ah} eq $x->{ah}
              && $last->{al} eq $x->{al} )
        {
            $x->{display} = 0;
            #delete $x->{physical_location};
            #delete $x->{part_desc};
            #delete $x->{last_time_in_cooked};
            #delete $x->{previous_time_in_cooked};
            #delete $x->{db_level};
            #delete $x->{router};
            #delete $x->{red_time};
            #delete $x->{strength};
        }
        else
        {
            $x->{display} = 1;
        }
        $last = $x;
        if ($x->{logic} eq "VOLT")
        {
            my $value_suffix='';
            if ($x->{value} < $x->{alarm_low} || $x->{value} > $x->{alarm_high})  # it is out of range, like battries are out of juce
            {
                $x->{alert} = 1;
                $value_suffix = '<br>VOLTAGE<br>OUT OF<br>SPECIFICATION';
            }
            $x->{value} .= "v".$value_suffix;
            delete $x->{port_type};
        }
        $x->{port_on} = "On";
        $x->{port_off} = "Off";
        $x->{port_none} = "None";
        $x->{override_on} = "On";
        $x->{override_off} = "Off";
        $x->{override_none} = "No Override";
        if ($x->{logic} eq "LOW") # for alarm test
        {
           $x->{default_can_change} = 1;
        }
        if ($x->{logic} eq "BINARY")
        {
            $x->{default_can_change} = 1;
            $x->{wemo_device} = 1;
            $x->{raw_value} = $x->{value};
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
            $x->{default_can_change} = 1;
            $x->{port_on} = "OPEN";
            $x->{port_off} = "CLOSED";
            delete $x->{port_none};
            $x->{override_on} = "OPEN";
            $x->{override_off} = "CLOSED";
            if ($x->{current})
            {
                 $x->{value} = $x->{current} eq 'ON'?'Should<br>be Open':'Should<br>be Closed';
            }
            else
            {
                 $x->{value} = $x->{default_state}?'Should<br>be Open':'Should<br>be Closed';
            }
            $x->{wemo_device} = 1;
        }
        if ($x->{default_state} == 1)
        {
           $x->{default_on_checked} = 'checked';
        }
        elsif ($x->{default_state} == 0)
        {
           $x->{default_off_checked} = 'checked';
        }
        elsif ($x->{default_state} == -1)
        {
           $x->{default_none_checked} = 'checked';
        }
        if ($x->{override_state} == 1)
        {
           $x->{override_on_checked} = 'checked';
        }
        elsif ($x->{override_state} == -1)
        {
           $x->{override_none_checked} = 'checked';
        }
        elsif ($x->{override_state} == 0)
        {
           $x->{override_off_checked} = 'checked';
        }
        delete $x->{default_state};
        delete $x->{override_state};

        if ($x->{logic} eq "TMP36")
        {
            $x->{adjustable_device} = 1;
            if ($metric_units eq "checked")
            {
                $x->{value} = tools::convert_TMP36_C($x->{value}) . "c";
            }
            else
            {
               $x->{value} = tools::convert_TMP36_F($x->{value}) . "f";
            }
        }
        elsif ($x->{logic} eq "H2O")
        {
           delete $x->{port_type};
           $x->{raw_value} = $x->{value};
           if (defined $x->{value} && $x->{value} < 1015)
           {
              $x->{value} = "WET";
           }
           else
           {
              $x->{value} = "DRY";
           }
        }
        elsif ($x->{logic} eq "SW1")
        {
            delete $x->{port_type};
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
            delete $x->{port_type};
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
            delete $x->{port_type};
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
            delete $x->{port_type};
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
            delete $x->{port_type};
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
            delete $x->{port_type};
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
            delete $x->{port_type};
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
            delete $x->{port_type};
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
            delete $x->{port_type};
            $x->{value} = "";
        }

        elsif ($x->{logic} eq "MOMENTARY0")
        {
            delete $x->{port_type};
            $x->{value} = "";
        }
        if ($x->{external_override})
        {
            $x->{external_override} = "External Override";
        }
        else
        {
            delete $x->{external_override};
        }
        delete $x->{logic};
        delete $x->{port_type};
        $x->{allow_wemo_checked} = "checked"  if ($x->{allow_wemo} && $x->{allow_wemo} eq 'checked');
        $x->{invert_wemo_checked} = "checked" if ($x->{invert_wemo} && $x->{invert_wemo} eq 'checked');
        delete $x->{allow_wemo};
        delete $x->{invert_wemo};
    }
return ($one_or_more_missing, @wireless_devices);
}

sub get_debug_status
{
    my ($dt) = @_;
    my @fields = qw(drowid al trace physical_location part_desc);
    my @wireless_devices = $dt->tmpl_loop_query(
        <<EOF, @fields);
        SELECT  wireless_devices.rowid,
        wireless_devices.al,
        wireless_devices.trace,
        wireless_devices.physical_location,
        coalesce(device_types.desc, wireless_devices.part_nbr, "Unknown device")
        FROM wireless_devices
        LEFT JOIN device_types ON wireless_devices.part_nbr = device_types.part_nbr
        ORDER BY wireless_devices.rowid
EOF

    foreach my $x (@wireless_devices)
    {
        $x->{physical_location}  = tools::location_string($x->{physical_location}, $x->{al})."(".substr(sprintf ("%0X", $x->{al}), -4).')';
        delete $x->{al};
    }
return (@wireless_devices);
}

sub db_level_html
{
    my ($db_level, $size_in, $qual_in) = @_;
    my $strength;
    my $qual = "";
    my $size = '';
    if ($size_in)
    {
        $size = "size=$size_in";
    }
    if ($qual_in)
    {
        $qual = $qual_in;
    }
    if ($db_level)
    {
        if ($db_level < 70)
        {
             $strength = "<b><font color=green $size>STRONG$qual</font></b>";
        }
        elsif ($db_level < 80)
        {
             $strength = "<b><font color=#A5DF00 $size>GOOD$qual</font></b>";
        }
        else
        {
             $strength = "<b><font color=#B45F04 $size>WEAK$qual</font></b>";
        }
    }
    else
    {
       $strength = '';
    }
    return $strength;
}

sub get_part_info
{
    my ($dt, $ah, $al, $port) = @_;
    my ($status, $part_nbr, $logic, $toggle_port) = $dt->get_rec(<<EOF, $ah, $al, $port);
    SELECT wireless_devices.part_nbr, port_types.logic, port_types.toggle_port
    FROM wireless_devices
    JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
    WHERE wireless_devices.ah = %s
      AND wireless_devices.al = %s
      AND port_types.port = %s
EOF
   return ($part_nbr, $logic, $toggle_port);
}

sub must_follow
{
    my ($logic) = @_;

    return 1 if ($logic =~ /SW1|SW0|SIG0|CLOSED|OPEN|SIG1|TMP36|H2O/);
    return 0;
}

sub check_ip_address
{
    my ($ip) = @_;
    my $status;  # undef == good
    if (!$ip || $ip eq "")
    {
          # ok to be blank
    }
    else
    {
        if( $ip =~ m/^(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)$/ )
        {
            if($1 <= 255 && $2 <= 255 && $3 <= 255 && $4 <= 255)
            {
                # it is good;
            }
            else
            {
                $status = "One of the octets is out of range, octets must contain a number between 0 and 255";
            }
        }
        else
        {
           $status = "Invalid format for a IP address";
        }
    }
    return $status;
}

sub delete_device
{
   my ($dt, $ah, $al) = @_;
   DBG&&$fp->prt("removing all for %0x:%0x", $ah, $al);
   $dt->do("DELETE FROM wireless_devices WHERE ah = %s AND al = %s", $ah, $al);
   $dt->do("DELETE FROM sensor WHERE ah = %s AND al = %s", $ah, $al);
   $dt->do("DELETE FROM devices WHERE ah = %s AND al = %s", $ah, $al);
   $dt->do("DELETE FROM alerts WHERE ah = %s AND al = %s", $ah, $al);
   $dt->do("DELETE FROM actions WHERE ah = %s AND al = %s", $ah, $al);
   $dt->do("DELETE FROM alert_pictures WHERE  ah = %s AND al = %s", $ah, $al);
   $dt->do("DELETE FROM timed_events WHERE ah = %s AND al = %s", $ah, $al);
   $dt->do("DELETE FROM routing WHERE ah = %s AND al = %s", $ah, $al);
}



sub permit_join
{
    my ($dt, $XbeeSendQueue, $on) =@_;  # on to 1 causes permit joining to be enabled, 0 turns joining off
    my $v = $on?cfg::PERMIT_JOIN_TIME_ON:cfg::PERMIT_JOIN_TIME_OFF;
    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'NJ', value => $v});

    # find all xbee routers and set them

    use constant GET_XBEE_ROUTERS_FIELDS => qw (ah al na);
    use constant GET_XBEE_ROUTERS_SQL => <<EOF;
    SELECT wireless_devices.ah, wireless_devices.al, wireless_devices.na
       FROM wireless_devices WHERE wireless_devices.part_nbr LIKE 'R%'
EOF

    my $get_xbee_routers_sth    = $dt->query_prepare(GET_XBEE_ROUTERS_SQL);
    my @routers = $dt->loop_query_execute($get_xbee_routers_sth, GET_XBEE_ROUTERS_FIELDS);
    DBG&&$fp->prt("on[%s]\n%s", $on, tools::hexDumper("", \@routers));
    foreach my $r (@routers)
    {
        $XbeeSendQueue->enqueue({request => 'PERMIT_JOINING', ah => $r->{ah} ,al => $r->{al}, na => $r->{na}, on => $on});
    }
    DBG&&$fp->prt("requests sent");
    $XbeeSendQueue->enqueue({request => 'HA_ENDPOINTS', ah => 0xffffffff, al => 0xffffffff, na => 0xffff}) if $on;  # broadcast for HA devices
}

# test area
main() if not caller();
sub main {
    my $t;
    my $menu_submit;
    ($t,$menu_submit)=main_page($dt, $now, $WorkerBeeQueue,  $Watchdog, %form);

}


1;
