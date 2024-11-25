package cfg;
# Copyright 2011-2024 by James E Dodgen Jr.  MIT Licence
use strict;

use constant TIMEDATECTL => "/usr/bin/timedatectl";
# database locations and names
use constant DBNAME  => '/dev/shm/hm.db';   # working data base, in shared memory
use constant SAVE_DATABASE_AS => '/database/saved.db';
# email stuff
use constant DEFAULT_EMAIL => 'jim@dodgen.us';
use constant DEFAULT_FROM => 'AlertAway@gmail.com';
use constant DEFAULT_PASSWORD => "zutgxiuoslillkkj"; #'rikandjed';'rikandjed';rikandjed';
# FTP/SSH stuff
# the upgraded versions are downloaded from your cloud.
# the system is designed to have central support with many aa systems in operation.
# upon boot the latest version in a tar.gz like aa123.tar.gz. is pulled down, if a newer.
# provision for  automatic updates based on time als use these.
# 
use constant FTP_SITE     => 'sompe place in the cloud.com';
use constant FTP_USER     => '';
use constant FTP_PASSWORD => '';
use constant FTP_PORT     => 22;
#

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



