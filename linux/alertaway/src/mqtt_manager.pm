package mqtt_manager;
# Copyright 2017, 2023 by James E Dodgen Jr.  All rights reserved.

use DBI;
use DBD::SQLite;
use DBTOOLS;
use db;
use cfg;
use Filesys::Df;
use Data::Dumper;
# use Net::EmptyPort; # qw(empty_port check_port);
use strict;
use tools qw (:debug);
use filterPrint;

use constant DBG => 1;

my $fp = filterPrint->new();


sub task
{
    use Inline Python => <<'...';
import  mqtt_processor
mqtt_processor.mqtt_task()
...
}

1;
