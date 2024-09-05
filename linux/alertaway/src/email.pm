package email;
# Copyright 2011, 2015, 2020, 2021, 2022 by James E Dodgen Jr.  All rights reserved.

## Sending email with attachments is a little trickier since we have to construct multi-part messages.
## The Net::SMTP::Multipart module provides a wrapper around Net::SMTP (but not Net::SMTP::SSL)
## to support attachments, but I don't like the syntax it requires and lack of MIME types guessing so
## I extracted the core logic from that module into the example below:
# use Net::SMTP::SSL;
use Net::SMTP; #::SSL;
use POSIX ":signal_h";
use MIME::Base64 qw(encode_base64);
use File::Spec;
use LWP::MediaTypes;
use Carp;
use Data::Dumper;
use strict;
use html;
use cfg;
use filterPrint;
#use constant DBG => 0;
my $fp = filterPrint->new();

use tools;

use constant IN_RANGE => 1;
use constant OUT_OF_RANGE => 0;
use constant UNKNOWN => -1;

my @bchrs;
my $bi=0;
foreach my $bn (48..57,65..90,97..122)
{
    $bchrs[$bi++] = chr($bn);
}

sub task
{
    my ($trace_in) = @_;
    my $WorkerBeeQueue = QueueManager::WorkerBeeQueue();
    my $XbeeSendQueue = QueueManager::XbeeSendQueue();
    my $EmailQueue = QueueManager::EmailQueue({reader => 1});
    my $dt = db::open(cfg::DBNAME);
    $dt->do("UPDATE alerts SET last_range_state = %s", UNKNOWN);
    $dt->do("UPDATE sensor SET last_range_state = %s", UNKNOWN);
    load_any_alerts($dt);
    while (1)
    {
        my $send = $EmailQueue->dequeue;
        #print "email::task ",Dumper $send;
        DBG&&$fp->prt("procesing cmd [%s]", $send->{cmd});
        #$WorkerBeeQueue->enqueue({request => "LOG", fmt => "email:task: processing cmd [%s]", parms => [$send->{cmd}]}) if ($send->{cmd} ne "sensor_check");
        if ($send->{cmd} eq 'simple')
        {
            simple_send($WorkerBeeQueue, $send);
        }
        elsif ($send->{cmd} eq 'to_primary')
        {
            to_primary($dt, $WorkerBeeQueue, $XbeeSendQueue,
                  $send->{subject}, $send->{msg}, $send->{ah}, $send->{al});
        }
        elsif ($send->{cmd} eq 'sensor_check')
        {
            sensor_check($dt, $WorkerBeeQueue, $XbeeSendQueue, $send->{ah}, $send->{al}, $send->{port},
                $send->{in_value}, $send->{current_value}, $send->{event_time});
        }
        elsif ($send->{cmd} eq 'reminder_check')
        {
            reminder_check($dt, $WorkerBeeQueue, $XbeeSendQueue);
        }
        elsif ($send->{cmd} eq 'refresh')
        {
            load_any_alerts($dt);
        }
        else
        {
            DBG&&$fp->prt("unknown cmd [%s]", $send->{cmd});
        }
    }
}

my %any_alerts;
my $any_alerts_sql = "select distinct ah||'-'||al||'-'||port, 1 from alerts";

sub load_any_alerts
{
    my ($dt) = @_;
    DBG&&$fp->prt("loading");
    %any_alerts = $dt->query_row_per_hash($any_alerts_sql);
}

sub email_daily_status
{
    my ($dt, $WorkerBeeQueue, $EmailQueue, $subject, $msg) = @_;
    my $config = tools::get_config($dt);
    my $default_email = $config->{primary_contact};
    $default_email = cfg::DEFAULT_EMAIL if ($default_email eq 'none');
    DBG&&$fp->prt("%s, %s", $subject, Dumper);
    $WorkerBeeQueue->enqueue({request => "LOG", fmt => "email:email_daily_status [%s] sent to [%s]", parms => [$subject,$default_email]});
    my ($one_or_more_missing, @wireless_devices) = http_processor::get_devices_status($dt, time, 1);
    my $t = HTML::Template->new_scalar_ref( html::emailed_status(),
            ( xdebug => 1, xstack_debug => 1 ) );
    $t->param( wireless_devices => \@wireless_devices );
    my @contacts;
    push @contacts, $default_email;
    my $id = tools::system_string($config->{pan_id}, $config->{ident});
    $id .= " PROBLEMS" if ($one_or_more_missing);
    my $ip = ip_tools::get_ip_addr($config, $WorkerBeeQueue);
    my $body = sprintf"Hello \n%s\n\nTo access your server (You must be on your LAN): http://%s:%s \nAt %s, SW Version %d\n\nYour fathfull servant AlertAway",
                 $msg,  $ip,  $config->{internal_http_port}, $id, $config->{version_number};

     my $html_body = tools::clean_html($t->output);
     $EmailQueue->enqueue({cmd => 'simple', subject => "$id, ".$subject, text_body => $body,
         html_body => $html_body, to => \@contacts, event_time => 0});
}


sub to_primary
{
    my ($dt, $WorkerBeeQueue, $XbeeSendQueue, $subject, $msg, $ah, $al) = @_;
    my $config = tools::get_config($dt);
    my $primary_contact = $config->{primary_contact};
    DBG&&$fp->prt("[%s]", $primary_contact);

    my $id = tools::system_string($config->{pan_id}, $config->{ident});
    my $long_id = tools::system_string($config->{pan_id}, $config->{ident}, 1);
    my $ip = ip_tools::get_ip_addr($config, $WorkerBeeQueue);
    my $subject_head = "$id, ";
    my $full_subject = $subject_head.$subject;
     my $body = sprintf "Hello \n%s\n\nTo access your server (You must be on your LAN): http://%s:%s \nAt %s, SW Version %d\n\nYour fathfull servant AlertAway",
                 $msg,  $ip,  $config->{internal_http_port}, $long_id, $config->{version_number};

    my @primary = ($primary_contact);
    simple_send($WorkerBeeQueue, {subject => $full_subject, text_body => $body, to => \@primary});
}

sub cook_value
{
    my ($logic, $in_value, $sensor_adjustment, $metric) = @_;
    my $cooked_value=$in_value;
    my $string='';
    if ($logic eq 'TMP36')
    {
        my $suffix;
        ($cooked_value, $suffix) = tools::cook_tmp36($in_value, $sensor_adjustment||0, $metric);
        $string = ", Temperature ".$cooked_value.$suffix;
    }
    elsif ($logic eq 'VOLT')
    {
        $string = ', '.$in_value.' volts';
    }
    DBG&&$fp->prt("logic[%s] in_value[%s] sensor_adjustment[%s] metric[%s] cooked_value[%s] string[%s]",
          $logic, $in_value, $sensor_adjustment||'none', $metric, $cooked_value, $string);
    return ($cooked_value, $string);
}


sub get_problem_contacts
{
    my ( $dt, $ah, $al, $port, $logic, $in_value, $current_value, $sensor_adjustment, $metric) = @_;
    DBG&&$fp->prt("[%s:%s] logic[%s]", tools::location_string($al), $port||'no port', $logic||'whole device');
    my ($cooked_value, $info) = cook_value($logic, $in_value, $sensor_adjustment, $metric);
    my $hash_key = $ah.'-'.$al.'-'.$port;
    # early out, a quick check for any alerts
    my @raw;
    if (exists($any_alerts{$hash_key}))
    {
        @raw = $dt->tmpl_loop_query(<<EOF,(qw(rowid contact email short threshold_from threshold_to last_date last_range_state)));
        SELECT alerts.rowid, alerts.contact, emails.email_address, emails.requires_short_messages,
        alerts.threshold_from, alerts.threshold_to, alerts.last_date, alerts.last_range_state
        FROM alerts
        JOIN emails ON alerts.contact = emails.contact
        WHERE alerts.ah = $ah
          AND alerts.al =  $al
          AND alerts.port = '$port'
EOF
    }

    # printf STDERR "raw contacts: %s\n", Dumper \@raw;
    # now we filter out those that fall out of the threshold range
    my @cooked;
    foreach my $r (@raw)
    {
        my $from = $r->{threshold_from};
        my $to = $r->{threshold_to};
        delete $r->{threshold_from};
        delete $r->{threshold_to};
        $r->{info} = '';
        my $this_range_state=OUT_OF_RANGE;
        # printf STDERR ("email:get_problem_contacts:  checking states %s <> %s\n", $r->{last_range_state}, $this_is_not_needed_anymore) if DEBUG;
        my $momentary = $logic =~ /^MOMENTARY/;
        if ($momentary)
        {
            $this_range_state=IN_RANGE;  # these only come through on a 1, note not neede to update 'last_range_state'
        }
        else # all but momentarys need last_range_state messed with
        {
            DBG&&$fp->prt("checking [%s:%s}", $logic, $info);
            if ($cooked_value >=  $from && $cooked_value <= $to) # in range?
            {
                $this_range_state=IN_RANGE;
            }
        }
        # now need to check to see if email is needed?

        if ($this_range_state != $r->{last_range_state} || $momentary)# looks like a range change so lets pop out an email AND add to the update string
        {
            $r->{this_range_state} = $this_range_state;
            push @cooked, $r;
            if (! $momentary)
            {
                $dt->do("UPDATE alerts SET last_range_state = %s WHERE rowid = %s", $this_range_state, $r->{rowid});
            }
        }
    }
    return ($info, $cooked_value, @cooked);
}

            ## sensor_on($dt, $send->{ah}, $send->{al}, $send->{port});

sub sensor_check
{
    my ($dt, $WorkerBeeQueue, $XbeeSendQueue, $ah, $al, $port, $in_value, $current_value, $event_time) = @_;

    my ($status, $transition_time, $physical_location, $port_desc, $text_to_display_in_range, $text_to_display_out_of_range, $force, $logic,
         $sensor_adjustment, $sensor_alarm_value_low, $sensor_alarm_value_high) = get_problem_info( $dt,$ah,$al,$port);
    if (!$status)
    {
        $WorkerBeeQueue->enqueue({request => "LOG", fmt => "email::sensor_check: could not get problem_info_for [[%x:%x]%s]", parms => [$ah,$al,$port] });
        return;
    }
    my $config = tools::get_config($dt);
    my $metric = $config->{metric_units};
    DBG&&$fp->prt("sensor_adjustment[%s] metric[%s]", $sensor_adjustment||'none', $metric);
    my $prob_time =localtime($transition_time);
    my $loc =  tools::location_string($physical_location, $al);
    DBG&&$fp->prt("force[%s] sensor_adjustment[%s] sensor_alarm_value_low[%s] sensor_alarm_value_high[%s] metric[%s]",
        $force,  $sensor_adjustment||'none', $sensor_alarm_value_low, $sensor_alarm_value_high, $metric);

    my @contacts;
    my $info = '';
    my $cooked_value = '';

     ($info, $cooked_value, @contacts) = get_problem_contacts($dt, $ah, $al, $port, $logic, $in_value, $current_value, $sensor_adjustment, $metric);
     DBG&&$fp->prt("info [%s] cooked_value[%s]", $info, $cooked_value);

     if (!@contacts)
     {
         if (! $force)
         {
            DBG&&$fp->prt("no contacts found and not forced [%0x:%s]%s", $al, $port, $cooked_value);
            return;
         }
         my $this_range_state;
         # forced so see if out of range if so ignore
         DBG&&$fp->prt("FORCED cooked_value %s <  sensor_alarm_value_low %s || cooked_value %s > sensor_alarm_value_high %s",
            $cooked_value,  $sensor_alarm_value_low, $cooked_value, $sensor_alarm_value_high);
         if ($cooked_value <  $sensor_alarm_value_low || $cooked_value > $sensor_alarm_value_high) # out of range,, which is a problem?
         {
            $this_range_state = OUT_OF_RANGE;
            DBG&&$fp->prt("no contacts but forced and out of range so it is a problem like low voltage [%0x:%s] %s", $al, $port, $cooked_value);
             my $primary_contact = $config->{primary_contact};
             if ($primary_contact eq "none")
             {
                # OK, no configured or default primary contact. we need one set up on alertaway.com.
                $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Problem Emailing, no contacts or primary_contact set , default emailing to alertaway"});
                push @contacts, {email => cfg::DEFAULT_EMAIL, this_range_state => $this_range_state};
             }
             else # we have a default primary contact
             {
                DBG&&$fp->prt("forcing?  force[%s]", $force);
                push @contacts, {email => $primary_contact, this_range_state => $this_range_state};
             }
             my ($stat, $last_range_state) = $dt->get_rec("SELECT last_range_state from sensor where ah = %s and al = %s and port = %s", $ah, $al, $port);

             if ($last_range_state == $this_range_state) # if it has been reported then we ignore
             {
                 # no need to do anything, just exit
                 return;
             }
             $dt->do("UPDATE sensor SET last_range_state = %s WHERE ah = %s AND al = %s AND port = %s", $this_range_state, $ah, $al, $port);

         }
         else
         {
             return;  # nothing to do
         }
    }
    DBG&&$fp->prt("force[%s] info[%s]", $force, $info);
    my $id = tools::system_string($config->{pan_id}, $config->{ident});
    my $long_id = tools::system_string($config->{pan_id}, $config->{ident}, 1);
    my $ip = ip_tools::get_ip_addr($config, $WorkerBeeQueue);

#    my $msg = sprintf "At %s the [%s] located at [%s] has this condition:\"%s\"",
#                $prob_time, $port_desc, $loc, $text_to_display_in_range;
  ### "Hello \n%s\n\nTo access your server (You must be on your LAN): http://%s:%s \nAt %s, SW Version %d\n\nYour fathfull servant AlertAway",$msg.$info,  $ip,  $config->{internal_http_port}, $long_id, $config->{version_number};
    my $subject = sprintf "%s, Hello: at %s the %s  \"", $id, $loc, $port_desc;
    my $body_front = sprintf <<EOF, $long_id, $prob_time, $port_desc, $loc;
Hello
At %s
on %s the [%s] located at [%s] has this condition:
EOF

    my $body_rear = sprintf <<EOF, $ip,  $config->{internal_http_port};

To access your server (You must be on your LAN): http://%s:%s \n
Your fathfull servant AlertAway
EOF

    # two sets of email may need to be sent,
    # one for normal email with more text and attachments the other short for SMS and no attachements at the present.
    # so lets build the lists
    my @short;
    my @long_in_range;
    my @long_out_of_range;
    DBG&&$fp->prt("contacts: %s", tools::remove_nl(Dumper \@contacts));
    foreach my $c (@contacts)
    {
        if ($c->{short} && $c->{short} eq "checked")
        {
            push @short,  $c->{email};
        }
        else
        {
            if ($c->{this_range_state} == IN_RANGE)
            {
                push @long_in_range, $c->{email};
            }
            else
            {
                push @long_out_of_range, $c->{email};
            }

        }
    }
    my @images;
    if (@long_in_range || @long_out_of_range)
    {
        # get the cameras, take the pictures
        my @cameras = get_problem_cameras($dt, $ah, $al, $port);
        if (@cameras)
        {
            my $moton_pid=0;
            #while (1) # CAUSES a wait until process startsl
            #{
              #$moton_pid= processManager::GetPIDByName($dt, 'motion_manager');
              #last if ($moton_pid > 1);
              #printf STDERR ("email:to_contacts: waiting for motion_manager to start\n");
              #sleep(1);
            #}
            my $cfg = tools::get_config($dt);
            my $simpleNVRip = $cfg->{'dvr_ip'};
            my $simpleNVRport = $cfg->{'dvr_port'};
           DBG&&$fp->prt("some pictures needed NOW so getting fresh ones from motion PID = %s", $moton_pid);
            LWP::Simple::get('http://'.$simpleNVRip.':'.$simpleNVRport.'/forcesnampshots');
            foreach my $name (@cameras)
            {
                DBG&&$fp->prt("camera name = %s\n", $name->{name});
                my $image = LWP::Simple::get('http://'.$simpleNVRip.':'.$simpleNVRport.'/camera/'.$name->{name});
                if ($image)
                {
                   push @images, $image;
                }
            }
        }
    }
    # print "images = ", Dumper \@images, "\n" if DEBUG;

    if (@short)
    {
       simple_send($WorkerBeeQueue, { text_body => $subject.$info, to => \@short});
    }
    if (@long_in_range)
    {
       # print Dumper $config if DEBUG;
       simple_send($WorkerBeeQueue, {subject => $subject.$text_to_display_in_range."\"", text_body => $body_front.$text_to_display_in_range.$info.$body_rear, to => \@long_in_range,  attach => \@images});
    }
    if (@long_out_of_range)
    {
       # print Dumper $config if DEBUG;
       simple_send($WorkerBeeQueue, {subject => $subject.$text_to_display_out_of_range."\"", text_body => $body_front.$text_to_display_out_of_range.$info.$body_rear, to => \@long_out_of_range,  attach => \@images});
    }
    # save away stuff for the reminder check

}

sub get_problem_info
{
    my ( $dt, $ah, $al, $port) = @_;

    DBG&&$fp->prt("addr_high[%s] addr_low[%s] port[%s]", $ah, $al, $port);
    my ($status, $transition_time, $physical_location, $port_desc, $text_to_display_out_of_range, $text_to_display_in_range, $force_notification, $logic, $sensor_adjustment, $sensor_alarm_value_low, $sensor_alarm_value_high) =
        $dt->get_rec(<<EOF, $ah, $al, $port);
        SELECT sensor.transition_time, wireless_devices.physical_location, coalesce(sensor.location,port_types.desc),
            coalesce(event_description.text_to_display_out_of_range,'REPORTING an EVENT'), coalesce(event_description.text_to_display_in_range,'CLEARING an EVENT'), port_types.force_notification,
           port_types.logic, sensor.adjustment, sensor.alarm_value_low, sensor.alarm_value_high
        FROM  sensor
        JOIN wireless_devices ON sensor.ah = wireless_devices.ah
            AND sensor.al = wireless_devices.al
        JOIN device_types ON wireless_devices.part_nbr = device_types.part_nbr
        JOIN port_types ON wireless_devices.part_nbr = port_types.part_nbr
            AND sensor.port = port_types.port
            AND port_types.type = "S"
        LEFT JOIN event_description ON port_types.desc = event_description.desc
        WHERE sensor.ah = %s AND sensor.al = %s AND sensor.port = %s
EOF

return ($status, $transition_time, $physical_location, $port_desc, $text_to_display_in_range, $text_to_display_out_of_range, $force_notification, $logic, $sensor_adjustment, $sensor_alarm_value_low, $sensor_alarm_value_high);
}


sub boundry
{
    my $boundry = "";

    my $cnt = 20;
    while ($cnt--)
    {
       $boundry .= $bchrs[int(rand($bi))];
    }
    return $boundry;
}

sub get_problem_cameras
{
    my ( $dt, $ah, $al, $port ) = @_;
    # printf "email:get_problem_cameras: ah %s al %s port %s\n", $ah, $al, $port;
    my $and_port="";
    if ($port)
    {
        $and_port = "AND alert_pictures.port = '$port'";
    }
    return $dt->tmpl_loop_query(<<EOF,(qw(name repeat_count repeat_delay)));
        SELECT alert_pictures.camera_name
        FROM alert_pictures
        WHERE alert_pictures.ah = $ah
           AND alert_pictures.al = $al
          $and_port
EOF

}


sub reminder_check
{
    my ($dt, $WorkerBeeQueue, $XbeeSendQueue) = @_;

    ## tbd
}

sub simple_send
{
    my ($WorkerBeeQueue, $options) = @_;
    DBG&&$fp->prt("to be sent %s", Dumper \$options);
    #printf STDERR "email:simple_send: to be sent %s\n", Dumper \@_ if DEBUG;
    # return;
    # Create arbitrary boundary text used to seperate
    # different parts of the message
    my $check_to="";
    foreach my $recp (@{$options->{to}})
    {
        $check_to .= $recp.",";
    }
    chop $check_to;

    if ($check_to eq 'none')
    {
        print "email:simple_send:  no default email set\n";
        return;
    }

    my $boundry = boundry();
    my $from = $options->{from}||cfg::DEFAULT_FROM;
    my $password = $options->{password}||cfg::DEFAULT_PASSWORD;

    # connect
    my $smtp;
    my $i=10;
    while ($i--)
    {
        if ($smtp = Net::SMTP->new('smtp.gmail.com',
                                  Port => 465,
                                  xDebug => 1,
                                  SSL => 1,))
        {
            last;
        }
        sleep(1);
    }
    if ($i == 0)
    {
        $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Problem Emailing, connect failed [%s]", parms => [$@]}) if ($WorkerBeeQueue);
        printf "email:simple_send: Could not connect to  email server [%s]\n", $@;
        return;
    }

    # Authenticate
    if (!$smtp->auth($from, $password))
    {
        $WorkerBeeQueue->enqueue({request => "LOG", fmt => "Problem Emailing, Authenticate failed %s:%s", parms => [$from, $password]}) if ($WorkerBeeQueue);
        printf  "email:simple_send: Authentication failed! for %s:%s\n", $from, $password ;
        return;
    }

     # Send the header
    $smtp->mail($from . "\n");

    my $to;
    foreach my $recp (@{$options->{to}})
    {
        DBG&&$fp->prt("sending to %s", $recp);
        if ($smtp->to($recp . "\n"))
        {
            $to .= $recp.",";
        }
        else
        {
            DBG&&$fp->prt("email \$smtp->to failed");
        }
    }
     chop $to;
     # print $to;
     $smtp->data();
     $smtp->datasend('From: AlertAway@alertaway.com'."\n");
     $smtp->datasend("To: " . $to . "\n");
     $smtp->datasend("Subject: 🏡 ". $options->{subject} . "\n");
     $smtp->datasend("MIME-Version: 1.0\n");
     $smtp->datasend("Content-Type: multipart/mixed; BOUNDARY=\"$boundry\"\n");


     # Send the body
     if (exists $options->{text_body})
     {
         $smtp->datasend("\n--$boundry\n");
         $smtp->datasend("Content-Type: text/plain\n\n");
         $smtp->datasend($options->{text_body} . "\n\n");
     }

     if (exists $options->{html_body})
     {
         $smtp->datasend("\n--$boundry\n");
         $smtp->datasend("Content-Type:text/html;\n\n");
         $smtp->datasend($options->{html_body} . "\n\n");
     }
     # Send attachments
      if ($options->{attach})
      {
          foreach my $image (@{$options->{attach}})
          {
             DBG&&$fp->prt("image");
             # Get the file name without its directory
             #my ($volume, $dir, $fileName) = File::Spec->splitpath($file);
             # Try and guess the MIME type from the file extension so
             # that the email client doesn't have to
             #my $contentType = guess_media_type($file);
             #if (open(my $fh, "$file"))
             #{
                #binmode($fh);

                # printf  STDERR "before encode lth = %d...\n", length($data);
                $smtp->datasend("--$boundry\n");
                $smtp->datasend("Content-Type: image/jpeg; name=\"\"\n");
                $smtp->datasend("Content-Transfer-Encoding: base64\n");
                $smtp->datasend("Content-Disposition: attachment; =filename=\"\"\n\n");
                #while (sysread ($fh, my $data, 60*57))
                #{
                    $smtp->datasend(MIME::Base64::encode_base64($image));
                #}
                $smtp->datasend("--$boundry\n");
                # print "...after datasend\n";
             #}


          }
      }

     # Quit
     $smtp->datasend("\n--$boundry--\n"); # send boundary end message
     $smtp->datasend("\n");
     if ($smtp->dataend())
     {
        $smtp->quit;
     }
     else
     {
         printf "email:simple_send: ERROR %s\n", $smtp->message();
     }
     DBG&&$fp->prt("email sent");
}


 #Send away! test code
 #my $recp = ['jim@dodgen.us', 'jim.dodgen@gmail.comm'];
 #my $jpgs = ['favicon.ico', '/home/jim/Dropbox/Getting Started.pdf'];
 #my $html = <<EOF;
 #<table border=2>
 #<tr>
 #<td>hello</td>
 #<td>hello</td>
 #<td>hello</td>
 #</tr>
 #<tr>
 #<td>hello</td>
 #<td>hello</td>
 #<td>hello</td>
 #</tr>
#</table>

#EOF

 ####email::send({subject =>'email with attachements', text_body => 'a test', to => $recp, attach => $jpgs});
#simple_send(undef, {subject =>'email with html', text_body => "tell me how this looks, should have a table 3x3 with hello and a border around the cells" ,html_body => $html, to => $recp});

1;
