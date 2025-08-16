#!/usr/bin/perl
# Copyright 2011-2018 by James E Dodgen Jr.  All rights reserved.
use lib ('.', "./admin");
# use Storable;
#use Data::Dumper;
use Secure;  # CGI::Auth;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use strict;
my $form = new CGI;
use DBI;
use DBTOOLS;

my $pan_id = $form->param("pan_id");
my $hex_pan_id = sprintf("%x", $pan_id);

###  all these are from the sftp'ed filelocated in the input directory. they are in Dumper format ###
#my $id = $form->param("id");
#my $ip_addr = $form->param("ip_addr");
#my $primary_email = $form->param("primary_email");
#my $logmsg = $form->param("logmsg");
#my $logtime = $form->param("logtime");
#my $sh =  $form->param("sh");
#my $sl =  $form->param("sl");
#my $network = $form->param("network");

my $ftp_pgms = '/home/alerta/';
my $ftp_input = '/home/alerta/';
my $ftp_output = '/home/alerta/';
my $db_name = "/home/alerta/main.db";

my $useMD5 = 1;

my $current_remote_ip_address = $ENV{REMOTE_ADDR};
  #my %h = (a => 0, b => 2);
  #Storable::nstore \%h, $ftp_input.'input'.$pan_id;
my $msg='';
if (! $pan_id)
{
   $msg  .= "status=error id not passed in&";
}
else
{
   my $now = time;
   my $input_file_path = $ftp_input.'input'.$pan_id;
   my $output_file_path = $ftp_input.'output'.$pan_id;
   $msg .= "time=".$now."&input_path=[".$input_file_path.']';

   if (-r $input_file_path) # file exists
   {
       $msg .= "&input exists=found";
       open (FH, '<', $input_file_path);
       binmode FH;
       my $raw_data = <FH>;
       close (FH);
       my %input_data = parse_parms($raw_data);
       #print Dumper $input_data;
       #printf "b is %s\n", $input_data->{b};
       my %attr = (PrintError => 0,RaiseError => 0, AutoCommit => 1);
       my $new_db = 1;

       my $dbh = DBI->connect("dbi:SQLite:$db_name","","",\%attr);
       if (!defined($dbh))
       {
         croak("could not connect to $db_name");
       }
       my $output='';
       my $dt = new DBTOOLS(dbh => $dbh, trace => 1);
       my ($status, $default_email, $send_me_db, $push_db, $reboot) = $dt->get_rec(
       "SELECT default_email, send_me_db, push_db, reboot FROM systems WHERE pan_id = %s", $hex_pan_id);
       if ($status == 1) # exists so update
       {
           $output = 'default_email='.$default_email;
           if ($send_me_db)
           {
              $output .= '&send_db=1';
           }
           if ($push_db)
           {
              $output .= '&pull_db=1';
           }
           if ($reboot)
           {
              $output .= '&reboot=1';
           }
           $status = $dt->do(<<EOF, $input_data{primary_email}, $input_data{ip_addr}, $current_remote_ip_address, $input_data{sh}, $input_data{sl}, $now, $input_data{id}, $input_data{network}, Secure::encrypt_data($input_data{pass_phrase}), $hex_pan_id);
                UPDATE systems SET primary_email = %s, ip_addr = %s, remote_ip_addr = %s, sh = %s, sl = %s, time = %s, id = %s, network = %s, pass_phrase = %s,
                    send_me_db = 0, push_db = 0, reboot = 0
                WHERE pan_id = %s
                AND pan_id != "admin"
EOF
           if ($status == 0)
           {
              $output .= '&status=update failed';
           }
       }
       else
       {

           $status = $dt->do("INSERT INTO systems (pan_id, id, sh, sl, primary_email, ip_addr, remote_ip_addr, time, pass_phrase) VALUES (%s, %s, %s, %s,%s, %s,%s,%s, %s)",
           $hex_pan_id, $input_data{id}, $input_data{sh}, $input_data{sl}, $input_data{primary_email},
                $input_data{ip_addr}, $current_remote_ip_address, $now,
                Secure::encrypt_data($input_data{pass_phrase}));
       }
       $output .= '&latest_version='.get_latest_version();
       open (FH, '>', $output_file_path);
       binmode FH;
       print FH $output;
       close (FH);
       $msg .= '&output_path='.$output_file_path;
   }
   else
   {
       $msg .= "&input exists=not found";
   }
}

print "Content-type: text/html\n\n$msg";
exit;

sub get_latest_version
{
    my $ver=0;
    opendir(DIR,$ftp_pgms);
    my @curfiles = readdir(DIR);
    closedir(DIR);
    foreach my $n (@curfiles)
    {
      my $nbr = getVersionNbr($n);
      if ($nbr)
      {
        $ver = $nbr if ($nbr > $ver);
      }
    }
    return $ver;
}

sub getVersionNbr
{
  my ($in) = @_;
  my $nbr_out = $1 if ($in =~ /^aa(\d+)\.tar\.gz$/);
  return $nbr_out;
}


sub parse_parms   # from tools.pm
{
    my %form;
    my ($p) = @_;
    my @parms = split( /&/, $p );

    foreach my $parm (@parms)
    {
        my ( $name, $value ) = split( /=/, $parm );
        $value .= '';
         #printf("tools:parse_parms: [%s] =  [%s]\n", $name, $value);

        $value =~ tr/+/ /;
        $value =~ s/%(..)/pack("C", hex($1))/eg;
        $name  =~ s/%(..)/pack("C", hex($1))/eg;
        if (exists $form{$name})
        {
           $form{$name} .= ",".$value;
        }
        else
        {
            $form{$name} = $value;
        }
    }
    return %form;
}

#sub compareVersions
#{
   #my ($a, $b) = @_;
  #my $a_num = getVersionNbr($a);
  #my $b_num = getVersionNbr($b);
  #return -1 if (defined $a_num && !defined $b_num);
  #return  1  if (defined $b_num && !defined $a_num);
  #return $a_num <=> $b_num if (defined $a_num);  ## note returns -1 if a is less than b
  #return lc $a cmp lc $b;
#}
