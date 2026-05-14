
#!/usr/bin/perl -w
package HomeMonitor;
# Copyright 2011,2018,2024 by James E Dodgen Jr.  MIT License
use lib '.';
use Data::Dumper;
#use forkQueue;
use POSIX ":signal_h";
use DBI;
use DBD::SQLite;
use DBTOOLS;
print "AlertAway starting ...\n";
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
use favicon;
use Time::HiRes qw (usleep);
use Carp;
use valve;
use tools qw (:debug);
use cfg;
use filterPrint;
use feature 'state';

### use Devel::Size qw(total_size);

my $system_type="sys";
#use constant HOURS24 => 86400;
use constant HOURS12 => 43200;

use constant START_MSG_SENT  => 1;
use constant START_ACKED  => 2;
use constant STOP_MSG_SENT  => 3;
use constant STOP_ACKED  => 4; ## never used, record is deleted when ack is back

use constant DBG => 1;

my $api;
# $Data::Dumper::Indent = 0;
my $fp = filterPrint->new({modules => ["upload_database", "download_database"]});

{
    ###  watchdogTimer();  ## Just for testing
    # ip_tools::set_ip_dhcp();
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $PacketQueue = QueueManager::PacketQueue();
    my ($starting_config, $dt) = initialize($WorkerBeeQueue);
    # Now spawn off the worker processes
    processManager::startAll($dt, $starting_config->{trace}, $WorkerBeeQueue);
    $WorkerBeeQueue->enqueue({request => 'REASON_STARTED', code => 0, descr => "Unknown, Possible crash"});
    $WorkerBeeQueue->enqueue({request => 'STARTUP'});
}
my $shut_down_in_progress = 0;
watchdogTimer();
sleep(2);
exit 0;

sub watchdogTimer
{
    sleep(1);
    $|=1;
    my $dt = db::open(cfg::DBNAME);
    my $Watchdog = QueueManager::Watchdog({reader => 1});
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue({nowait => 1});
    my $EvaluateQueue = QueueManager::EvaluateQueue({nowait => 1});
    my $XbeeSendQueue = QueueManager::XbeeSendQueue({nowait => 1});
    my $start = time;
    my $every5seconds = timer->new(5, $start);
    my $every10seconds = timer->new(10, $start);
    while (1)
    {
        my $req = {request => 'TIMED_OUT'};
        if ($Watchdog->queue_cnt())
        {
            $req = $Watchdog->dequeue();
        }
        else
        {
            sleep 2;
            if ($Watchdog->queue_cnt())
            {
                $req = $Watchdog->dequeue();
            }
        }
        DBG&&$fp->prt("awake reason[%s]", $req->{request});
        my $now = time;
        if ($req->{request} eq "restart_process")
        {
            DBG&&$fp->prt("restart_process [".$req->{process}."]");
            processManager::killandrestart($dt, $req->{process});
        }
        elsif ($req->{request} eq "Reboot")
        {
            DBG&&$fp->prt("Reboot request, shutting down for restart");
            shutDown();
            # this never returns
        }

        if ($every5seconds->test($now))
        {
            # things to check every 5 second go here
            #$EvaluateQueue->enqueue();
        }
        if ($every10seconds->test($now))
        {

            if (processManager::checkHealth($dt, $WorkerBeeQueue)) # something nasty, so reboot to really clean things out
            {
                $WorkerBeeQueue->enqueue({request => 'REASON_STARTED', code => 1, descr => "reboot to fix dead process"});
                $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Process died, causing reboot"});
                DBG&&$fp->prt("bad health a process has died, so shutting down\n");
                shutDown(); # force a reboot
                # this never returns
            }
        }
        #if ($every20seconds->test($now))
        #{
        #}
    }
}

sub shutDown
{
  if ($shut_down_in_progress)
  {
      DBG&&$fp->prt("HomeMonitor:shutDown: in progress, additional request ignored");
      return;
  }
  $shut_down_in_progress=1;

  DBG&&$fp->prt("shutting down for reboot");
  my $dt = db::open(cfg::DBNAME);
  sleep(10);
  db::backup($dt, cfg::SAVE_DATABASE_AS);
  processManager::killAll();
  DBG&&$fp->prt("exitcode 1");
  exit 1;
}

# this runs as a seperate process, it is non real-time in that processing  messages can take various amounts of time.
sub worker_bee
{
    my ($trace_in) = @_;
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue({reader => 1});
    my $WorkerBeeQueue_enqueue = QueueManager::WorkerBeeQueue({nowait => 1});
    my $ProcessMsgQueue = QueueManager::ProcessMsgQueue({nowait => 1});
    my $EvaluateQueue = QueueManager::EvaluateQueue({nowait => 1});
    my $PacketQueue = QueueManager::PacketQueue({nowait => 1});
    my $EmailQueue = QueueManager::EmailQueue({nowait => 1});
    my $Watchdog = QueueManager::Watchdog({nowait => 1});
    my $TraceQueue = QueueManager::TraceQueue({nowait => 1});
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
    my $queue_timeout = 60;  # in seconds
    my $email_status_hour = 8;
    my $email_status_sent = 0;
    ##   for testing uset_ippload_database($tracer,$dt);
    my $get_network_frequency = 99999;  # force a net scan at first watchdog wakeup
    DBG&&$fp->prt("starting ...");

    while ( 1 )
    {
        my $q = $WorkerBeeQueue->dequeue($queue_timeout);
        if (!$q)
        {
            $q->{request} = 'WATCHDOG WAKEUP';
            $call_home_loop_counter++;
        }
        #sample_all_devices($dt,$XbeeSendQueue, $notXbees);

        my $config = tools::get_config($dt);
        my $now = time;
        #my $msg; eval $raw;
        #my $q = $msg;
        #DBG&&$fp->prt("hm:worker_bee: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<processing [%s]>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", $q->{request}||Dumper \$q);
        if ($q->{request} eq "LOG")
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
            DBG&&$fp->prt("logged error message  [%s]", $msg);
        }
        elsif ($q->{request} eq 'REASON_STARTED')
        {

            DBG&&$fp->prt("Setting REASON_STARTED [%s] [%s]",  $q->{code}, $q->{descr});
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
           #$XbeeSendQueue->enqueue({request => 'TOGGLEONOFF', ah => 0xE20DB9FF, al => 0xFE08063F, na => 0x2E99, endpoint => 0xa, profile_id => 0xC05E});   ## testing

           if ($backup_db_frequency > 19 && $db_changed == 1)    # every twenty sleep cycles we back up, if needed
           {
                db::backup($dt, cfg::SAVE_DATABASE_AS);
                DBG&&$fp->prt("database backup complete");
                $backup_db_frequency = 0;
                $db_changed=0;
            }
            my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now);
            #DBG&&$fp->prt("hm:worker_bee Daily checks current hour = %d > magic hour %d",  $hour, $email_status_hour);
            if ($hour == $email_status_hour)  # magic hour to send the daily status email as well as a few other late night tasks
            {
                if ($email_status_sent == 0)
                {
                    DBG&&$fp->prt("hm:worker_bee doing checks and email");
                    my $id = tools::system_string($config->{pan_id}, $config->{ident});
                    email::email_daily_status($dt, $WorkerBeeQueue_enqueue, $EmailQueue, "Daily status", "Good morning, here is your daily status");
                    DBG&&$fp->prt("hm:worker_bee:magic hour backup");
                    db::backup($dt, cfg::SAVE_DATABASE_AS);
                    upload_database($dt);
                    #route_collection::clean($dt);
                    #route_collection::get($dt,$XbeeSendQueue);
                    $email_status_sent = 1;
                }
            }
            else # not the magic hour
            {
                ### evaluate::check_timers($now, $dt, $XbeeSendQueue);
                ###$EmailQueue->enqueue({cmd => 'reminder_check', event_time => 0});
                $email_status_sent = 0; # this set is for the next $email_status_hour one shot
            }
        }
        elsif ($q->{request} eq 'BACKUP_NOW')
        {
            DBG&&$fp->prt("hm:worker_bee:backup now");
            db::backup($dt, cfg::SAVE_DATABASE_AS);
            DBG&&$fp->prt("hm:worker_bee:database backup complete");
        }
        elsif ($q->{request} eq 'BACKUP_SOON')
        {
            $db_changed = 1;
            $backup_db_frequency = 10;
        }
        elsif ($q->{request} eq 'GOOD_XBEE_COMM')
        {
            DBG&&$fp->prt("hm:worker_bee:processed GOOD_XBEE_COMM");
            $good_xbee_comm = 1;
        }

       ## end of message processing, now do other  checks

        if ($fresh_started == 1)
        {
            #$WorkerBeeQueue_enqueue->enqueue({request => "LOG", fmt => "Sending startup email"});
            DBG&&$fp->prt("hm:worker_bee:Sending startup email");
            my ($restart_code, $restart_descr) = tools::get_restart_reason($dt);
            email::email_daily_status($dt, $WorkerBeeQueue_enqueue, $EmailQueue, "Starting", "Restart because of - $restart_descr");
            $fresh_started = 0;
        }

        # is it time to phone home?
        if ($config->{pan_id} && $call_home_loop_counter > 1) # must have this first
        {
          $call_home_loop_counter = 0;
          # DBG&&$fp->prt("hm:worker_bee:pan_id = %0x", $pan_id);
          my $pe = $dt->trim($config->{primary_contact});
          my $cip = ip_tools::get_ip_addr($config, $WorkerBeeQueue_enqueue);
          if ($config->{ip_set_status} != 0 || ($config->{connection_type} eq 'STATIC IP' && $cip ne  $config->{static_ip}))
          {
              my $ip_status = ip_tools::set_ip($dt);  ## try again
              if ($ip_status == 0)  # good it worked this time
              {
                  $WorkerBeeQueue_enqueue->enqueue({nowait => 1, request => "LOG", fmt => "Retry of primary IP set now worked"});
                  DBG&&$fp->prt("hm:worker_bee:Retry of primary IP set now worked");
                  $dt->do("update config set ip_set_status = 0");
              }
          }
          DBG&&$fp->prt("hm:worker_bee: IP address = $cip");
          #if (($primary_email ne $pe) # if it has changed then phone home now
              #|| (!$current_ip_address || $current_ip_address ne $cip)
              #|| $call_home_loop_counter > 15)
          {
              $primary_email = $pe;
              $current_ip_address = $cip;

              my ($status, $parms) = tools::phone_home($dt, $config, $cip, $system_type, $WorkerBeeQueue_enqueue);
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
                     $Watchdog->enqueue({request => 'Reboot'});
                     # kill(POSIX::SIGUSR1, getppid());  # causes graceful shutdown to be run in parent process
                  }
                  if ($parms->{pull_db}) # this is a request to pull a db from alertaway.com and use it. a little complex also causes a reboot.
                  {
                      download_database($dt);
                      $Watchdog->enqueue({request => 'Reboot'});
                      #kill(POSIX::SIGUSR1, getppid());  # causes graceful shutdown to be run in parent process
                  }
                  if (DBG && !defined $parms->{latest_version})
                  {
                      DBG&&$fp->prt("%s",Dumper $parms);
                  }
                  my $server_version = sprintf("%d",$parms->{latest_version}||0);
                  my $default_email =$dt->trim($parms->{default_email});
                  $dt->do('update config set server_version = %s, default_email = %s', $server_version, $default_email);
                  DBG&&$fp->prt("hm:worker_bee:Server version = %d, local version = %d problem = %s problem version = %s",
                      $server_version, $config->{version_number}, $parms->{upgrade_problem}||'NONE', $parms->{problem_server_version_number}||'N/A');

                  # now lets do somthing with the default email, if it exists.

                  if ($default_email ne '' && ($pe eq '' || $pe eq 'none')) # we have one from alertaway.com an no primary has been set so fix it
                  {
                     DBG&&$fp->prt("hm:worker_bee:setting default email to primary [%s]", $default_email);
                     $dt->do('update config set primary_contact = default_email');
                     $config->{primary_contact} =  $default_email;  # might need this below
                     $dt->do('insert or replace into  emails (contact, email_address) values ("Default email", %s)',  $default_email);
                  }
                  if ($config->{upgrade_problem})
                  {
                      if ($server_version == $parms->{problem_server_version_number} && $now > ($config->{process_start_time} + (3600*24)))
                      {
                          # ignore for now, we will check back in 24 hours, this keeps us out of a reboot loop
                      }
                      else # an even newer version that the problem version
                      {
                          DBG&&$fp->prt("hm:worker_bee:time to upgrade (problem), backing up and exiting process");
                          $dt->do("INSERT INTO errors (time, message) values (%s,%s)", $now, "rebooting for software upgrade");
                          $db_changed = update_reason_started($dt, 3, "Software upgrade, from problem");
                          $db_changed=0;
                          $EmailQueue->enqueue({cmd => 'to_primary', subject => "AlertAway upgrade", event_time => 0,
                              msg => "AlertAway upgrade","The AlertAway Software is restarting to install a upgrade\nFrom version $config->{version_number}, to version $server_version\n"
                                   });

                          #evaluate::email_to_contacts($dt, $WorkerBeeQueue,  $XbeeSendQueue,
                          #"AlertAway upgrade","The AlertAway Software is restarting to install a upgrade\nFrom version $config->{version_number}, to version $server_version\n");
                          $Watchdog->enqueue({request => 'Reboot'});
                          #kill(POSIX::SIGUSR1, getppid());   # causes shutdown to be run in parent process
                          sleep 99;
                      }
                  }
                  elsif ($server_version > $config->{version_number})  # looks like it is upgrade time
                  {
                     DBG&&$fp->prt("hm:worker_bee:time to upgrade, backing up and exiting process");
                     $dt->do("INSERT INTO errors (time, message) values (%s,%s)", $now, "rebooting for software upgrade");
                     $db_changed = update_reason_started($dt, 4, "Software upgrade");
                     $EmailQueue->enqueue({cmd => 'to_primary', subject => "AlertAway upgrade", event_time => 0,
                         msg => "AlertAway upgrade, \"The AlertAway Software is restarting to install a upgrade\nFrom version $config->{version_number}, to version $server_version\n"});

                     # evaluate::email_to_contacts($dt, $WorkerBeeQueue,  $XbeeSendQueue, "AlertAway upgrade", "The AlertAway Software is restarting to install a upgrade\nFrom version $config->{version_number}, to version $server_version\n");
                     sleep 1;
                     $Watchdog->enqueue({request => 'Reboot'});
                     #kill(POSIX::SIGUSR1, getppid());  # causes graceful shutdown to be run in parent process
                     sleep 99
                  }
              }
              else
              {
                  my $time_to_fail = time - $now;
                  DBG&&$fp->prt("hm:worker_bee:problem with phone home, nothing done time to fail %s", $time_to_fail);
                  # next;
              }
          }
        }

        if ($now > $good_xbee_time && $good_xbee_comm == 0)  # not good looks like xbee sending is out of sync, best to reboot
        {
            DBG&&$fp->prt("hm:worker_bee: xbee sending is out of sync, best to reboot");
            $dt->do("INSERT INTO errors (time, message) values (%s,%s)", $now, "rebooting to fix xbee send problem");
            update_reason_started($dt, 9, "XBee comm problem");
            $Watchdog->enqueue({request => 'Reboot'});   # causes shutdown to be run in parent process
            sleep 99;
        }


        # current thought is to delay a short time after a restart just to give devices time to check in
        # so I need to use $now and well as the start time, a minute should do it
        # check three tables for problems sensor, wireless devices, and devices
        $delay_time=0;
        if ($now > $delay_time)
        {
            DBG&&$fp->prt("hm:worker_bee: checking for lost devices");
            my @devices =  $dt->tmpl_loop_query(<<EOF, (qw(rowid addr_h addr_l na last_time_in loc desc allowed_away_time time_reported_gone parent_addr part_nbr)));
            SELECT wireless_devices.rowid, wireless_devices.ah, wireless_devices.al,  wireless_devices.na, wireless_devices.last_time_in,
                   wireless_devices.physical_location, device_types.desc,
                   device_types.allowed_away_time,wireless_devices.time_reported_gone,
                   wireless_devices.parent_network_address,
                   wireless_devices.part_nbr
            FROM wireless_devices
            JOIN device_types ON wireless_devices.part_nbr = device_types.part_nbr
EOF
            #### DBG&&$fp->prt Dumper "hm:worker_bee:devices ", @devices, "\n" if DEBUG;

            my $problem_reporting_frequency = tools::get_config($dt)->{problem_reporting_frequency};
            my $allowed_prf_seconds = $problem_reporting_frequency * 60; # convert to seconds
            my $its_time_to_ignore = HOURS12;

            foreach my $d (@devices)
            {
                if ($d->{allowed_away_time} > 0 && $d->{last_time_in} < ($now - $d->{allowed_away_time})) # looks like a device has gone away
                {
                    DBG&&$fp->prt("hm:worker_bee: lost check gone too long");
                    if ($d->{time_reported_gone})  # it has been reported gone
                    {
                        DBG&&$fp->prt("hm:worker_bee: lost check recent enough");
                        next; #  ignore for now, no need to bug them
                    }
                    # else # Has not been reported yet yet
                    {
                        DBG&&$fp->prt("hm:worker_bee: lost check updating time_reported_gone");
                        my $status = $dt->do("UPDATE wireless_devices SET time_reported_gone = %s WHERE rowid = %s", $now, $d->{rowid});
                    }
                    DBG&&$fp->prt("lost check now we should email");
                    my $time_string = localtime($d->{last_time_in});
                    my $loc =  tools::location_string($d->{loc}, $d->{addr_l});
                    my $subject = 'Lost connection to "'.$d->{desc}.'@'.$loc.'"';
                    my $msg = sprintf "%s @ %s has not reported in since: %s (%s)\n", $d->{desc}, $loc, $time_string, tools::how_long($now, $d->{last_time_in});
                    my $force = 1;
                    $EmailQueue->enqueue({cmd => 'to_primary', subject => $subject, msg => $msg, ah => $d->{addr_h},
                          al => $d->{addr_l}, event_time => $now||0});
                }
                elsif ($d->{time_reported_gone})
                {
                     DBG&&$fp->prt("hmworker_bee: lost check it looks like it is back and we have reported it gone");
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
                    DBG&&$fp->prt("lost check device is fine");
                }
                #DBG&&$fp->prt("");
            }
        }
        else
        {
            DBG&&$fp->prt("waiting time left %s", $delay_time - $now);
        }


    }
    DBG&&$fp->prt("exiting");
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
    # gzip last backup
    my $pan_id = tools::get_config($dt)->{pan_id};
    my $local_path = "/dev/shm/${pan_id}.db.gz";
    my $remote_dir = "databases";
    my $remote_path = "$remote_dir/${pan_id}.db.gz";
    system ("gzip -c ".cfg::SAVE_DATABASE_AS." > $local_path");
    my $sftp = tools::connect_to_sftp("upload_database");
    if (!$sftp)
    {
       DBG&&$fp->prt("could not open the ftp connection [%s]", cfg::FTP_SITE);
    }
    else
    {
        my $databases_exists = 0;
        DBG&&$fp->prt("sftp open worked");
        my $files = $sftp->ls('.');
        foreach my $n (@$files)
        {
            DBG&&$fp->prt("remote file[%s]", $n->{filename});
            if ($n->{filename} eq  $remote_dir)
            {
                $databases_exists = 1;
                last;
            }
        }
        if (!$databases_exists) # we need to make the dir
        {
            DBG&&$fp->prt("making directory [%s]", $remote_dir);
            my $attrs = Net::SFTP::Foreign::Attributes->new(());
            $sftp->do_mkdir($remote_dir,$attrs);
        }
        DBG&&$fp->prt("Now sending %s to %s", $local_path, $remote_path);
        eval {local $SIG{__DIE__}; $sftp->put($local_path, $remote_path);};
        if ($@)
        {
            DBG&&$fp->prt("die cause a fail in ftp send [%s]", $@);
        }
        else
        {
            DBG&&$fp->prt("database uploaded OK");
        }
    }
}

sub download_database
{
    my ($dt) = @_;
    # note all the tracing will be lost if this works
    # gzip last backup
    my $pan_id = tools::get_config($dt)->{pan_id};
    my $local_path = "/dev/shm/${pan_id}.db.gz";
    my $remote_path = "/databases/${pan_id}.db.gz";
    my $sftp = tools::connect_to_sftp("download_database");
    if (!$sftp)
    {
       DBG&&$fp->prt("could not open the ftp connection [%s]",cfg::FTP_SITE);
    }
    else
    {
        DBG&&$fp->prt("ftp open worked");
        DBG&&$fp->prt("Now getting [%s] to [%s]", $remote_path, $local_path);
        eval {local $SIG{__DIE__}; $sftp->get($remote_path, $local_path);};
        if ($@)
        {
            DBG&&$fp->prt("die cause a fail in ftp get [%s]", $@);
        }
        else
        {

            DBG&&$fp->prt("now doing the gunzip");
            system ("gunzip -c ".$local_path." > ".cfg::SAVE_DATABASE_AS);
            my $saved_dt = db::open(cfg::SAVE_DATABASE_AS);
            $saved_dt->do("UPDATE reason_started SET next_code = %s, next_descr = %s", 8,"Phone home DB download");
        }
    }
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
    DBG&&$fp->prt("status email at %s\n", scalar localtime($restart_time));
    return $restart_time;
}

sub initialize
{ # this is the startup stuff
    my ($WorkerBeeQueue) = @_;
    #flush queue, get Ehernat port, open database
    my $dt = db::open(cfg::DBNAME);
    ip_tools::save_port($dt);
    my $WorkerBeeQueue_dequeue = QueueManager::WorkerBeeQueue({reader => 1});
    while (1)
    {
        my $q = $WorkerBeeQueue_dequeue->dequeue(2);
        if (!$q) # timed out
        {
            #DBG&&$fp->prt("WorkerBeeQueuequeue empty ");
            last;
        }
        #DBG&&$fp->prt("Flushing WorkerBeeQueue queue");
    }
    
    db::apply_patch($dt);
    db::load_static_data($dt);
    my $starting_config = tools::get_config($dt);
    my  $cip = ip_tools::get_ip_addr($starting_config, $WorkerBeeQueue);

    
    open my $ver, "</alertaway/version.txt";
    my $version_number_raw = <$ver>;
    close $ver;
    my ($version_number,  $upgrade_problem,  $problem_server_version_number) = split /\s/, $version_number_raw;


    my $cnt=0;
    while (1) ## loop until we get the time from home
    {
      DBG&&$fp->prt("phone home\n");
      my ($status, $parms) = tools::phone_home($dt, $starting_config, $cip, $system_type, $WorkerBeeQueue);
      if ($status)
      {
          DBG&&$fp->prt("time returned from phone_home = %s", $parms->{time});
          time_keeper::set_time($dt, $parms->{time});
          last;
      }
      if ($cnt++ > 2)
      {
          $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Problem contacting AlertAway.com for correct date/time"});
          DBG&&$fp->prt("Problem contacting AlertAway.com for time");
          ## now we have a bad starting time so we should fix it and all the times that have been recorded,
          ## the times will be thrown off and this is a problem
          # we will use a offset time to correct this,
          last;
      }
    }

    my $now = time;
    #DBG&&$fp->prt("----- updating process starttime %s\n", $now);
    $dt->do("update config set version_number = %s, upgrade_problem = %s, problem_server_version_number = %s, process_start_time = %s, time_offset = 0",
           $version_number,  $upgrade_problem,  $problem_server_version_number, $now);

    my $ip_set_status = 0;
    my $ip_status = ip_tools::set_ip($dt); # 0 = primary worked, 1 = backup worked, 2 = both failed
    if ($ip_status == 0)
    {
        DBG&&$fp->prt("primary IP set worked");
        $WorkerBeeQueue->enqueue({request => "LOG", fmt => "initialize::primary IP set worked"});
    }
    else ## Had IP problems, so log messages and set value to re-try later
    {
        $ip_set_status = 1;
        DBG&&$fp->prt("primary IP set had problems, status = %s", $ip_set_status);
        if ($ip_status ==  2)
        {
            $WorkerBeeQueue->enqueue({request => "LOG", fmt => "initialize::primary and secondary failed so default to DHCP"});
        }
        elsif ($ip_status ==  1)
        {
            $WorkerBeeQueue->enqueue({request => "LOG", fmt => "initialize::primary IP set failed, fell back to last working IP set"});
        }
    }
    DBG&&$fp->prt("updating process starttime [%s]", $now);
    $dt->do("update config set version_number = %s, upgrade_problem = %s, problem_server_version_number = %s, process_start_time = %s, ip_set_status = %s",
           $version_number,  $upgrade_problem,  $problem_server_version_number, $now, $ip_set_status);



    my $timezone = $starting_config->{timezone};
    if ($timezone && $timezone gt "")
    {
        $ENV{TZ}=$timezone;
        POSIX::tzset;
        DBG&&$fp->prt("setting time zone = %s", $timezone);
    }
    else
    {
        DBG&&$fp->prt("no timezone set");
    }

    my $date_string = localtime($now);
    DBG&&$fp->prt("hm:initialize: DATE:  %s", $date_string);
    $dt->do("INSERT or REPLACE INTO processes (name, pid) VALUES (%s,%s)", 'main', $$);
    rotate_reason_started($dt);
    tools::fix_last_time_in($dt, $now);
    # $dt->do("UPDATE wireless_devices SET db_level = NULL, na = NULL, parent_network_address = NULL");
    #my $rid = $dt->last_insert_rowid();
    #DBG&&$fp->prt("last_insert_rowid [%s]",$rid);
    return ($starting_config, $dt);
}


sub sample_all_devices
{
    my ($dt, $XbeeSendQueue, $notXbees) = @_;
    state $sample_all_devices_dt;
    state $sample_all_devices_sth;
    use constant SAMPLE_ALL_DEVICES_FIELDS => qw (ah al na port device_type endpoint profile_id);
    use constant SAMPLE_ALL_DEVICES_SQL => <<EOF;
SELECT wireless_devices.ah, wireless_devices.al, wireless_devices.na, '', device_types.part_type, wireless_devices.endpoint, wireless_devices.profile_id
       FROM wireless_devices
       JOIN device_types
        ON device_types.part_nbr = wireless_devices.part_nbr
       WHERE device_types.part_type <> 'HA'
    UNION
    SELECT wireless_devices.ah, wireless_devices.al, wireless_devices.na, port_types.port, device_types.part_type, wireless_devices.endpoint, wireless_devices.profile_id
       FROM wireless_devices
       JOIN device_types
        ON device_types.part_nbr = wireless_devices.part_nbr
       JOIN port_types
        ON device_types.part_nbr = port_types.part_nbr
       WHERE device_types.part_type = 'HA'
EOF
    state $sample_all_devices_HA_sth;
    use constant SAMPLE_ALL_DEVICES_HA_SQL => <<EOF;
    SELECT wireless_devices.ah, wireless_devices.al, wireless_devices.na, port_types.port, device_types.part_type, wireless_devices.endpoint, wireless_devices.profile_id
       FROM wireless_devices
       JOIN device_types
        ON device_types.part_nbr = wireless_devices.part_nbr
       JOIN port_types
        ON device_types.part_nbr = port_types.part_nbr
       WHERE device_types.part_type = 'HA'
EOF

    if (! $sample_all_devices_dt)
    {
        DBG&&$fp->prt("doing prepare, if you see this late in the run you have a memory leak");
        $sample_all_devices_dt = $dt;
        $sample_all_devices_sth    = $dt->query_prepare(SAMPLE_ALL_DEVICES_SQL);
        $sample_all_devices_HA_sth = $dt->query_prepare(SAMPLE_ALL_DEVICES_HA_SQL);
    }
    my @alarms = $dt->loop_query_execute($notXbees ? $sample_all_devices_HA_sth : $sample_all_devices_sth, SAMPLE_ALL_DEVICES_FIELDS);
    DBG&&$fp->prt("%s", tools::hexDumper("sample_all_devices", \@alarms));
    foreach my $a (@alarms)
    {
        DBG&&$fp->prt("requesting sample [%x:%x][%x]", $a->{ah}, $a->{al}, $a->{na}||0);
        # this will force the remotes to send ports and cause a state evaluation
        $XbeeSendQueue->enqueue({request => 'FORCE_SAMPLE', ah => $a->{ah}, al => $a->{al}, na => $a->{na},
               port => $a->{port}, device_type => $a->{device_type},  endpoint => $a->{endpoint}, profile_id => $a->{profile_id}});
    }
}

package timer;
sub new
{
    my ($class,$period,$now) = @_;
    my $self = {};
    bless( $self, $class );
    $self->{period} = $period;
    $self->{last} = $now;
    $self->{elapsed_time} = 0;
    return $self;
}

sub test
{
    my ($self,$now) = @_;
    $self->{elapsed_time} += ($now - $self->{last});
    $self->{last} = $now;
    if ($self->{elapsed_time} >= $self->{period})
    {
        $self->{elapsed_time} = 0;
        return 1;
    }
}

