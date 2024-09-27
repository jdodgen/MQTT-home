package processManager;
# Copyright 2011, 2012, 2024 by James E Dodgen Jr.  MIT
use strict;
use Data::Dumper;
use POSIX ":sys_wait_h";
use IO::Handle;
use tools;
use process_packet;
use LANserver;
use client;
# use xbee_reader;
## use #DVRserver;
use email;
use XBeeXmitProcessor;
use fauxmo_manager;
use mqtt_manager;
use POSIX ":signal_h";
use QueueManager;
use cfg;

use filterPrint;
use constant DBG => 1;

my $fp = filterPrint->new();

my $reader = 1;
my $writer = 2;
my $readWrite = 3;

my @no_xbee_servers = (
               {process => 'evaluate', pgm => \&evaluate::task, nice => 0},
               {process => 'fauxmo_manager', pgm => \&fauxmo_manager::task, nice => -1, autorestart => 1},
               {process => 'LANserver', pgm => \&LANserver::task, nice => 0},
               {process => 'process_packet', pgm => \&process_packet::task, nice => 0},
               {process => 'email', pgm => \&email::task, nice => 3},
               {process => 'worker_bee', pgm => \&HomeMonitor::worker_bee, nice => 5},
               {process => 'SSH client', pgm => \&client::task, nice => 0, autorestart => 1},
               {process => 'mqtt manager (Python)', pgm => \&mqtt_manager::task, nice => 0, autorestart => 1},
               );

# my @xbee_servers = ({process => 'xbee_reader', pgm => \&xbee_reader::xbee_reader, nice => 0},
#                     {process => 'xbee_dispatch', pgm => \&xbee_reader::xbee_dispatch, nice => 0},
#                     {process => 'XBeeXmitProcessor', pgm => \&XBeeXmitProcessor::task, nice => -1}
#                     );

my %running_processes;
my %running_names;


# my $db_name;
my $trace;
my $api;

sub startAll
{
  my ($dt, $trace_in) = @_;
  my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
  $trace = $trace_in;
  foreach my $server (@no_xbee_servers)
  {
    # startSingle($server,  %no_xbee_servers);
     startSingle($dt, $server->{process}, $server->{pgm}, $server->{nice}, $server->{autorestart}, $WorkerBeeQueue);
  }
}

# sub startAllWithXbee
# {
#   my ($dt, $api_in) = @_;
#   my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
#   $api=$api_in;
#   foreach my $server (@xbee_servers)
#   {
#     startSingle($dt, $server->{process}, $server->{pgm}, $server->{nice}, $server->{autorestart}, $WorkerBeeQueue);
#   }
# }

sub startSingle
{
  my ($dt, $name, $program, $nice, $autorestart, $WorkerBeeQueue) = @_;
  my $pid = fork;
    if ($pid)  # in parent
    {
      #printf "processManager:startSingle: starting ... %s > %s\n", $name, $pid;
      $running_processes{$pid} = $name;
      $running_names{$name} = {pid => $pid, pgm => $program, nice => $nice, autorestart => $autorestart};
      $dt->do("INSERT or REPLACE INTO processes (name, pid) VALUES (%s,%s)", $name, $pid);
      # $WorkerBeeQueue->enqueue({request => "SAVE_PROCESS", pid => $pid, name => $name});
      return;
    }
    die "fork failed: $!" unless defined $pid;
    setpriority(0,$$,$nice);
    printf "processManager:startSingle: started [%s] pid [%s]\n", $name, $$;
    &{$program}($trace, $api);
    exit;  # Ends the child process.
}

sub checkHealth
{
    my ($dt, $WorkerBeeQueue) = @_;
    foreach my $process (keys %running_processes)
    {
        my $status = ProcessDeadCheck($process);
        if ($status) # we have a dead child process
        {
            my $name = $running_processes{$process};

            if ($running_names{$name}{autorestart})
            {
                delete $running_processes{$process};
                # sleep 20;
                $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Process $name $process has died, auto restarting"});
                startSingle($dt, $name, $running_names{$name}{pgm}, $running_names{$name}{nice}, $running_names{$name}{autorestart}, $WorkerBeeQueue);
            }
            else
            {
                $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Process $name $process has died"});
                return 1;
            }
        }
    }
    return 0;
}

sub ProcessDeadCheck
{
    my ($process) = @_;
    my $status = waitpid($process, WNOHANG);
    if ($status != 0) # we have a dead child process
    {
        print "processManager:ProcessDeadCheck: Process $running_processes{$process} $process Is dead\n";
        return 1;
    }
    #print STDERR "processManager:ProcessDeadCheck: ***** Process $running_processes{$process} $process is alive\n";
    return 0;
}

sub GetPIDByName
{
    my ($dt, $name) = @_;
    my ($status, $pid) = $dt->get_rec("select pid from processes where name = %s", $name);
    return "unknown" if ($status == 0);
    return $pid;
}

sub killandrestart
{
    my ($dt, $who) = @_;
    if (exists $running_names{$who})
    {
        my $pid = $running_names{$who}{pid};
        my $pgm = $running_names{$who}{pgm};
        my $nice = $running_names{$who}{nice};
        killsingle($pid);
        DBG&&$fp->prt("processManager:killandrestart: restarting [$who]");
        startSingle($dt, $who, $pgm, $nice);
    }
    else
    {
        DBG&&$fp->prt("processManager:killandrestart: ***** Process $who not found");
    }
}

sub killAll
{
  foreach my $pid (keys %running_processes)
  {
     killsingle($pid);
  }
  sleep 10;
}

sub killsingle
{
    my ($pid, $signal) = @_;
    my $vsz = `ps p $pid h o vsz`;
    chomp $vsz;
    printf STDERR "processManager:killsingle: killing %s pid = %s vsz = %s\n", $running_processes{$pid}, $pid, $vsz;
    kill(SIGINT, $pid);
    while(1) ## wait for death
    {
        last if (ProcessDeadCheck($pid));
        sleep 1;
    }
    delete($running_processes{$pid});
}

# # test area
# main() if not caller();
# sub main {
#     print(">>>>>>>>>>>> processManager running <<<<<<<<<<<<<<<<<<<<");
#     startAll();   
# }


1;
