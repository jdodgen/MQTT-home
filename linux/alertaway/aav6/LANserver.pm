package LANserver;
# Copyright 2011,2012 by James E Dodgen Jr.  All rights reserved.
use Data::Dumper;
use IO::Socket;
use HTML::Template;
use html;
use DBI;
use DBTOOLS;
use strict;
use favicon;
use tools;
use ip_tools;
use http_processor;
use cfg;
use filterPrint;

#use ImpactVCB;
use tools qw (:debug);
use constant DBG => 1;
my $fp;
sub task
{
    $SIG{CHLD} = 'IGNORE';
    my ($trace_in) = @_;
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue({nowait => 1});
    my $XbeeSendQueue = QueueManager::XbeeSendQueue({nowait => 1});
    my $EmailQueue = QueueManager::EmailQueue({nowait => 1});
    my $Watchdog = QueueManager::Watchdog({nowait => 1});
    my $EvaluateQueue = QueueManager::EvaluateQueue({nowait => 1});
    my $main_pid = getppid();
    my $config_at_start;
    {
        my $dt = db::open(cfg::DBNAME);
        $config_at_start = tools::get_config($dt);
    }
    $fp = filterPrint->new();
    $fp->filter();
    my $ip  = ip_tools::get_ip_addr($config_at_start, $WorkerBeeQueue);
    my $internal_http_port = $config_at_start->{internal_http_port};
    my $server = IO::Socket::INET->new(
        Proto     => 'tcp',
        LocalPort => $internal_http_port,
        Listen    => 4,
        ReuseAddr     => 1
    );
    if (! $server)
    {
      DBG&&$fp->prt("LANserver: Unable to open LAN server port %s [$@]\n", $internal_http_port);
      $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Unable to open LAN server port %s", parms => [$internal_http_port]});
      sleep(20);
      return;
    }
    binmode $server;
    my $t;

    printf("accepting clients at http://%s:%s]\n",$ip,$internal_http_port);

    while ( my $client = $server->accept() )
    {
      my $pid = fork;
      if ($pid)  # in parent
      {
         DBG&&$fp->prt(" started process pid[%d]\n", $pid);
         next;
      }
      die "fork failed: $!" unless defined $pid;
      process_request($client, $WorkerBeeQueue, $XbeeSendQueue, $Watchdog, $EmailQueue, $main_pid, $EvaluateQueue);
      exit 0;
     }
}

sub process_request
{
    my ($client, $WorkerBeeQueue, $XbeeSendQueue, $Watchdog, $EmailQueue, $main_pid, $EvaluateQueue) = @_;
    my $dt = db::open(cfg::DBNAME, {debug => 1});
    my $now = time;
    my $remote_IP = $client->peerhost();
    DBG&&$fp->prt("process_request:  recieved a request from  %s\n", $remote_IP);
    $client->autoflush(1);
    my $t;
    my $menu_submit;
    my $request;
    $client->recv($request,4096);
    if (defined $request )
    {
        DBG&&$fp->prt("process_request: request [%s]\n", $request);
        my ($method, %form) = tools::parse_http_request($request);
        DBG&&$fp->prt("process_request: request [%s]\n", Dumper \%form) if (%form);
        if (!$method) ## main page
        {
            $method="main";
        }
        if ($method eq "extern")
        {
            my $result = http_processor::extern($dt, $now, $WorkerBeeQueue, $XbeeSendQueue, $EmailQueue, $EvaluateQueue, %form);
            $client->send("HTTP/1.0 200 OK\nContent-Type: text/html\n\n$result");
            close $client;
            return;
        }
        elsif ($method eq "favicon.ico")
        {
            my ($icon) = favicon::get();
            $client->send("HTTP/1.0 200 OK\nContent-Type: image/x-icon\n\n".$icon);
            close $client;
            return;
        }
        elsif ($method eq "whoareyou")
        {
            my ($icon) = favicon::get();
            $client->send("HTTP/1.0 200 OK\nContent-Type: text/html\n\nalertaway");
            close $client;
            return;
        }
        else
        {
            ($t, $menu_submit) = http_processor::process($method, $dt, $now, $main_pid, $WorkerBeeQueue, $XbeeSendQueue, $Watchdog, $EmailQueue, $EvaluateQueue, %form);
            if (! $t)
            {
                $client->send("HTTP/1.0 404 OK\nContent-Type: text/html\n\nunknown method");
                #$client->send("HTTP/1.0 204 OK\n");
                close $client;
                # print "end of routine", Dumper \%form;
                return;
            }
        }

        # push out the form
        if ($t)
        {
          DBG&&$fp->prt("process_request: now sending http message\n");
          $t->param(form_action => html::form_action_LAN());
          my $m = HTML::Template->new_scalar_ref(html::menu());
          $t->param(menu => $m->output);
          tools::clean_html
          $client->send("HTTP/1.0 200 OK\nContent-Type: text/html\n\n".tools::clean_html($t->output));
        }
        else
        {
          $client->send("HTTP/1.0 200 OK\nContent-Type: text/html\n\nNothing to do?");
        }
        close $client;
    }
}

1;
