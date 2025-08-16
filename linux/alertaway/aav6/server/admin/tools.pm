package tools;
# Copyright 2011,2012 by James E Dodgen Jr.  All rights reserved. 
use threads::shared;
use Data::Dumper;


use strict;



sub how_long
{
    my ($now, $then) = @_;
    
    if ($then)    
    {
        my $seconds = $now - $then;
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
    return ''; 
}



sub xhow_long
{
    my ($now, $then) = @_;
    
    my $result ="";
    
    if ($then)    
    {
        my $seconds = $now - $then;
        if ($seconds < 60)
        {
            $result = sprintf("%d Sec", $seconds);
        }
        elsif ($seconds < 3600)
        {
           $result = sprintf("%.0f Min", ($seconds / 60)); 
        }
        elsif ($seconds < 86400)
        {
            $result = sprintf("%.0f Hrs", ($seconds / 3600));
        }
        else
        {
            $result = sprintf("%.0f Days", ($seconds / 86400));
        }
    }
    return $result;
}


sub check_ip_address
{
    my ($ip) = @_;
    my $status;  # undef == good
    if (!$ip || $ip eq "")
    {
          # ok to be blank
    } 
    else
    {  
        if( $ip =~ m/^(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)$/ )
        { 
            if($1 <= 255 && $2 <= 255 && $3 <= 255 && $4 <= 255)
            {
                # it is good;
            }
            else
            {
                $status = "One of the octets is out of range, octets must contain a number between 0 and 255";
            }
        }
        else
        {
           $status = "Invalid format for a IP address";
        }
    }
    return $status;
}

sub phone_home
{
  my ($config, $ip_addr, $WorkerBeeQueue, $tracer) = @_;
  # my ($id, $email, $ip_addr, $lan_server_port, $wan_server_port, $WorkerBeeQueue) = @_;

  
  # Create a request
  require  HTTP::Request;
  my $req = HTTP::Request->new(POST => 'http://alertaway.com/cgi-bin/phonehome.pl');
  $req->content_type('application/x-www-form-urlencoded');
  if ($config->{pan_id})
  {
    my $data = sprintf 'pan_id=%s&id=%s&primary_email=%s&ip_addr=%s:%s&wan_port=%s&sh=%s&sl=%s',
       $config->{pan_id},
       $config->{ident}||'',
       $config->{primary_contact},
       $ip_addr, $config->{internal_http_port},
       $config->{external_http_port},
       $config->{sh},$config->{sl};
    $req->content($data);
  }
  else
  {
    $req->content("ping=pong");
  }

  # Pass request to the user agent and get a response back
  require  LWP::UserAgent;
  my $ua = LWP::UserAgent->new;
  $ua->agent("AlertAloneAtHome/0.1");
  my $res = $ua->request($req);

  # Check the outcome of the response
 
  if ($res->is_success) 
  {
      my %form = parse_parms($res->content, $tracer);
      # print "content = [". Dumper \%form. "]\n";
      # printf "latest version = %d\n", $form{version};
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
      $tracer->print("phone_home error = %s", $res->status_line);
  }
  return 0; # problems
}


sub fix_last_time_in
{
	my ($dt, $now) = @_;
    $dt->do("UPDATE wireless_devices SET last_time_in = %s WHERE last_time_in > %s", $now - 60, $now);
    $dt->do("UPDATE problems SET last_report_time = %s WHERE last_report_time > %s", $now - 60, $now);
} 



sub get_config
{
    my ($dt) = @_;
    my ($status, $values) = $dt->get_rec_hashref(<<EOF);
            SELECT problem_reporting_frequency, metric_units,primary_contact,  
            connection_type, external_http_port, static_ip, subnet_mask, gateway, dns1, dns2,
            lw_connection_type, lw_external_http_port, lw_static_ip, lw_subnet_mask, lw_gateway, lw_dns1, lw_dns2,
            watchdog_sleep_time, lost_device_wait, internal_http_port, version_number, upgrade_problem, problem_server_version_number,
            server_version, pan_id, process_start_time, ident, sh, sl, timezone, trace, print_trace
            FROM config
EOF
    $values->{status} = $status;
    ## print Dumper $values;
    return $values;
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
    my ($request, $tracer) = @_;
    my %form;
    $tracer->print("%s", $request);
    my $method;
    if ( $request =~ m'^(GET|POST) /(.*) HTTP/1\.[01]' )
    {
       my $get_or_post = $1;
       my $get_string = $2;
       $tracer->print("get_or_post = %s", $get_or_post);
       my $p;
       if (uc($get_or_post) eq "GET")
       {
           ( $method, $p ) = split( m/\?/, $get_string );
           $method  =~ s/%(..)/pack("C", hex($1))/eg if ($method);
       }
       else ## must be POST
       {
           $method = $get_string;
           $method  =~ s/%(..)/pack("C", hex($1))/eg;
           $request =~ m|\n(.*)$|;
           $p = $1;
          $tracer->print("post_string = [%s]", $p);
       }
       $tracer->print(" method = [%s]", $method) if ($method);
       if ($p)
       {
           %form = parse_parms($p, $tracer);
       }
    }
    # print Dumper \%form;
    return ($method, %form);
    
}

sub parse_parms
{
    my %form;
    my ($p, $tracer) = @_;
    my @parms = split( /&/, $p );
    
    foreach my $parm (@parms)
    {
        my ( $name, $value ) = split( /=/, $parm );

        $tracer->print("parse_parms [%s] =  [%s]", $name, $value||"");
        if ( !defined $value )
        {
            $value = "";
        }
        $value =~ tr/+/ /;
        $value =~ s/%(..)/pack("C", hex($1))/eg;
        $name  =~ s/%(..)/pack("C", hex($1))/eg;
        if ($form{$name})
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
     # printf "thermistor raw = %d mv = %0.2f \n", $value, $mv;
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
    # printf "TMP36 raw=%d, mv=%0.0f, c=%0.0f\n", $value, $mv, $c;
    return  $c;
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
    #printf "TMP36 raw=%d, mv=%0.0f, f=%0.0f\n", $value, $mv, $f;
    return $f;
}

sub convert_to_volts
{
    my ($raw) = @_;
    ## printf( "volts = %.3f\n", $raw / 853.33333 );

    return sprintf( "%.2f", $raw / 853.33333 );
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

sub system_string
{
	my ($ident, $addr_low) = @_;
	return trim($ident).sprintf ("(System ID-%0X)", $addr_low);
	
}

sub location_string
{
	my ($location, $addr_low) = @_;
	$location = trim($location);
	if ($location eq '' ||  $location eq 'UNK')
    {
				 $location = 'Device ID-'.substr(sprintf ("%0X", $addr_low), -4);
    }
    return $location;
}



# check_network_health();
1;
