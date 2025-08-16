package DBTOOLS;
# Copyright 2011 by James E Dodgen Jr.  All rights reserved. 
use strict;

require Exporter;
our ( @ISA, @EXPORT_OK, %EXPORT_TAGS );
use Carp qw(cluck);

# dbi wrapper for use with HTML::Template 
# property of Jim Dodgen
#

sub new
{
  my $pkg = shift;
  my $self; { my %hash; $self = bless(\%hash, $pkg); }

  for (my $x = 0; $x <= $#_; $x += 2)
  {
    defined($_[($x + 1)]) or croak("DBTOOLS::new() called with odd number of option parameters - should be of the form option => value");
    $self->{lc($_[$x])} = $_[($x + 1)];
    # print "loading hash lc($_[$x]) = $_[($x + 1)]\n";
  }
  #print "new called \n";
  return $self;
}


sub get_comments
{
   my ($self) = @_;
   if (exists($self->{login_comments}))
   {
     return "DBTOOLS_START\n".$self->{login_comments}."DBTOOLS_END\n";
   }
   return "";
}

sub put_comments
{
   my ($self, $string) = @_;


   $self->{login_comments}.=$string."\n" if (exists($self->{trace}));
}

sub get_rec_hashref
{
   my ($self, $rsql, @parms) = @_;
   chomp $rsql;
   $rsql=$self->trim($rsql);
   my $sql;
   if (@parms)
   {
      for (my $i = 0; $i <= $#parms; $i++)
      {
        # $self->{login_comments} .= "[$i]\n" if (exists($self->{trace}));
        $parms[$i] = $self->{dbh}->quote($parms[$i]);
        $self->{login_comments} .= "parm=".$parms[$i]."\n" if (exists($self->{trace}));
      }
      $sql = sprintf($rsql, @parms);
   }
   else
   {
      $sql = $rsql;
   }
   $self->{login_comments} .= "get_rec_hashref [$sql]\n" if (exists($self->{trace}));
   # print "$sql\n";
   ###   my $sth = $dbh->prepare("SELECT * FROM mytable");
   my $results = $self->{dbh}->selectrow_hashref($sql);
   
   # cluck if (!@results);
   $self->{login_comments}.="get_rec_hashref selectrow_array col returned [$sql]\n" if (exists($self->{trace}));
   if (!$results && defined($self->{dbh}->err))   # this is an sql error
   {
      $self->{login_comments} .= "get_rec_hashref selectrow_array failed".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return 0, \{error => $self->{dbh}->errstr};
   }
   elsif (!$results) # this is nothing returned from query
   {
      $self->{login_comments} .= "get_rec_hashref returned zero records\n" if (exists($self->{trace}));
      return 0, \{error =>  "nothing found"};
   }
   # print "[$self->{login_comments}]\n";
   return 1, $results;
}


sub get_rec
{
   my ($self, $rsql, @parms) = @_;
   chomp $rsql;
   $rsql=$self->trim($rsql);
   my $sql;
   if (@parms)
   {
      for (my $i = 0; $i <= $#parms; $i++)
      {
        # $self->{login_comments} .= "[$i]\n" if (exists($self->{trace}));
        $parms[$i] = $self->{dbh}->quote($parms[$i]);
        $self->{login_comments} .= "parm=".$parms[$i]."\n" if (exists($self->{trace}));
      }
      $sql = sprintf($rsql, @parms);
   }
   else
   {
      $sql = $rsql;
   }
   $self->{login_comments} .= "get_rec [$sql]\n" if (exists($self->{trace}));
   ## print "$sql\n";
   ###   my $sth = $dbh->prepare("SELECT * FROM mytable");
   my @results = $self->{dbh}->selectrow_array($sql);  
   # cluck if (!@results);
   $self->{login_comments}.="get_rec selectrow_array col returned = $#results [$sql]\n" if (exists($self->{trace}));
   if ($#results == 0 && defined($self->{dbh}->err))   # this is an sql error
   {
      $self->{login_comments} .= "get_rec selectrow_array failed $results[0]".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return (0, $self->{dbh}->errstr);
   }
   elsif ($#results < 0) # this is nothing returned from query
   {
      $self->{login_comments} .= "get_rec returned zero records\n" if (exists($self->{trace}));
      return (0, "nothing found");
   }
   # print "[$self->{login_comments}]\n";
   return (1, @results);
}

sub do_a_block
{
    my ($self, $block) = @_;
    $block =~ tr/\n/ /;
    my $errors=0;
    my @lines = split ";", $block;
    foreach my $line (@lines)
    {
       $errors += $self->do($line);
    }
    
}

sub do
{
   my ($self, $rsql, @parms) = @_;
   chomp $rsql;
   $rsql=$self->trim($rsql);
   my $sql;
   if (@parms)
   {
      for (my $i = 0; $i <= $#parms; $i++)
      {
        if(!defined $parms[$i] or $parms[$i] eq "")
        {
           $parms[$i]="NULL";
        }
        else
        {
          $parms[$i] = $self->{dbh}->quote($parms[$i]);
          $self->{login_comments} .= "parm=".$parms[$i]."\n" if (exists($self->{trace}));
        }
      }
      #  all the nulls are ro make sure we cover all trailing %s in the printf string
      $sql = sprintf($rsql, (@parms, ("NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL")));
   }
   else
   {
      $sql = $rsql;
   }

   $self->{login_comments} .= "do [".$sql."]\n" if (exists($self->{trace}));
   for (my $i = 0; $i < 10; $i++)
   { 
      my $stat = $self->{dbh}->do($sql);
      if (!$stat)
      {
         if ($self->{dbh}->err == 5) # locked
         {
             sleep(1);  # just a little wait for it to unlock
         }
         else
         { 
            warn "do failed\n$sql\nUnable execute ".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
            return 0;
         }
      }
      else
      {
        return 1;
      }      
   }
   return 0;
}

sub query_to_hash
{
    # retreves a single row into a hash keyed by column id
    my ($self, $rsql, @parms) = @_;
    chomp $rsql;
    $rsql=$self->trim($rsql);
    my $sql;
    if (@parms)
   {
      for (my $i = 0; $i <= $#parms; $i++)
      {
        if(!exists $parms[$i])
        {
           $parms[$i]="NULL";
        }
        else
        {
          $parms[$i] = $self->{dbh}->quote($parms[$i]);
          $self->{login_comments} .= "parm=".$parms[$i]."\n" if (exists($self->{trace}));
        }
      }
      #  all the nulls are ro make sure we cover all trailing %s in the printf string
      $sql = sprintf($rsql, (@parms, ("NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL")));
   }
   else
   {
      $sql = $rsql;
   }
    $self->{login_comments} .= "query_to_hash [$sql]\n" if (exists($self->{trace}));
    my $sth = $self->{dbh}->prepare($sql);
    if (!defined($sth))
    {
      $self->{login_comments} .= "query_to_hash Unable to prepare [$sql] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return;
    }
    my $stat = $sth->execute;
    if (!defined($stat))
    {
      $self->{login_comments}  .= "query_to_hash Unable execute [$sql] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return;
    }
    my %hash;
    while( my ($l,$v) = $sth->fetchrow_array )
    {
       $hash{$l} = $v;
    }
    $sth->finish;
    return \%hash;
}

sub tmpl_loop_query
{
    # name is table name
    my ($self, $search, @labels) = @_;
    chomp $search;
    $search=$self->trim($search);
    my @lov;
    $self->{login_comments} .= "tmpl_loop_query [$search]\n" if (exists($self->{trace}));
    my $sth = $self->{dbh}->prepare($search);
    if (!defined($sth))
    {
      $self->{login_comments} .= "tmpl_loop_query Unable to prepare [$search] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return;
    }
    my $stat = $sth->execute;
    if (!defined($stat))
    {
      $self->{login_comments}  .= "tmpl_loop_query Unable execute [$search] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return;
    }

    while( my @row = $sth->fetchrow_array )
    {
       my %fld_set;
       foreach my $lbl (@labels)
       {
           $fld_set{$lbl}= shift @row;
       }
       push (@lov, \%fld_set);
    }
    $sth->finish;
    return @lov;
}

sub query_to_array_of_hash
{
    # name is table name, first returned field is hash key, the rest go in by name list
    my ($self, $search) = @_;
    chomp $search;
    $search=$self->trim($search);
    
    $self->{login_comments} .= "query_to_array_of_hash [$search]\n" if (exists($self->{trace}));
    my $sth = $self->{dbh}->prepare($search);
    if (!defined($sth))
    {
      $self->{login_comments} .= "query_to_array_of_hash Unable to prepare [$search] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return;
    }
    my $stat = $sth->execute;
    if (!defined($stat))
    {
      $self->{login_comments}  .= "query_to array_of_hash Unable execute [$search] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return;
    }
    my $tbl_ary_ref = $sth->fetchall_arrayref({});
    $sth->finish;
    return $tbl_ary_ref;
}


sub query_to_array
{
    # name is table name
    my ($self, $search, $skip, $limit) = @_;
    chomp $search;
    $search=$self->trim($search);
    if (!defined($limit))
    {
    	$limit=100;
    }	
    my @csv_lines=();
    $self->{login_comments} .= "query_to_array [$search]\n" if (exists($self->{trace}));
    my $sth = $self->{dbh}->prepare($search);
    if (!defined($sth))
    {
      $self->{login_comments} .= "query_to_array Unable to prepare [$search] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return (-1, ($self->{dbh}->err,$self->{dbh}->errstr));
    }
    my $stat = $sth->execute;
    if (!defined($stat))
    {
      $self->{login_comments}  .= "query_to_array Unable execute [$search] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      $sth->finish;
      return (-1, ($self->{dbh}->err,$self->{dbh}->errstr));
    }
    while( my @row = $sth->fetchrow_array)
    {
        push(@csv_lines, \@row); # array of arrays
        $limit--;
        if ($limit < 1)
        {
            last;
        }
    }
    $sth->finish;
    return (1, @csv_lines);
}

sub tmpl_loop_select
{
    # name is table name
    my ($self, $table_name, $where) = @_;
    my @lov;
    if (!defined($where))
    {
    	$where="";
    }
    my $search="SELECT $table_name.id, $table_name FROM $table_name $where ORDER BY $table_name";
    $self->{login_comments} .= "tmpl_loop_select [$search]\n" if (exists($self->{trace}));
    my $sth = $self->{dbh}->prepare($search);
    if (!defined($sth))
    {
      $self->{login_comments} .= "tmpl_loop_select Unable to prepare [$search] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
      return;
    }
    my $stat = $sth->execute;
    if (!defined($stat))
    {
      $self->{login_comments} .= "tmpl_loop_select Unable execute [$search] SELECT:".$self->{dbh}->err.", ".$self->{dbh}->errstr."\n";
    }
    my ($id, $key);
    $sth->bind_columns( \$id, \$key);
    while( $sth->fetch() )
    {
      push (@lov, {value => $id, text => $key});
    }
    $sth->finish;
    return @lov;
}

sub quote
{
   my ($self, $thing) = @_;
   return $self->{dbh}->quote($thing);
}

sub trim {
    my ($self, $string) = @_;
    if (!defined($string))
    {
      return "";
    }
    $string  =~  s/^\s+//;
    $string  =~  s/\s+$//;
    if ($string eq "")
    {
        return "";
    }
    return $string;
}

sub trim_quote {
    my ($self, $string) = @_;
    if (!defined($string))
    {
      return "null";
    }
    $string  =~  s/^\s+//;
    $string  =~  s/\s+$//;
    if ($string eq "")
    {
        return "null";
    }
    return $self->{dbh}->quote($string);
}

# print "passed through package\n";
1;
