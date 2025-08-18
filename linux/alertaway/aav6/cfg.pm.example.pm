package cfg;
# Copyright 2011-2025 by James E Dodgen Jr.  All rights reserved.
use strict;

use constant TIMEDATECTL => "/usr/bin/timedatectl";
# database locations and names
use constant DBNAME  => '/dev/shm/hm.db';   # working data base, in shared memory
use constant SAVE_DATABASE_AS => '/database/saved.db';
# email stuff
use constant DEFAULT_EMAIL => 'jim@dodgen.us';
use constant DEFAULT_FROM => 'AlertAway@gmail.com';
use constant DEFAULT_PASSWORD => "xxxx xxxx xxxx xxxx";
# FTP/SSH stuff
use constant FTP_SITE     => 'alertaway.com';
use constant FTP_USER     => 'alerta';
use constant FTP_PASSWORD => "password";
use constant FTP_PORT     => 22;

#use constant CONFIG_FRESH_READ => 1;

my $system_type="sys";
use constant HOURS24 => 86400;
use constant HOURS12 => 43200;

use constant START_MSG_SENT  => 1;
use constant START_ACKED  => 2;
use constant STOP_MSG_SENT  => 3;
use constant STOP_ACKED  => 4; ## never used, record is deleted when ack is back

# PERMIT_JOIN time in sconds 0xff is forever

use constant PERMIT_JOIN_TIME_ON => pack('C', 0xff);
use constant PERMIT_JOIN_TIME_OFF => pack('C', 0x0);
#use constant CB2 => pack('C',2);
1;



