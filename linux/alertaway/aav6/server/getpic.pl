#!/usr/bin/perl


use CGI;
use CGI::Carp qw(fatalsToBrowser);
use strict;
my $form = new CGI;
use DBI;
use DBTOOLS;
use LWP::Simple;

my $pan_id = '5720'; #hex($form->param('id'));  #1658
my $type = 'camera'; #$form->param('type'); #camera
my $device = 'driveway'; #$form->param('device'); #frontdoor

my $db_name = "main.db";

my %attr = (PrintError => 0,RaiseError => 0, AutoCommit => 1);
my $dbh = DBI->connect("dbi:SQLite:$db_name","","",\%attr);
if (!defined($dbh))
{
	croak("could not connect to $db_name");
}
my $dt = new DBTOOLS(dbh => $dbh, trace => 1);
my ($status, $remote_ip_addr) = $dt->get_rec(
   "SELECT remote_ip_addr FROM systems WHERE pan_id = %s", $pan_id);  #64.30.195.129
if ($status == 1)
{
	my $request = "http://".$remote_ip_addr.":9000/${type}/${device}";
	my $content = get($request);
	if ($type eq "camera")
	{
		print "Content-type: image/jpeg\n\n$content";
	}
	else
	{
		print "Content-type: text/html\n\n$content";
	}
}
else
{
	print "Content-type: text/html\n\nCould not find $pan_id";
}

