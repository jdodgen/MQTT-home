#!/usr/bin/perl -I /dev/shm

use strict;
use warnings;

print "Content-type: text/html\n\n";

print "extern program stub<br>";
print "$key --> $ENV{REQUEST_URI}<br>";

