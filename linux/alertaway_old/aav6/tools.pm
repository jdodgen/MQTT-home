package tools;
# Copyright 2011-2020 by James E Dodgen Jr.  All rights reserved.
# use threads::shared;
#use Storable;
use Net::SFTP::Foreign;
use Data::Dumper;
use Digest::MD5 qw( md5_hex) ;
use DBTOOLS;
use strict;
use html_clean;
use POSIX;
use Astro::Sunrise;
use feature 'state';
use filterPrint;
use cfg;

my $fp = filterPrint->new();
#use constant DBG => 1;

sub how_long
{
    my ($now, $then) = @_;
    DBG&&$fp->prt("now = $now then = $then");
    if ($then =~ m/^[0-9]+$/ && $now =~ m/^[0-9]+$/)
    {
        my $seconds = $now - $then;
        # DBG&&$fp->prt("....................................... how_long now = $now then = $then);
        my $day = '';
        my $hour = '';
        my $minute = '';
        my $sec='';
        my $precision=0;
        if ($seconds >= 86400)
        {
            $day = sprintf "%d Days ", int($seconds / 86400);
            $seconds %= 86400;
            $precision++;
        }
        if ($seconds >= 3600)
        {
            $hour = sprintf "%d Hrs ", int($seconds / 3600);
            $seconds %= 3600;
            $precision++;
        }
        if ($seconds >= 60 && $precision < 2)
        {
           $minute = sprintf "%d Min ", int($seconds / 60);
           $seconds %= 60;
           $precision++;
        }
        if ($precision < 2)
        {
            $sec = $seconds.' sec';
        }
        return $day.$hour.$minute.$sec;
    }
    return 'Unknown';
}

sub phone_home
{
    my ($dt, $config, $ip_addr, $system_type, $WorkerBeeQueue) = @_;
    return if (! $config->{pan_id});
    my $file_to_send = '/tmp/input'.$config->{pan_id};
    my $file_to_send_server = 'input'.$config->{pan_id};
    # my $file_to_receive = '/tmp/output'.$config->{pan_id};
    my $file_to_receive_server = 'output'.$config->{pan_id};

    # my ($id, $email, $ip_addr, $lan_server_port, $wan_server_port, $WorkerBeeQueue) = @_;

    # print Dumper $config if DEBUG;
    # Create a request
    if (!$ip_addr)  ## no internet connection?
    {
      DBG&&$fp->prt("Cannot phone home beacuse we have no IP address?");
      return 0;
    }
    # https://alertaway.c13.ixsecure.com/cgi-bin/phonehome.pl
    # http://alertaway.com/cgi-bin/phonehome.pl


    my $sending = 'id='.tools::urlencode($config->{ident} ? $config->{ident}:"Not set yet")
    .'&primary_email='.tools::urlencode($config->{primary_contact} ? $config->{primary_contact}:'no contact')
    .'&ip_addr='.($ip_addr || '?')
    .'&sh='.($config->{sh} || 0)
    .'&sl='.($config->{sl} || 0)
    .'&pass_phrase='.($config->{password} || "none found")
    .'&network='.($dt ? tools::urlencode(tools::grapviz_network($dt)) : '');
    open (FH, '>', $file_to_send);
    binmode FH;
    print FH $sending;
    close (FH);
    my $sftp = connect_to_sftp("tools");
    eval
    {
        my $stat = $sftp->put($file_to_send, $file_to_send_server);
    };
    if ($@)
    {
       DBG&&$fp->prt("ftp put failed [%s]", $@);
       #system "ssh-keygen -R ".FTP_SITE;
       return (0,0);
    }

    require  HTTP::Request;
    my $req = HTTP::Request->new(POST => 'http://alertaway.com/cgi-bin/phonehome.pl');
    $req->content_type('application/x-www-form-urlencoded');
    if ($config->{pan_id})
    {
        # my $data = sprintf 'pan_id=%s&id=%s&primary_email=%s&ip_addr=%s:%s&wan_port=%s&sh=%s&sl=%s&system_type=%s&network=%s',
        my $data = sprintf 'pan_id=%s', $config->{pan_id};
        DBG&&$fp->prt("data %s", $data);
        $req->content($data);
    }
    else
    {
        $req->content("ping=pong");
    }
  # Pass request to the user agent and get a response back
  require  LWP::UserAgent;
  my $ua = LWP::UserAgent->new(ssl_opts => { verify_hostname => 0 });
  $ua->agent("AlertAloneAtHome/0.1");
  $ua->timeout( 10 );
  my $res = $ua->request($req);

  # Check the outcome of the response

  if ($res->is_success)
  {
      my %http_data = parse_parms($res->content);  # not much is returend this way
      # DBG&&$fp->prt("atest version = %d", $form{version});
      my $returned_raw;
      eval
      {
        $returned_raw = $sftp->get($file_to_receive_server);
      };
      if ($@)
      {
          DBG&&$fp->prt("sftp get failed [%s]", $@);
          return (0,0);
      }
      my %form = parse_parms($returned_raw);
      $form{time}=$http_data{time};
      DBG&&$fp->prt("content = [%s] dumped [%s]", $res->content, Dumper(\%form));
      return (1, \%form);
  }
  else
  {
      # this is a problem, could be alertaway.com down or more likely it is
      # a bad route, or gateway, even the users local network or ISP.
      # if it is a DHCP asigned address then we should just ignore the problem,
      # or just re-aquire a new address. This could hurt of the firewall/router/dhcp server is down.
      # so I expect we should just ignore the problem when the address is DHCP assigned.
      #
      # send a message to the watchdog to have the ipaddress checked out and if static lets give it
      # a dynamic address try.
      # we always log the error
      $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Problem contacting AlertAway.com with email = %s and ip = %s message = %s", parms => [$config->{primary_contact}, $ip_addr, $res->status_line]});
      # now send a message to the watchdog to check out the problem, it will decide what to do
      DBG&&$fp->prt("tools:phone_home: error = %s", $res->status_line);
  }
  return (0,0); # problems
}

sub connect_to_sftp
{
    my ($from_who) = @_;
    my $sftp;
    eval
    {
        $sftp = Net::SFTP::Foreign->new(cfg::FTP_SITE,
                        user => cfg::FTP_USER,
                        password => cfg::FTP_PASSWORD,
                        port => cfg::FTP_PORT,
                        more => [-o => 'StrictHostKeyChecking no']);
    };
    if ($@)
    {
       $fp->prt("sftp connect/new problem [%s] called by [%s]", $@, $from_who);
       #system "ssh-keygen -R ".FTP_SITE;
       return;
    }
    DBG&&$fp->prt("using FTP site = %s", cfg::FTP_SITE);
    return $sftp;
}



sub fix_last_time_in
{
    my ($dt, $now) = @_;
    $dt->do("UPDATE wireless_devices SET last_time_in = %s WHERE last_time_in <> 0", $now);
    $dt->do("UPDATE sensor SET last_report_time = 0");
}

my $config_cnt=999;
my $config_sth;
my $config_sql = <<EOF;
SELECT problem_reporting_frequency, metric_units,primary_contact,
connection_type, external_http_port, static_ip, subnet_mask, gateway, dns1, dns2,
lw_connection_type, lw_external_http_port, lw_static_ip, lw_subnet_mask, lw_gateway, lw_dns1, lw_dns2,
watchdog_sleep_time, lost_device_wait, internal_http_port, version_number, upgrade_problem, problem_server_version_number,
server_version, pan_id, pan_id_64, pan_id_16, operating_channel, stack_profile, process_start_time, ident, sh, sl, timezone, password, ip_set_status,
dvr_ip, dvr_port, dvr_user, dvr_password, ethernet_port, latitude, longitude, timezone_offset, wemo_port_base
FROM config
EOF
my $values;

sub get_config
{
    my ($dt,$refresh) = @_;

    if ($config_cnt++ > 10 || (! $values->{pan_id}) || $refresh)
    {
        $config_sth = $dt->query_prepare($config_sql);
        $config_cnt=0;
        my $status;
        ($status, $values) = $dt->get_rec_hashref_execute($config_sth);
        $values->{status} = $status;
        DBG&&$fp->prt("%s\n",  remove_nl(Dumper $values));
    }
    # DBG&&$fp->prt(" ............... get_config %s\n", $values->{process_start_time});
    return $values;
}

sub create_htpasswd
{
    my ($dt) = @_;
    system("/usr/bin/htpasswd -bc /database/htpasswd jed Dairy.squal");
    my $cfg = tools::get_config($dt);
    if ($cfg->{dvr_user} && $cfg->{dvr_password} && trim($cfg->{dvr_user}) gt '' &&  trim($cfg->{dvr_password}) gt '')
    {
        system("/usr/bin/htpasswd -b /database/htpasswd $cfg->{dvr_user} $cfg->{dvr_password}");
    }
}

sub get_restart_reason
{
    my ($dt) = @_;
    my ($status, $code, $descr) = $dt->get_rec("SELECT code, descr FROM reason_started");
    if ($status == 0 || (! defined $descr))
    {
        $code=0;
        $descr="unknown";
    }
    return ($code, $descr);
}



sub parse_http_request
{
    my ($request) = @_;
    my %form;
    DBG&&$fp->prt("%s", $request);
    my $method;
    if ( $request =~ m'^(GET|POST|PUT) /(.*) HTTP/1\.[01]' )
    {
       my $get_or_post = $1;
       my $get_string = $2;
       DBG&&$fp->prt("get_or_post = %s", $get_or_post);
       my $p;
       if (uc($get_or_post) eq "GET" || uc($get_or_post) eq "PUT")
       {
           ($method, $p) = split( m/\?/, $get_string );
           $method  =~ s/%(..)/pack("C", hex($1))/eg if ($method);
       }
       else ## must be POST
       {
           $method = $get_string;
           $method  =~ s/%(..)/pack("C", hex($1))/eg;
           $request =~ m|\n(.*)$|;
           $p = $1;
          DBG&&$fp->prt("post_string = [%s]", $p);
       }
       DBG&&$fp->prt("method = [%s]", $method||'?');
       if ($p)
       {
           %form = parse_parms($p);
       }
    }
    # print Dumper \%form;
    return ($method, %form);

}

sub parse_parms
{
    my %form;
    my ($p) = @_;
    my @parms = split( /&/, $p );

    foreach my $parm (@parms)
    {
        my ( $name, $value ) = split( /=/, $parm );
        $value .= '';
         DBG&&$fp->prt("[%s] = [%s]", $name, $value);

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

sub convert_30k_thermistor
{
     my ($value) = @_;
     my $mv = ($value * 1200) / 1024;
     # DBG&&$fp->prt("raw = %d mv = %0.2f", $value, $mv);
     return $mv;

    my %known_values = { 407 => 21.5, 157 => 0};
}


sub convert_LM335_C
{
    my ($value) = @_;
    return  sprintf "%.2f", ( ( $value / 1023.0 ) * 1.2 * 3.0 * 100 ) - 273.15;
}

sub convert_TMP36_C
{
    my ($value,$adjustment) = @_;
    my $mv = ($value * 1200) / 1024;
    my $c = sprintf "%0.1f", ($mv / 10) - 50 + ($adjustment||0);
    # DBG&&$fp->prt("raw=%d, mv=%0.0f, c=%0.0f", $value, $mv, $c);
    return  $c;
}

sub cook_tmp36
{
    my ($value, $adjustment, $metric_units) = @_;
    my $result;
    if ($metric_units eq "checked")
    {
        return (convert_TMP36_C($value, $adjustment), "C");
    }
    else
    {
        return  (convert_TMP36_F($value, $adjustment), "F");
    }
}

sub convert_TMP36_F_and_C
{
    my ($value, $adjustment, $metric_units) = @_;
    my $result;
    if ($metric_units eq "checked")
    {
        my $c = convert_TMP36_C($value, $adjustment);
        my $f = C_to_F($c);
        $result = sprintf "%0.0f&deg;F/%0.1f&deg;C";
    }
    else
    {
        my $f = convert_TMP36_F($value, $adjustment);
        my $c = F_to_C($f);
        $result = sprintf "%0.0f&deg;F / %0.1f&deg;C", $f, $c;
     }
     return $result;
}

sub C_to_F
{
   my ($value) = @_;
   return ($value * 1.8) + 32;
}



sub F_to_C
{
   my ($value) = @_;
   return ($value - 32) * 5/9;
}

sub convert_TMP36_F
{
    my ($value, $adjustment) = @_;
    my $mv = ($value * 1200) / 1024;
    my $c = ($mv / 10) - 50;
    my $f = sprintf "%0.0f",  ( 1.81 * $c ) + 32 + ($adjustment||0);
    #DBG&&$fp->prt("raw=%d, mv=%0.0f, f=%0.0f", $value, $mv, $f);
    return $f;
}

sub convert_to_volts
{
    my ($firmware_version, $raw) = @_;
    DBG&&$fp->prt("FW version %x raw = %s volts = %.3f", $firmware_version, $raw, $raw / 853.33333 );

    return 3.33 if (!$raw);
    if ($firmware_version && $firmware_version > 0x4000)  # XBee S2C version
    {
       return sprintf( "%.2f", $raw / 1000 );
    }
    # default for older S2 versions
    return sprintf( "%.2f", $raw / 853.33333 );
    #  from S2 manual:  AD(mV) = (A/D reading * 1200mV) / 1023
}

sub trim {
    my ($string) = @_;
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

sub clean_html
{
    my ($text) = @_;
    # DBG&&$fp->prt("called");
    my $h = new html_clean(\$text);
    $h->strip(whitespace => 1, comments => 1);
    return ${$h->data()};
}


sub system_string
{
    my ($addr_low, $ident, $both) = @_;
    if ($ident && $ident ne '')
    {
        if ($both)
        {
            return $ident.sprintf (" (System ID-%0X)", $addr_low);
        }
        return $ident;
    }
    return sprintf ("(System ID-%0X)", $addr_low||0);

}

sub remove_nl
{
    my ($l) = @_;
    $l =~ s/\n//g;
    $l =~ s/\s+/ /g;
    return $l;
}

sub location_string
{
    my ($location, $addr_low) = @_;
    $location = trim($location);
    if (!$addr_low)
    {
        $location = 'ID-'.substr(sprintf ("%0X", $location), -4);
    }
    elsif ($location eq '' ||  $location eq 'UNK')
    {
        $location = 'ID-'.substr(sprintf ("%0X", $addr_low), -4);
    }
    return $location;
}

sub validate_part_nbr  # returns the part number, UNK or undef
{
    my ($dt, $WorkerBeeQueue, $part_nbr_in) = @_;
    my $part_nbr;
    if (!$part_nbr_in) {
        $part_nbr = "UNK";
    } else {
       (my $status, $part_nbr) = $dt->get_rec('select part_nbr from device_types where part_nbr = %s', $part_nbr_in);
       if ($status > -1 ) {
           my $part_number_dump = unpack "H*", $part_nbr_in;
           $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Unknown device part-nbr %s", parms => [$part_number_dump]});
           undef $part_nbr;
       }
    }
    return $part_nbr;
}

sub grapviz_network_old
{
    my ($dt) = @_;
    my $cfg = get_config($dt);

    my %lines;
    my %cell_desc;
    $cell_desc{0} = sprintf '"%X\n%s\nCoordinator"', $cfg->{pan_id}, $cfg->{ident};
    my $text = sprintf "Graph Network {%s [shape=box,color=green,style=filled];\n", $cell_desc{0};
    my @devices =  $dt->tmpl_loop_query(<<EOF,(qw(physical_location part_nbr desc ah al na parent_network_address)));
    select coalesce(physical_location,''),
           coalesce(wireless_devices.part_nbr,'UNKNOWN'), device_types.desc, wireless_devices.ah, wireless_devices.al,
           coalesce(wireless_devices.na,wireless_devices.al),
           coalesce(wireless_devices.parent_network_address,wireless_devices.al)
    from wireless_devices
    join device_types on wireless_devices.part_nbr = device_types.part_nbr
EOF

    my $type;
    foreach my $e (@devices) {

        if ($e->{part_nbr} =~ /^E/) {
            $lines{bigger_on_left($e->{na}, $e->{parent_network_address})} = 1;
            my $label = sprintf '"%X\n%s\n%s"', $e->{na}, $e->{physical_location}, $e->{desc};
            $text .= sprintf "%s %s;\n", $label, "[color=lightblue,style=filled]";
            $cell_desc{$e->{na}} = $label if ($e->{na});
        } elsif ($e->{part_nbr} =~ /^U/) {
            my $label = sprintf '"%X\n%s\n%s"', $e->{na}, $e->{physical_location}, $e->{desc};
            $text .= sprintf "%s %s;\n", $label, "[color=yellow,style=filled]";
            $cell_desc{$e->{na}} = $label if ($e->{na});
        } elsif ($e->{part_nbr} =~ /^R/) {
            my $label = sprintf '"%X\n%s\n%s"', $e->{na}, $e->{physical_location}, $e->{desc};
            $text .= sprintf "%s %s;\n", $label, "[color=yellow,style=filled]";
            $cell_desc{$e->{na}} = $label if ($e->{na});
        } else {
            $e->{physical_location} = '';
            my $label = sprintf '"NOT OURS\n%0X:%0X"', $e->{ah}, $e->{al};
            $text .= sprintf "%s %s;\n", $label, "[color=red,style=filled]";
        }
    }

    my @routers =  $dt->tmpl_loop_query(<<EOF,(qw(physical_location part_nbr ah al na dest_addr next_hop)));
    select wireless_devices.physical_location, wireless_devices.part_nbr, routing.ah, routing.al, routing.na, routing.dest_addr, routing.next_hop
    from routing
    join wireless_devices on routing.ah = wireless_devices.ah
         and routing.al = wireless_devices.al
EOF

    foreach my $r (@routers) {
        DBG&&$fp->prt("routers %s", Dumper \$r);
        if ($r->{dest_addr} == $r->{next_hop}) {
            $lines{bigger_on_left($r->{na}, $r->{dest_addr})} = 1;
        }
        else {
            $lines{bigger_on_left($r->{next_hop}, $r->{dest_addr})} = 1;
            $lines{bigger_on_left($r->{na}, $r->{next_hop})} = 1;
        }
    }
    foreach my $i(keys %lines) {
        my ($l, $r) = split ',', $i;
        $text .= sprintf "%s -- %s;\n", $cell_desc{$l}||$l, $cell_desc{$r}||$r;
    }
    DBG&&$fp->prt("%s", $text);
    return $text."}\n";
}


sub grapviz_network
{
    my ($dt) = @_;
    my $cfg = get_config($dt);
    return if (!$cfg->{pan_id});
    # on occasion a device changes its network_address, so we toss the old ones
    $dt->do(<<EOF);
    DELETE FROM routing WHERE na NOT IN (SELECT na FROM wireless_devices UNION SELECT 0)
                                 OR dest_addr NOT IN (SELECT na FROM wireless_devices UNION SELECT 0)
                                 OR next_hop  NOT IN (SELECT na FROM wireless_devices UNION SELECT 0)
EOF
    my %lines;

    my $text = sprintf "Graph Network {\n0 [shape=box,color=green,style=filled,label=%s];\n", sprintf '"PAN:%X\n%s\nCoordinator"', $cfg->{pan_id}, $cfg->{ident}||"unknown";
    $text .= "I [shape=hexagon,color=wheat,style=filled,label=Internet];\n0 -- I;\n";
    my @devices =  $dt->tmpl_loop_query(<<EOF,(qw(physical_location part_nbr desc ah al na parent_network_address)));
    select coalesce(physical_location,''),
           coalesce(wireless_devices.part_nbr,'UNKNOWN'), device_types.desc, wireless_devices.ah, wireless_devices.al,
           coalesce(wireless_devices.na,wireless_devices.al),
           coalesce(wireless_devices.parent_network_address,wireless_devices.al)
    from wireless_devices
    join device_types on wireless_devices.part_nbr = device_types.part_nbr
EOF

    my $type;
    foreach my $e (@devices) {
        my $color="red";
        if ($e->{part_nbr} =~ /^E/) {
            if ($e->{na} != $e->{parent_network_address}) {
            $lines{bigger_on_left($e->{na}, $e->{parent_network_address})} = 1;
            }
            $color='lightblue';
        } elsif ($e->{part_nbr} =~ /^U/) {
            $color='lightgray';
        } elsif ($e->{part_nbr} =~ /^R/) {
            $color='yellow';
        } else {
            $color="red";
        }
        $text .= sprintf "%s [color=%s,style=filled,label=%s];\n",
                    $e->{na}, $color, sprintf '"ADDR:%X\n%s\n%s"', $e->{na}, $e->{physical_location}||"UNKNOWN", uc($e->{desc}||"");
    }

    my @routers =  $dt->tmpl_loop_query(<<EOF,(qw(physical_location part_nbr ah al na dest_addr next_hop)));
    select wireless_devices.physical_location, wireless_devices.part_nbr, routing.ah, routing.al, routing.na, routing.dest_addr, routing.next_hop
    from routing
    join wireless_devices on routing.ah = wireless_devices.ah
         and routing.al = wireless_devices.al
EOF

    foreach my $r (@routers) {
        # print Dumper $r, "\n";
        if ($r->{dest_addr} == $r->{next_hop}) {
            $lines{bigger_on_left($r->{na}, $r->{dest_addr})} = 1;
        }
        else {
            $lines{bigger_on_left($r->{next_hop}, $r->{dest_addr})} = 1;
            $lines{bigger_on_left($r->{na}, $r->{next_hop})} = 1;
        }
    }
    foreach my $i(keys %lines) {
        my ($left, $right) = split ',', $i;
        $text .= sprintf "%s -- %s;\n", $left, $right;
    }
    # DBG&&$fp->prt("text %s",$text);
    return $text."}\n";
}



sub bigger_on_left
{
    my ($a, $b) = @_;
    if ($a > $b) {
        return $a.','.$b;
    }
    return $b.','.$a;
}

sub urlencode {
    my $s = shift;
    $s =~ s/ /+/g;
    $s =~ s/([^A-Za-z0-9\+-])/sprintf("%%%02X", ord($1))/seg;
    return $s;
}

sub urldecode
{
    my $s = shift;
    $s =~ s/\%([A-Fa-f0-9]{2})/pack('C', hex($1))/seg;
    $s =~ s/\+/ /g;
    return $s;
}

sub hexDumper
{
    my ($name, $item, $not_first_time) = @_;
    my $string = '';
    return _hexDumperRecursion($string, $name, $item, $not_first_time);
}


sub _hexDumperRecursion
{
    my ($string, $name, $item,) = @_;
    my $type = ref($item);
    #printf Dumper $item;
    #printf ">>>  [%s] [%s] type [%s]\n", $name, $item, $type;
    if ($type eq 'HASH')
    {
        #print "Processing a HASH [$type]\n";
        foreach my $h (sort (keys (%$item)))
        {

            #printf "processing HASH item key[%s] value[%s] type[%s]\n",  $h, $item->{$h}, ref($item->{$h});
            if (ref($item->{$h}))
            {
                $string = _hexDumperRecursion($string, "$name->$h", $item->{$h});
            }
            else
            {
                 $string = _hexDumperRecursion($string, "$name->$h", \$item->{$h});
            }
        }

    }
    elsif ($type eq 'ARRAY')
    {
        #print "doing array $item\n";
        my $i = 0;
        foreach my $a (@$item)
        {
            #printf "processing array item [$a] %s\n", ref($a);
            if (ref($a))
            {
                 $string = _hexDumperRecursion($string, "$name\@$i", $a);
            }
            else
            {
                 $string = _hexDumperRecursion($string, "$name\@$i", \$a);
            }
            $i++;
        }
    }
    elsif ($type eq "SCALAR")
    {
        if (! defined($$item))
        {
            $string .= sprintf "%s[undef]\n", $name;
        }
        elsif ($$item =~ /^\d+$/)
        {
            $string .= sprintf "%s[%X]\n", $name, $$item;
        }
        elsif ($$item  =~ /^[\x20-\x7E]*$/)
        {
            $string .= sprintf "%s[%s]\n", $name, $$item;
        }
        else
        {
            $string .=  sprintf "%s[%s]\n", $name, unpack( 'H*', $$item);
        }
    }
    else
    {
        $string .= $$item;
    }
    return $string;
}
#my $nothing;
#my $foo = {x=> 456, y=>789, z => "\x00\x05", Array => [1,2,4, $nothing,0, '34','35xx'], headder => {mine=> 'zzz', yours => 'qwert'}, text => "hello world"};
#print hexDumper("", $foo);

sub set_coordinator_configuration {
    my ($XbeeSendQueue, $pan_id_64, $pan_id_16, $operating_channel, $stack_profile) = @_;

    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'ID', value => pack( 'Q>',  int $pan_id_64)});

    # $dt->do("update config set pan_id = %s", $prior_cfg->{pan_id_64});
    # set the mask to current operating_channel
    #my $mask = 1 << ($operating_channel - 0xb);
    #my $operating_channel = pack( 'n',  1 << ($operating_channel - 0xb));
    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'SC', value => pack( 'n',  1 << ($operating_channel - 0xb))});

    #my $stack_profile = pack( 'n',  int $stack_profile);
    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'ZS', value => pack( 'n',  int $stack_profile)});
    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'WR'});

    #my $pan_id_16 = pack( 'n',  int $pan_id_16);
    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'II', value => pack( 'n',  int $pan_id_16)});
    $XbeeSendQueue->enqueue({request => 'XBEE_AT', cmd => 'ID'}); # this causes it to be set in config
}

sub midnight # epoch at last midnight
{
    my ($now) = @_;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now);
    return $now - ($sec + (($min + ($hour * 60)) * 60));
}

sub sunRiseSet
{
    my ($lat,$long) = @_;
    my $tz_offset = (POSIX::mktime(localtime) - POSIX::mktime(+gmtime)) / 60 / 60;
    #printf "tz offset %s\n", $tz_offset;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
    #printf("year[%s] month[%s] day[%s]\n",$year+1900, $mon+1, $mday);

    my ($sunrise, $sunset) = sunrise( { year => $year+1900, month => $mon+1, day => $mday,
                                    lon  => $long, lat   => $lat,
                                    tz   => $tz_offset,    isdst => $isdst } );

    my ($riseHour,$riseMinute) = split /\:/, $sunrise;
    my ($setHour,$setMinute) = split /\:/, $sunset;
    #print "returning  rise $riseHour : $riseMinute, set $setHour : $setMinute \n";
    return ($riseHour,$riseMinute, $setHour,$setMinute);
}

sub seconds_from_midnight
{
    my ($minutes, $hours) = @_;
    return (($minutes + ($hours * 60)) * 60);
}
sub remove_override
{
    my ($dt, $rowid) = @_;
    my $status = $dt->do("UPDATE devices SET override_state = NULL, external_override = NULL WHERE rowid = %s",
            $rowid );
}

sub hash_trace
{
    my %hash;
    my ($str, $debug) = @_;
    if ($debug)
    {
       $hash{DEBUG} = 1;
    }
    else
    {
       $hash{DEBUG} = 0;
    }
    foreach my $al (split /,/, $str)
    {
        $hash{$al} = 1;
    }
    return %hash;
}

sub hashValue {
    my $data = shift ;
    local $Data::Dumper::SortKeys = 1;
    return md5_hex( Dumper($data) ) ;
}

sub DumpString {
    my $s = shift || "";
    my @a = unpack('C*',$s);
    my $o = 0;
    my $i = 0;
    DBG&&$fp->prt("\tb0 b1 b2 b3 b4 b5 b6 b7");
    DBG&&$fp->prt("\t-- -- -- -- -- -- -- --");
    while (@a) {
        my @b = splice @a,0,8;
        my @x = map sprintf("%02x",$_), @b;
        my $c = substr($s,$o,8);
        $c =~ s/[[:^print:]]/ /g;
        DBG&&$fp->prt("w%02d",$i);
        DBG&&$fp->prt(" "x5,join(' ',@x),"");
        $o += 8;
        $i++;
    }
}

sub whocalled  {
    my ($package,$filename, $line, $subroutine) = caller(1);
    my $tail = "";
    my $depth=3;
    while (1)
    {
        my ($package,$filename, $line, $subroutine) = caller($depth++);
        last if (!$subroutine);
        $tail .= ">".$subroutine."@".$line;
    }
    my $called_by1 = (caller(2))[3];
    my $from = $called_by1?$called_by1:$package; # top check
    return $subroutine.">".$from."@".$line.$tail;
}

sub trim { my $s = shift; $s =~ s/^\s+|\s+$//g; return $s };
sub ltrim { my $s = shift; $s =~ s/^\s+//;       return $s };
sub rtrim { my $s = shift; $s =~ s/\s+$//;       return $s };

sub trim_block
{
    my ($block) = @_;
    my $new_block = '';
    foreach  my $line (split /\n/, $block)
    {
       $new_block .= trim($line)."\n";
    }
    return $new_block;
}





#
#
# test code
#
#
#use db;
#my $dt = db::open(cfg::DBNAME);
#printf "next change time 8 = %s\n", scalar localtime(get_next_timed_event_change($dt,time,8));

1;
