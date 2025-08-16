package http_processor;
# Copyright 2011,2012 by James E Dodgen Jr.  All rights reserved. 
use Data::Dumper;
use IO::Socket;
use HTML::Template;
use html;
use POSIX ":signal_h";
use POSIX ":sys_wait_h";
use strict;
use tools;

my $xbee_server;
sub process
{
	my ($method, $dt, $now, $main_pid, $WorkerBeeQueue, $XbeeSendQueue, %form) = @_;
	
	my $t;
	if ($main_pid)
	{
		$xbee_server = 1;
	}
	
	if ($method eq "main")
	{
		$t=main_page($dt, $now, $WorkerBeeQueue, %form);
    }
	elsif ($method eq "contacts")
	{
		$t=contacts($dt, $now, $WorkerBeeQueue, %form);
	}
	elsif ($method eq "alarms")
	{
		$t=alarms($dt, $now, $XbeeSendQueue, $WorkerBeeQueue, %form);
	}
	elsif ($method eq "configuration")
	{
		$t=config($dt, $now, $main_pid, $WorkerBeeQueue, %form);
	}
	elsif ($method eq "cameras")
	{
		$t=cameras($dt, $now, %form);
	}
	elsif ($method eq "date")
	{		
	   $t=date($dt, $now, $WorkerBeeQueue, %form);		
	}
	elsif ($method eq "system")
	{
		$t=system_info($dt, $now, %form);
	}
	elsif ($method eq "trace")
	{
		$t=trace_info($dt, $now, %form);
	}
	return $t;		
}
    		
sub alarms
{
    my ($dt, $now, $XbeeSendQueue, $WorkerBeeQueue, %form) = @_;
     my $t = HTML::Template->new_scalar_ref( html::alarms(),
            ( xdebug => 1, xstack_debug => 1 ) );
    my $filterSQL = '';
    if ($xbee_server)
    {
       if (! ImpactVCB::exists())
       {
		   $filterSQL = ' AND cameras.server <> "ImpactVCB" ';
	   }
    }
    if ( $form{state})
    {
        if ( $form{state} eq "Map alarm" )
        {
            if ($form{"SENSORTOALARM:sensor"})
            {
               my ($addr_high, $addr_low, $port ) = split /\:/, $form{"SENSORTOALARM:sensor"};
                                      
               if ($form{"SENSORTOALARM:alarm"})
               {
                  if ($form{"SENSORTOALARM:alarm"} =~ /UnMapSensor/)
                  {
                     # remove the old alarms for this senesor
                     my $status = $dt->do("DELETE FROM alarms WHERE addr_high = %s AND addr_low = %s AND port = %s",
                        $addr_high, $addr_low, $port); 
                  }
                  else
                  {
                    my @alarms = split /\,/, $form{"SENSORTOALARM:alarm"};
                    foreach my $a (@alarms)
                    {
                       my ($alarm_addr_high, $alarm_addr_low, $alarm_port ) = split /\:/, $a;
                         my $status = $dt->do(
                          "INSERT INTO alarms (addr_high, addr_low, port, alarm_addr_high, alarm_addr_low, alarm_port, duration) VALUES (%s,%s,%s,%s,%s,%s,'DEFAULT')",
                        $addr_high, $addr_low, $port, $alarm_addr_high, $alarm_addr_low, $alarm_port);                                         
                    }
                  }
               }                 
            }
        }
        elsif ($form{state} eq "Test alarm" && $form{"SENSORTOALARM:alarm"})
        {  
          my @alarms = split /\,/, $form{"SENSORTOALARM:alarm"};
          foreach my $a (@alarms)
          {
             my ($alarm_addr_high, $alarm_addr_low, $alarm_port ) = split /\:/, $a;
             $XbeeSendQueue->enqueue({request => 'TEST_ALARM',
               ah => $alarm_addr_high, al => $alarm_addr_low, port => $alarm_port}) if($XbeeSendQueue);
          }
        }
        elsif ( $form{state} =~ /^Set\s*Duration\:(\d*)$/ )
        {
			my $rowid = $1;
			$dt->do("UPDATE alarms SET duration = %s WHERE rowid = %s",
			$form{"SENSORTOALARM:duration:${rowid}"}, $rowid);
		}


        elsif ( $form{state} eq "Map Contact" )
        {
            if ($form{"SENSORTOCONTACT:sensor"})
            {
               my ($addr_high, $addr_low, $port ) = split /\:/, $form{"SENSORTOCONTACT:sensor"};                     
               if ($form{"SENSORTOCONTACT:contact"})
               {
                   if ($form{"SENSORTOCONTACT:contact"} =~ /UnMapSensor/)
                   {
                      # remove the old alerts for this contact 
                      my $status = $dt->do("DELETE FROM alerts WHERE addr_high = %s AND addr_low = %s AND port = %s",
                           $addr_high, $addr_low, $port); 
                   }  
                   else
                   {
                     my @contacts = split /\,/, $form{"SENSORTOCONTACT:contact"};
                     foreach my $each_name (@contacts)
                     {                   
                        my $status = $dt->do(
                          "INSERT OR REPLACE INTO alerts (addr_high, addr_low, port, contact) VALUES (%s,%s,%s,%s)",
                        $addr_high, $addr_low, $port, $each_name);                                         
                     }
                   }
               }                 
            }
        }
        elsif ( $form{state} eq "Map Camera" )
        {
            if ($form{"SENSORTOCAMERA:sensor"})
            {
               my ($addr_high, $addr_low, $port ) = split /\:/, $form{"SENSORTOCAMERA:sensor"};                     
               if ($form{"SENSORTOCAMERA:camera"})
               {
                   if ($form{"SENSORTOCAMERA:camera"} =~ /UnMapSensor/)
                   {
                      # remove the old alerts for this contact 
                      my $status = $dt->do("DELETE FROM alert_pictures WHERE addr_high = %s AND addr_low = %s AND port = %s",
                           $addr_high, $addr_low, $port); 
                   }  
                   else
                   {
                     my @cameras = split /\,/, $form{"SENSORTOCAMERA:camera"};
                     foreach my $each_name (@cameras)
                     {                   
                        my $status = $dt->do(
                          "INSERT OR REPLACE INTO alert_pictures (addr_high, addr_low, port, camera_name, repeat_count, repeat_delay) VALUES (%s,%s,%s,%s,0,0)",
                           $addr_high, $addr_low, $port, $each_name);                                         
                     }
                   }
               }                 
            }
        }
        elsif ( $form{state} =~ /^Update\s*Options\:(\d*)$/ )
        {
			my $rowid = $1;
			$dt->do("UPDATE alert_pictures SET repeat_count = %s, repeat_delay = %s WHERE rowid = %s",
			$form{"${rowid}:repeat_count"}, $form{"${rowid}:repeat_delay"}, $rowid);
		}
        $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if($WorkerBeeQueue);
    }
        
        my @contacts_name_only = $dt->tmpl_loop_query(
        "SELECT DISTINCT contact FROM emails ORDER BY contact",
            ( "contact" ));
        $t->param( contacts_name_only => \@contacts_name_only);
               
        my @sensors = $dt->tmpl_loop_query(<<EOF,(qw (addr_high addr_low port desc)) );
            SELECT wireless_devices.addr_high, wireless_devices.addr_low, port_types.port, 
                device_types.desc||"@"||wireless_devices.physical_location||" &rarr; "||coalesce(sensor.location, port_types.desc) 
                FROM wireless_devices
                JOIN device_types ON wireless_devices.part_nbr =  device_types.part_nbr
                JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr 
                  AND port_types.type = "S"
                LEFT JOIN sensor ON wireless_devices.addr_high = sensor.addr_high 
                  AND wireless_devices.addr_low = sensor.addr_low
                  AND port_types.port = sensor.port
                ORDER BY 4
EOF
           
        $t->param( sensors => \@sensors);
        
        my @alarms = $dt->tmpl_loop_query(<<EOF,(qw (addr_high addr_low port desc)) );
            SELECT wireless_devices.addr_high, wireless_devices.addr_low, port_types.port, 
                device_types.desc||"@"||wireless_devices.physical_location||" &rarr; "||port_types.desc 
                FROM wireless_devices
                JOIN device_types ON wireless_devices.part_nbr =  device_types.part_nbr
                JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr 
                  AND port_types.type = "A"
                ORDER BY 4
EOF
            
        $t->param( alarms => \@alarms);
        
        my @mapped_alarms = $dt->tmpl_loop_query(<<EOF,(qw (rowid sensor_desc alarm_desc duration)) );        
        SELECT alarms.rowid, sensd.desc||"@"||sensw.physical_location||" &rarr; "||sensp.desc,
               alarmd.desc||"@"||alarmw.physical_location||" &rarr; "||alarmp.desc, alarms.duration
        FROM alarms
        JOIN wireless_devices AS sensw ON sensw.addr_high =  alarms.addr_high
             AND sensw.addr_low =  alarms.addr_low              
        JOIN device_types AS sensd  ON  sensw.part_nbr = sensd.part_nbr
        JOIN port_types AS sensp ON sensp.part_nbr = sensw.part_nbr
            AND sensp.port = alarms.port
        JOIN wireless_devices AS alarmw ON alarmw.addr_high =  alarms.alarm_addr_high
             AND alarmw.addr_low =  alarms.alarm_addr_low              
        JOIN device_types AS alarmd  ON  alarmw.part_nbr = alarmd.part_nbr
        JOIN port_types AS alarmp ON alarmp.part_nbr = alarmw.part_nbr
            AND alarmp.port = alarms.alarm_port
EOF

        $t->param( mapped_alarms => \@mapped_alarms);   
 
         my @mapped_contacts = $dt->tmpl_loop_query(<<EOF,(qw (sensor_desc contact)) );        
        SELECT DISTINCT sensd.desc||"@"||sensw.physical_location||" &rarr; "||sensp.desc,
               emails.contact
        FROM alerts
        JOIN wireless_devices AS sensw ON sensw.addr_high =  alerts.addr_high
             AND sensw.addr_low =  alerts.addr_low              
        JOIN device_types AS sensd  ON  sensw.part_nbr = sensd.part_nbr
        JOIN port_types AS sensp ON sensp.part_nbr = sensw.part_nbr
            AND sensp.port = alerts.port
        JOIN emails ON alerts.contact = emails.contact
EOF

        $t->param( mapped_contacts => \@mapped_contacts);
        
        my @cameras = $dt->tmpl_loop_query("SELECT camera_name FROM cameras WHERE 1 = 1 $filterSQL ORDER BY 1",("camera"));
        $t->param( cameras_name_only => \@cameras );
        
        my @mapped_cameras = $dt->tmpl_loop_query(<<EOF,(qw (rowid sensor_desc camera repeat_count repeat_delay)) );        
        SELECT DISTINCT alert_pictures.rowid, sensd.desc||"@"||sensw.physical_location||" &rarr; "||sensp.desc,
               alert_pictures.camera_name, repeat_count, repeat_delay
        FROM alert_pictures
        JOIN wireless_devices AS sensw ON sensw.addr_high =  alert_pictures.addr_high
             AND sensw.addr_low =  alert_pictures.addr_low              
        JOIN device_types AS sensd  ON  sensw.part_nbr = sensd.part_nbr
        JOIN port_types AS sensp ON sensp.part_nbr = sensw.part_nbr
            AND sensp.port = alert_pictures.port
EOF
        $t->param( mapped_cameras => \@mapped_cameras);        
   return $t;
}
sub config
{
    my ($dt, $now, $main_pid, $WorkerBeeQueue, %form) = @_;
    my $message = '';
    my $t = HTML::Template->new_scalar_ref( html::configuration(),
            ( xdebug => 1, xstack_debug => 1 ) );
    
    my $prior_cfg;
   
    if ($form{state} )
    {
            if ( $form{state} eq "Update Config" || $form{state} eq "Reboot")
            {                           
                $prior_cfg = tools::get_config($dt);               
                my $status = $dt->do(
                    <<EOF, $form{"CONFIG:contact"}, $dt->trim($form{"CONFIG:freq"}),  $dt->trim($form{"CONFIG:contype"}),  $dt->trim($form{"CONFIG:port"}), $dt->trim($form{"CONFIG:ip"}), $dt->trim($form{"CONFIG:mask"}),  $dt->trim($form{"CONFIG:gw"}), $dt->trim($form{"CONFIG:dns1"}),$dt->trim($form{"CONFIG:dns2"}),$form{"CONFIG:metric_units"}||"no", $form{"CONFIG:ident"}, $form{"CONFIG:trace"},  $form{"CONFIG:printtrace"});
                UPDATE config SET primary_contact = %s, problem_reporting_frequency = %s, connection_type = %s, 
                external_http_port = %s, static_ip = %s, subnet_mask = %s, gateway = %s, dns1 = %s, dns2 = %s, metric_units = %s, ident = %s, trace = %s, print_trace = %s
EOF
                if ($WorkerBeeQueue)
                {
					$WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if($WorkerBeeQueue);					
					if  ( $form{state} eq "Reboot" &&  $WorkerBeeQueue)
					{			   
					   $WorkerBeeQueue->enqueue({request => 'REASON_STARTED', code => 4, descr => "User requested reboot"});
					   $WorkerBeeQueue->enqueue({request => "LOG", fmt => "User requested reboot"});
					   $WorkerBeeQueue->enqueue({request => "BACKUP_NOW"});				   
					   sleep 4;
					   kill(POSIX::SIGUSR1, $main_pid) if ($main_pid);   # causes shutdown to be run in parent process
					}
			    }		
            }
            	     
     }   
    if ($WorkerBeeQueue)
    {  
		$t->param(display_reboot => 1);
	}                                
    my $cfg = tools::get_config($dt);

    my $curripmsg   = tools::check_ip_address($cfg->{static_ip}); 
    my $currmaskmsg = tools::check_ip_address($cfg->{subnet_mask}); 
    my $currgwmsg   = tools::check_ip_address($cfg->{gateway}); 
    my $currdns1msg = tools::check_ip_address($cfg->{dns1}); 
    my $currdns2msg = tools::check_ip_address($cfg->{dns2}); 
    
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
        $message = "No vaild static IP information, DHCP rules inforced";
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
            tools::set_ip($dt); # ok change it to DHCP, about as safe as it gets
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
               my $fell_back = tools::set_ip($dt); # ok change it,              
               if ($fell_back == 1) # does not look like the address is very good
               {
                   $message = "This set of static IP address information does not work, reverted to prior values";
               }
               else
               {
                   print "new address worked\n";
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
     
    $t->param( msg => $message);
    $t->param( curripmsg   => $curripmsg);  
    $t->param( currmaskmsg => $currmaskmsg);  
    $t->param( currgwmsg   => $currgwmsg); 
    $t->param( currdns1msg => $currdns1msg);  
    $t->param( currdns2msg => $currdns2msg);  
    
    $t->param( currident   => $cfg->{ident});
    $t->param( currtrace   => $cfg->{trace});
    $t->param( currprinttrace   => $cfg->{print_trace});
    $t->param( currprimary => $cfg->{primary_contact});
    $t->param( currfreq    => $cfg->{problem_reporting_frequency} );
    $t->param( currcontype => $cfg->{connection_type});
    $t->param( currport    => $cfg->{external_http_port} );
    $t->param( currip      => $cfg->{static_ip});
    $t->param( currmask    => $cfg->{subnet_mask});
    $t->param( currgw      => $cfg->{gateway});
    $t->param( currdns1    => $cfg->{dns1});
    $t->param( currdns2    => $cfg->{dns2});
    $t->param( currunits   => $cfg->{metric_units});
    my @contacts = $dt->tmpl_loop_query(
    "SELECT contact, email_address FROM emails ORDER BY 1,2",
        (  "contact", "email" ));
    $t->param( contacts => \@contacts );
        
   return $t;
}

sub cameras
{
    my ($dt, $now, $WorkerBeeQueue, %form) = @_;
    my $t = HTML::Template->new_scalar_ref( html::cameras(),
            ( xdebug => 1, xstack_debug => 1 ) );
    my $filterSQL ="";
    if ($xbee_server)
    {
		if (! ImpactVCB::exists())
		{
			$filterSQL = ' AND cameras.server <> "ImpactVCB" ';
		}
	}
	if ($form{state} )
	{
		if ($form{state} =~ /^Delete\s*(\d*)/ )
		{
			$dt->do("DELETE FROM cameras WHERE rowid = %s", $1);
		}
		elsif ($form{state} eq "Add")
		{
			$dt->do("INSERT INTO cameras (camera_name, server) values(%s, %s)", $form{add_camera_name}, $form{add_server});
		}
		elsif ($form{state} eq "Update" )
		{
			my %records;
			foreach my $item (keys(%form))
			{
				my ($rowid, $field) = split /\:/, $item;
				if ($field)
				{                  
				   $records{$rowid} = "x";
				}
			}
			foreach my $rowid (keys %records)
			{
				$dt->do(<<EOF,
				UPDATE cameras 
				SET camera_name = %s, wan_access = %s, refresh_rate = %s, pre_reads = %s, raw = %s,
				ip_addr = %s, user = %s, password = %s, port = %s
				WHERE rowid = %s $filterSQL
EOF
				   $form{$rowid.":camera_name"}, $form{$rowid.":wan_access"}||"", $form{$rowid.":refresh_rate"}||0, $form{$rowid.":pre_reads"}||0, $form{$rowid.":raw"}||"",
				   $form{$rowid.":ip_addr"},$form{$rowid.":user"},$form{$rowid.":password"},$form{$rowid.":port"},
				   $rowid);
			}
		}
		$WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if($WorkerBeeQueue);      
	}

    
    my @cameras = $dt->tmpl_loop_query(<<EOF,
    SELECT rowid, camera_name, server,port,wan_access, refresh_rate, pre_reads, raw, ip_addr, user, password
    FROM cameras WHERE 1 = 1 $filterSQL ORDER BY 1
EOF
   (  qw (rowid camera_name server port wan_access refresh_rate pre_reads raw ip_addr user password) ));
    $t->param( cameras => \@cameras );
    foreach my $x (@cameras)
    {
      if ($x->{server} eq "ImpactVCB")  # not a IP camera
      {
        $x->{readonly} = ' readonly ';
      }
      if (! $xbee_server)
      {
		  delete $x->{camera_name};
	  }
    }
    $t->param( cameras => \@cameras );
    return $t;
}

sub date
{
    my ($dt, $now, $WorkerBeeQueue, %form) = @_;
    my $t = HTML::Template->new_scalar_ref( html::date(),
            ( xdebug => 1, xstack_debug => 1 ) );
    my $cfg = tools::get_config($dt);
    my $tz = $cfg->{timezone};
    if ($form{state} )
    {
        if ($form{state} eq "Set Date/Time" )
        {
            my $month = $form{month}; 
            my $day = $form{day};
            my $year = $form{year};
            my $hour = $form{hour};
            my $minute = $form{minute};
            print "hour  = $hour\n";
            $ENV{TZ}=$form{timezone};
            $tz = $form{timezone};
            POSIX::tzset;
            my $rc = $dt->do("UPDATE config SET timezone = %s", $tz);
            tools::fix_last_time_in($dt, $now);
            ## print "---------------- do returend $rc\n";             
            system ('/bin/date', ('-s', "$day $month $year ${hour}:${minute}:00"));
        }
        $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if($WorkerBeeQueue);      
    }
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
    my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
     
    $t->param( month =>  $abbr[$mon]);
    $t->param( day =>  $mday);
    $t->param( year =>  $year + 1900);
    $t->param( hour =>  $hour);
    $t->param( minute =>  $min);
    
    $t->param( timezone =>  $tz);    
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
    my $cfg = tools::get_config($dt);
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

sub trace_info
{
    my ($dt, $now, %form) = @_;
    my $t = HTML::Template->new_scalar_ref(html::trace_list(), (xdebug => 1, xstack_debug => 1 ));
    
    my $smallest;
    my $where="";
    my $delem = ':';
    my $curr_ss_filter = "all";
    if ($form{state})
    {
        if ($form{state} eq "More")
        {
           my $start_here = $form{"start_at"}  + 1;
           $where = "WHERE trace_parms.seq < $start_here";
           $curr_ss_filter = $form{"subsystem_filter"};
	    }  
    }
    my $second_where = ""; 
    if  ($curr_ss_filter ne "all")
    {
		if ($where eq "")
		{
			 $second_where = "WHERE ";
		 }
		 else
		 {
			 $second_where = " AND ";
		 }
		 $second_where .= "trace_name.name = '$curr_ss_filter'";
    }
    
    my @sub_systems = $dt->tmpl_loop_query(<<EOF, (qw(name)));
select trace_name.name
from trace_name 
ORDER BY trace_name.name
EOF
    push @sub_systems, {name => "all"};
    $t->param(sub_systems => \@sub_systems );  
      
    my @items =  $dt->tmpl_loop_query(<<EOF, (qw(seq name fmt parms)));
select trace_parms.seq, trace_name.name, trace_fmt.fmt, trace_parms.parms
from trace_parms
join trace_name on trace_name.name_key = trace_parms.name_key
join trace_fmt on trace_fmt.fmt_key = trace_parms.fmt_key
$where
$second_where
ORDER BY trace_parms.seq DESC
LIMIT 100
EOF
   
    foreach my $r (@items)
	{                      
		my @parms = ();
		if ($r->{parms})
		{
			@parms = split $delem, $r->{parms};
		}    		
		$r->{msg} = sprintf "\t".$r->{fmt}."\n", @parms,"","","","","";
		delete $r->{parms};
		delete $r->{fmt};
		$smallest=$r->{seq};
	}
	$t->param(curr_ss_filter => $curr_ss_filter);
	$t->param(start_at => $smallest);
    $t->param( items => \@items );
    return $t;
}


sub system_info
{
    my ($dt, $now, $WorkerBeeQueue, %form) = @_;
    my $config = tools::get_config($dt);
    my $t = HTML::Template->new_scalar_ref( html::systems_info(),
            ( xdebug => 1, xstack_debug => 1 ) );
            my ($restart_code, $restart_descr) = tools::get_restart_reason($dt);
	$t->param(restart_descr => $restart_descr);
	$t->param(restart_code => $restart_code);
	$t->param(run_time => tools::how_long($now, $config->{process_start_time})); #decimal hours
	$t->param(sysid => tools::system_string($config->{ident},$config->{pan_id}));        
	$t->param(version => $config->{version_number});
	$t->param(server_version => $config->{server_version});
	my $text .= `free -m`."\nSTORAGE\n".`df -m`."\nUPTIME load averages for 1,5,15 minutes\n".`uptime`;		
	
	my $pid_lines="Process info:\n";
	my @processes = $dt->tmpl_loop_query("select name, pid from processes order by pid", ("name", "pid"));
	foreach my $p (@processes)
	{
		
		my $ps= sprintf "ps --pid %s h  o vsz", $p->{pid};
		my $ps_result = `$ps`;
		$ps_result =~ /\s*(\d+)/;
		my $memory = $1;
		$memory = sprintf "%.1f", $memory / 1024;
		$pid_lines .= sprintf "%s\(%s) = %s Mb\n", $p->{name}, $p->{pid}, $memory;
	}	
	$text =~ /\nMem:\s*(\d*)\s*.*\n.*cache\:\s*(\d*)\s*/;
	my $total_memory = $1;
	my $in_use_memory = $2;
	
	$t->param(text => "MEMORY (in Mb) total = $total_memory in_use = $in_use_memory\n".$pid_lines.$text);
	return $t;
}

sub main_page
{
    my ($dt, $now, $WorkerBeeQueue, %form) = @_;
    my $config = tools::get_config($dt);
    my $t = HTML::Template->new_scalar_ref( html::main_page(),
            ( xdebug => 1, xstack_debug => 1 ) );
    # print Dumper \%form;
    if ($form{state})
    { 
        # print $form{state}."\n";
        if ($form{state} eq 'Clear log')
        {
            ## print 'clearing the log\n';
            $dt->do('delete from errors');
        }
        elsif ($form{state} eq 'Restart' )
        {
            exit 0;
        }
        elsif ($form{state} =~ /^Remove\s*(\d*)/ )
        {
            my $rowid = $1;
            # ok clean out all for this one
            my ($status, $ah, $al) = $dt->get_rec("SELECT addr_high, addr_low FROM wireless_devices WHERE rowid = %s", $rowid);
            if ($status == 1)
            {
               printf "removing all for %0x:%0x\n", $ah, $al;
               $dt->do("DELETE FROM wireless_devices WHERE addr_high = %s AND addr_low = %s", $ah, $al);
               $dt->do("DELETE FROM alarms WHERE addr_high = %s AND addr_low = %s", $ah, $al);
               $dt->do("DELETE FROM sensor WHERE addr_high = %s AND addr_low = %s", $ah, $al);
               $dt->do("DELETE FROM problems WHERE addr_high = %s AND addr_low = %s", $ah, $al);
               $dt->do("DELETE FROM alerts WHERE addr_high = %s AND addr_low = %s", $ah, $al);
               $dt->do("DELETE FROM alert_pictures WHERE addr_high = %s AND addr_low = %s", $ah, $al);
            }
            
        }
        elsif ($form{state} eq 'Update' )
        {
            foreach my $key ( keys %form )
            {
                my ($rowid, $field) = split /\:/, $key;
                if ($rowid && $field)
                {
                    printf "%s  -- %s\n", $rowid, $field;
                    if ($field eq "loc")
                    {                 
                       my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                       UPDATE wireless_devices 
                          SET physical_location = %s 
                          WHERE rowid = %s
EOF
                   }
                   if ($field eq "adj")
                   {                 
                       my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                       UPDATE sensor 
                          SET adjustment = %s 
                          WHERE rowid = %s
EOF
                   }
                   if ($field eq "high")
                   {                 
                       my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                       UPDATE sensor 
                          SET alarm_value_high = %s 
                          WHERE rowid = %s
EOF
                   }
                    if ($field eq "low")
                   {                 
                       my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                       UPDATE sensor 
                          SET alarm_value_low = %s 
                          WHERE rowid = %s
EOF
                   }
                    if ($field eq "sensor_desc")
                   {                 
                       my $status = $dt->do(<<EOF, $dt->trim($form{$key}), $rowid );
                       UPDATE sensor 
                          SET location = %s 
                          WHERE rowid = %s
EOF
                   }
        my ($restart_code, $restart_descr) = tools::get_restart_reason($dt);
        $t->param(restart_descr => $restart_descr);
        $t->param(restart_code => $restart_code);
        $t->param(run_time => tools::how_long($now, $config->{process_start_time})); #decimal hours
        $t->param(sysid => tools::system_string($config->{ident},$config->{pan_id}));        
        $t->param(version => $config->{version_number});
        $t->param(server_version => $config->{server_version});
                }
            }
        }
        $WorkerBeeQueue->enqueue({request => "BACKUP_SOON"}) if($WorkerBeeQueue);     
    }
    
        my @wireless_devices = get_devices_status($dt, $now);
        my ($restart_code, $restart_descr) = tools::get_restart_reason($dt);
        $t->param(restart_descr => $restart_descr);
        $t->param(restart_code => $restart_code);
        $t->param(run_time => tools::how_long($now, $config->{process_start_time})); #decimal hours
        $t->param(sysid => tools::system_string($config->{ident},$config->{pan_id}));        
        $t->param(version => $config->{version_number});
        $t->param(server_version => $config->{server_version});
        $t->param( wireless_devices => \@wireless_devices );
        # my @error_log = $dt->tmpl_loop_query("SELECT datetime(time,'unixepoch'), message FROM errors ORDER BY id DESC",(qw (time message)) );
        my @error_log = $dt->tmpl_loop_query("SELECT datetime(time,'unixepoch','localtime'), message FROM errors ORDER BY id DESC",(qw (time message)) );
        $t->param( error_log => \@error_log); 

        return $t;
}

sub get_devices_status
{
	my ($dt, $now) = @_;
	my @wireless_devices = $dt->tmpl_loop_query(
		<<EOF, qw( drowid srowid addr_high addr_low physical_location adjustment sensor_desc alarm_low alarm_high value part_desc part_nbr last_time_in previous_time_in problem_time port_desc logic port) );
		SELECT wireless_devices.rowid, sensor.rowid,
		wireless_devices.addr_high, 
		wireless_devices.addr_low, 
		wireless_devices.physical_location,
		sensor.adjustment,
		sensor.location,
		sensor.alarm_value_low,
		sensor.alarm_value_high,
		sensor.value_1,
		coalesce(device_types.desc,"UNK"),
		coalesce(device_types.part_nbr,"???"),
		wireless_devices.last_time_in,
		wireless_devices.previous_time_in,
		problems.problem_time, 
		coalesce(port_types.desc,"UNK"),
		coalesce(port_types.logic,"UNK"),
		sensor.port
		FROM wireless_devices
		LEFT JOIN sensor    ON wireless_devices.addr_high = sensor.addr_high 
		   AND wireless_devices.addr_low = sensor.addr_low
		LEFT JOIN device_types     ON wireless_devices.part_nbr = device_types.part_nbr
		LEFT JOIN port_types    ON  port_types.part_nbr = wireless_devices.part_nbr
		   AND port_types.port = sensor.port 
		LEFT JOIN problems    ON wireless_devices.addr_high = problems.addr_high 
		   AND wireless_devices.addr_low = problems.addr_low
		   AND port_types.port = problems.port
		WHERE port_types.IO_direction = 1 OR port_types.IO_direction IS NULL          
		ORDER BY device_types.desc, wireless_devices.addr_high, wireless_devices.addr_low, port_types.desc
EOF
	my $last;
	
	foreach my $x (@wireless_devices)
	{
		$x->{last_time_in_cooked} = tools::how_long($now,$x->{last_time_in});
		if ($x->{problem_time})
		{
		   $x->{problem_date} = localtime($x->{problem_time});
		}
		$x->{problem_time} = tools::how_long($now, $x->{problem_time});
	   
		$x->{previous_time_in_cooked} = tools::how_long($x->{last_time_in} , $x->{previous_time_in});
		delete $x->{last_time_in};
		delete $x->{previous_time_in};
		$x->{addr_high_hex} = sprintf "%0X", $x->{addr_high}; 
		$x->{addr_low_hex} = sprintf "%0X", $x->{addr_low};
		$x->{physical_location}  = tools::location_string($x->{physical_location}, $x->{addr_low});                   
		if ($last->{addr_high}
			  && $last->{addr_high} == $x->{addr_high}
			  && $last->{addr_low} == $x->{addr_low} )
		{                
			delete $x->{physical_location};
			delete $x->{part_desc}; 
			delete $x->{last_time_in_cooked};
			delete $x->{previous_time_in_cooked};                                           
		}        
		$last = $x;
		if ($x->{logic} eq "VOLT")
		{
			$x->{value} .= "v";
		}			   
		elsif ($x->{logic} eq "TMP36")
		{
			if (tools::get_config($dt)->{metric_units} eq "checked") 
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
		   if ($x->{value} && $x->{value} < 1023)
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
			if ($x->{value} && $x->{value} == 0)
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
			if ($x->{value} && $x->{value} == 1)
			{
			   $x->{value} = "OPEN";
			}
			else
			{
			   $x->{value} = "CLOSED";
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
	}
return @wireless_devices;
}
1;
