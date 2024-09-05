# !/usr/bin/perl
# Copyright 2011, 2012, 2013, 2021 by James E Dodgen Jr.  All rights reserved.

#  this needs to run as root as well as the rest of AlertAway

use QueueManager;
print "use db\n";
use db;
use cfg;
use tools;
print "alertaway_init starting\n";
mkdir('/database');
db::create_or_copy( cfg::DBNAME, cfg::SAVE_DATABASE_AS);
my $dt = db::open(cfg::DBNAME);

tools::create_htpasswd($dt);
print "htpasswords created\nDestroying message queues\n";
QueueManager::destroy_message_queues();
print "changing the limit size of message queues to 1/2 gig\n";
system("bash -c 'ulimit -q 8388608'");  # max
system("bash -c 'ulimit -q'");

my ($WorkerBeeQueue, $XbeeSendQueue, $TraceQueue, $EmailQueue, $watchdog, $ProcessMsgQueue, $PacketQueue) = QueueManager::create_message_queues();

system("chmod 666 /dev/mqueue/*");

print "message queues created\n";

$WorkerBeeQueue->enqueue({request => "LOG", fmt => "alertaway_init created message queues and copied database"});

print "alertaway_init complete\n";




