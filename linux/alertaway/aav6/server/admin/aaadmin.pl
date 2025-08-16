#!/usr/bin/perl
use lib '/var/www/alertaway.com/cgi-bin/admin';
use Secure;  # CGI::Auth;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use strict;
use DBI;
use DBTOOLS;
use Auth;  # testing CGI::Auth
use HTML::Template;
use File::stat;
use Time::localtime;
use http_processor;

use constant MAIN_DB_PATH => '/home/alerta/main.db';
use constant DB_DIR => '/home/alerta/ftp/databases/';

# use constant => $graphviz_html_loc = '/var/www/alertaway.com/';

my %attr = (PrintError => 0,RaiseError => 0,AutoCommit => 1);
my $dbh = DBI->connect("dbi:SQLite:".MAIN_DB_PATH,"","",\%attr);
if (!defined($dbh))
{
  croak("could not connect to ".MAIN_DB_PATH);
}

my $dt = new DBTOOLS(dbh => $dbh, trace => 1);

if ($ARGV[0])
{
    $dt->do("INSERT OR REPLACE INTO systems (pass_phrase, pan_id) VALUES (%s, %s)", Secure::encrypt_data($ARGV[0]), "admin");
    exit;
}

#foreach my $key (sort keys(%ENV)) {
#  print STDERR "$key = $ENV{$key}\n";
#}


my $cgi = new CGI;
printf STDERR "from form u[%s] p[%s] sid[%s]\n", ''.$cgi->param('user'), ''.$cgi->param('pass'), ''.$cgi->param('sessonID');

my $sec = new Secure({
        -dbi            => $dbh,
        #-dbpath         => MAIN_DB_PATH,
        -userquery      => "SELECT pass_phrase FROM systems WHERE pan_id = %s",
        -formaction     => 'aaadmin.pl',
        -check          => {user => ''.$cgi->param('user'), password => ''.$cgi->param('pass'), sessonID => ''.$cgi->param('sessonID')},
        -user           => {display => "USER", min => 8, max =>20},
        -pass           => {display => "PASSWORD", min => 8, max =>35},
        -timeout        => 60 * 4,
        -LoginForm      => \&login_html,
    });


# this is the check for a valid user


my ($pan_id, $sessionID) = $sec->check;
# if we get here we are logged in ok

print STDERR "panid [".$pan_id."]\n";
#my $pan_id = $auth->data('user');
#my $sess_file = $auth->data('sess_file');

if ($pan_id eq 'admin')
{
    do_admin();
}
else
{
   do_a_pan_id($pan_id);
}

sub do_admin
{
    my $state = $cgi->param('admin_state');
    my $msg='';

    $msg .= `which dot`;

    my $new_db = 0;
    if (-f MAIN_DB_PATH)
    {
      $new_db = 1;
    }

    $ENV{TZ} = "America/Los_Angeles";

    my %attr = (PrintError => 0,RaiseError => 0,AutoCommit => 1);
    my $dbh = DBI->connect("dbi:SQLite:".MAIN_DB_PATH,"","",\%attr);
    if (!defined($dbh))
    {
      croak("could not connect to ".MAIN_DB_PATH);
    }

    my $dt = new DBTOOLS(dbh => $dbh, trace => 1);


    if ($new_db == 0)
    {
      $dt->do("CREATE TABLE IF NOT EXISTS systems (sh,sl, primary_email, default_email, id, pan_id, pass_phrase, ip_addr, remote_ip_addr, time, send_me_db, push_db, reboot, network, primary key (pan_id))");
    }

    my $t;

    if ($state =~ /^Delete\:(\d*)$/ )
    {
       my $id = $1;
       my $t = HTML::Template->new_scalar_ref( html(),( xdebug => 1, xstack_debug => 1 ) );
       my ($status, $values) = $dt->get_rec_hashref("select pan_id, sh, sl, id, default_email from systems where pan_id = %s", $id);
       $t->param(deleted_pan_id =>  sprintf( "%X", $values->{pan_id}));
       $t->param(deleted_id =>  $values->{id});
       $t->param(deleted_sh =>  sprintf( "%X", $values->{sh}));
       $t->param(deleted_sl =>  sprintf( "%X", $values->{sl}));
       $t->param(deleted_default_email =>  $values->{default_email});
       $dt->do("delete from systems where pan_id = %s",$id);
    }
    elsif ($state =~ /^Get DB\:(\d*)$/ )
    {
       my $id = $1;
       my $t = HTML::Template->new_scalar_ref( html(),( xdebug => 1, xstack_debug => 1 ) );
       $dt->do("update systems set send_me_db = 1 where pan_id = %s", $id);
    }
    elsif ($state =~ /^GraphViz\:(\d*)$/ )
    {
       my $pan_id = $1;
       my $t = HTML::Template->new_scalar_ref( html(),( xdebug => 1, xstack_debug => 1 ) );
       my ($status,$gv, $id) = $dt->get_rec("select network, id from systems where pan_id = %s", $pan_id);
       $t->param(graphviz => $gv);
    }
    elsif ($state =~ /^Push DB\:(\d*)$/ )
    {
       my $id = $1;
       my $t = HTML::Template->new_scalar_ref( html(),( xdebug => 1, xstack_debug => 1 ) );
       $dt->do("update systems set push_db = 1 where pan_id = %s", $id);
    }
    elsif ($state =~ /^Abort Push\:(\d*)$/ )
    {
       my $id = $1;
       my $t = HTML::Template->new_scalar_ref( html(),( xdebug => 1, xstack_debug => 1 ) );
       $dt->do("update systems set push_db = 0 where pan_id = %s", $id);
    }
    elsif ($state =~ /^Reboot\:(\d*)$/ )
    {
       my $id = $1;
       my $t = HTML::Template->new_scalar_ref( html(),( xdebug => 1, xstack_debug => 1 ) );
       $dt->do("update systems set reboot = 1 where pan_id = %s", $id);
    }
    elsif ($state eq 'Add' )
    {
       my $t = HTML::Template->new_scalar_ref( html(),( xdebug => 1, xstack_debug => 1 ) );
       if ($cgi->param('pan_id'))
       {
           my $email = $dt->trim($cgi->param('default_email'));
           if ($email  =~ /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i)
           {
             my $stat = $dt->do("insert or replace into systems (sh, sl, pan_id, default_email, id) values (%s,%s,%s,%s,%s)",
                #hex($cgi->param('sh')),hex($cgi->param('sl')),hex($cgi->param('pan_id')), $email, $cgi->param('id'));
                hex($cgi->param('sh')),hex($cgi->param('sl')),$cgi->param('pan_id'), $email, $cgi->param('id'));  # now string the hex value
             # $msg .= sprintf "insert Status = %s pan_id = %s", $stat, hex($cgi->param('pan_id'));
           }
           else
           {
               $msg .= " Invalid email address";
               $t->param(deleted_pan_id =>  $cgi->param('pan_id'));
               $t->param(deleted_id =>  $cgi->param('id'));
               $t->param(deleted_sh =>  $cgi->param('sh'));
               $t->param(deleted_sl =>  $cgi->param('sl'));
               $t->param(deleted_default_email =>  $email);
           }
       }
       else
       {
           $msg .= " PAN_ID required";

       }
    }
    if ($state =~ /^Unzip\:(\d*)$/ )
    {
        my $pan_id = $1;
        my ($gzip_db,$real_db) = get_db_names($pan_id);
        system ("gunzip -c $gzip_db > $real_db");
        $msg .= "Unzipped";
    }
    if ($state =~ /^Zip\:(\d*)$/ )
    {
        my $pan_id = $1;
        my ($gzip_db,$real_db) = get_db_names($pan_id);
        if (-f  $real_db)
        {
          system ("gzip -c $real_db > $gzip_db");
          unlink $real_db;
          $msg .= "Zipped";
        }
        else
        {
             $msg .= "Nothing to zip";
        }
    }

    if ($state =~ /^Edit\:(\d*)$/ )
    {
        my $pan_id = $1;
        my ($gzip_db,$real_db) = get_db_names($pan_id);
        # system ("gunzip -c $gzip_db > $real_db");
        if (-f $real_db)
        {
            # $t->param(msg =>  "$real_db exists");
            my $dbh = DBI->connect("dbi:SQLite:$real_db","","",\%attr);
            if (!defined($dbh))
            {
               croak("could not connect to $real_db");
            }
            my $dt_real = new DBTOOLS(dbh => $dbh, trace => 1);
            my %new_form;
            my @names = $cgi->param;
            foreach my $n (@names)
            {
                $new_form{$n} = $cgi->param($n);
            }
            my $method;
            if ( $cgi->param("method"))
            {
                $method=$cgi->param("method");
            }
            else
            {
                $method="main";
            }
            my $t = http_processor::process($method, $dt_real, time, undef, undef, undef, %new_form);
            $t->param(form_action => html::form_action_cgi());

            my $t_menu = HTML::Template->new_scalar_ref( html::cgi_menu(),
                ( xdebug => 1, xstack_debug => 1 ) );
            $t_menu->param(pan_id => $pan_id);
            $t_menu->param(method => $method);
            my $menu_html = $t_menu->output;
            $t->param(menu => $menu_html);
        }
        else
        {
            $msg .= " $real_db not found";
        }
    }
    else
    {
        ## datetime(time, 'unixepoch', 'localtime')

        $t = HTML::Template->new_scalar_ref( html(),( xdebug => 1, xstack_debug => 1 ) );

        my @systems =  $dt->tmpl_loop_query(<<EOF,(qw(pan_id pass_phrase sh sl id ip_addr remote_ip_addr primary_email default_email date send_me_db push_db reboot network)));
        SELECT pan_id, pass_phrase, sh, sl, id, ip_addr, COALESCE(remote_ip_addr,'Unknown'), primary_email, default_email, datetime(time, 'unixepoch', 'localtime'),
        send_me_db, push_db, reboot, network
        FROM systems
EOF
        if (!@systems)
        {
          $msg .= " System table empty ???";
        }
        else
        {
          foreach my $r (@systems)
          {
            #$r->{graphviz_link} = create_graphviz_html($r->{pan_id}, $r->{id}, $r->{network});
            delete $r->{network};
            $r->{sh} = sprintf ("%X",$r->{sh});
            $r->{sl} = sprintf ("%X",$r->{sl});
            my ($gzip_db,$real_db) = get_db_names($r->{pan_id});
            if (-f $gzip_db)
            {
                $r->{gz_exists} = 1;
                $r->{file_date} = ctime(stat($gzip_db)->mtime);
            }
            if (-f $real_db)
            {
                $r->{db_exists} = 1;
            }
            if ($r->{send_me_db})
            {
                $r->{get_scheduled} = "DB get Scheduled";
            }
            delete $r->{send_me_db};
            if ($r->{push_db})
            {
                $r->{push_scheduled} = "DB push Scheduled";
            }
            delete $r->{push_db};
            if ($r->{reboot})
            {
                $r->{reboot_scheduled} = "Reboot Scheduled";
            }
            delete $r->{reboot};
          }
          $t->param(systems => \@systems);
          $t->param(sessonID => $sessionID);
        }
    }
    if ($t->query(name => "msg"))
    {
      $t->param(msg =>  $msg);
    }
    print "Content-Type: text/html\n\n".$t->output;
    exit;
}

sub do_a_pan_id
{
    my ($pan_id) = @_;

    my $t = HTML::Template->new_scalar_ref( html_single(),( xdebug => 1, xstack_debug => 1 ) );
    my ($status, $pan_id, $pass_phrase, $id, $ip_addr, $primary_email, $default_email, $date) =  $dt->get_rec(<<EOF, $pan_id);
    SELECT pan_id, pass_phrase, id, ip_addr,  primary_email, default_email, datetime(time, 'unixepoch', 'localtime')
    FROM systems
    WHERE pan_id = %s
EOF
    if (!$status)
    {
        $t->param(msg =>  "$pan_id not found");
    }
    else
    {
        $t->param(pan_id        => $pan_id);
        $t->param(pass_phrase   => $pass_phrase);
        $t->param(id            => $id);
        $t->param(ip_addr       => $ip_addr);
        $t->param(primary_email => $primary_email);
        $t->param(default_email => $default_email);
        $t->param(date          => $date);
    }
    $t->param(sessonID => $sessionID);

    print "Content-Type: text/html\n\n".$t->output;
    exit;
}


sub urlencode {
    my $s = shift;
    $s =~ s/ /+/g;
    $s =~ s/([^A-Za-z0-9\+-])/sprintf("%%%02X", ord($1))/seg;
    return $s;
}

sub get_db_names
{
    my ($pan_id) = @_;

    return  (DB_DIR.$pan_id.".db.gz",
             DB_DIR.$pan_id.".db");
}

#sub create_graphviz_html
#{
    #my ($pan_id, $title, $gv) = @_;
    #my $t = HTML::Template->new_scalar_ref( graph_html(),( xdebug => 1, xstack_debug => 1 ) );
    #$t->param(title => $title);
    #$gv =~ tr/'/`/;
    #$t->param(graphvizencoded => $gv);
    #my $fn = $pan_id.'.html';
    #open (GV, '>', $graphviz_html_loc.$fn);
    #print GV $t->output;
    #close (GV);
    #return 'http://alertaway.com/'.$fn;
#}

sub html
{
  my $stuff = <<EOF;
<html>
  <head>
  <title>Internal Configuration Server</title>
  <meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
  </head>
  <body  bgcolor=khaki>
  <form  action=/cgi-bin/admin/aaadmin.pl method=POST>
  <center>
  <input type=hidden name=dir value="<tmpl_var name=dir>">
  <table border=1>
    <tr>
      <th><input type=submit name="admin_state" value="Refresh"></th>
      <th>Serial number</th>
      <th>System ID</th>
      <th>Pan ID</th>
      <th>Pass Phrase</th>
      <th>Primary email</th>
      <th>Default email</th>
      <th>Date</th>
      <th>Internal Link<br>External IP addr</th>
      <th>Edit<br>Database</th>
    </tr>
    <tmpl_if name=msg>
      <tr>
      <th align=center colspan=100%><font color=red><tmpl_var name=msg></font></th>
      </tr>
    </tmpl_if>
    <tr>
      <td><input type=submit name="admin_state" value="Add"></td>
      <td> <tmpl_var name=deleted_sh>:<tmpl_var name=deleted_sl>
         <input type=hidden name=sl value="<tmpl_var name=deleted_sl>">
         <input type=hidden name=sh value="<tmpl_var name=deleted_sh>"></td>
      <td> <input type=text readonly name=id value="<tmpl_var name=deleted_id>"></td>
      <td align=right><input type=text size=7 name="pan_id" value="<tmpl_var name=deleted_pan_id>"></td>
      <td></td>
      <td><input type=text size=30 name="default_email" value="<tmpl_var name=deleted_default_email>"></td>
      <td></td>
      <td></td>
      <td></td>
    </tr>

    <tmpl_loop name=systems>
      <tr>
        <td>
         <input type=submit name="admin_state" value="Delete:<tmpl_var name=pan_id>">
         <tmpl_if name=push_scheduled>
             <input type=submit name="admin_state" value="Abort Push:<tmpl_var name=pan_id>">
             <tmpl_var name=push_scheduled>
           <tmpl_else>
             <input type=submit name="admin_state" value="Push DB:<tmpl_var name=pan_id>" onClick="return confirm('Ae you sure you want to download the stored copy?  It will undo any activity since it was uploaded')">
           </tmpl_if>
           <input type=submit name="admin_state" value="Get DB:<tmpl_var name=pan_id>"><br>
           <tmpl_var name=get_scheduled>
           <input type=submit name="admin_state" value="Reboot:<tmpl_var name=pan_id>">
           <input type=submit name="admin_state" value="GraphViz:<tmpl_var name=pan_id>">

           <tmpl_var name=reboot_scheduled>
        </td>
        <td> <tmpl_var name=sh>:<tmpl_var name=sl></td>
        <td align=left><tmpl_var name=id></td>
        <td align=right><tmpl_var name=pan_id></td>
        <td align=left><tmpl_var name=pass_phrase></td>
        <td><tmpl_var name=primary_email></td>
        <td><tmpl_var name=default_email></td>
        <td><tmpl_var name=date></td>
        <td><tmpl_if name=ip_addr>
            <a href="http://<tmpl_var name=ip_addr>:9001">Internal Server at <tmpl_var name=ip_addr></a> </tmpl_if>
            <br>
            Internet IP Address
            <tmpl_var name=remote_ip_addr>
        </td>
        <td align=left>
          <tmpl_if name=gz_exists>
            <input type=submit name="admin_state" value="Unzip:<tmpl_var name=pan_id>"><br>
          </tmpl_if>
          <tmpl_if name=db_exists>
            <input type=submit name="admin_state" value="Edit:<tmpl_var name=pan_id>"><br>
            <input type=submit name="admin_state" value="Zip:<tmpl_var name=pan_id>"><br><tmpl_var name=file_date>
          </tmpl_if>
        </td>
      </tr>
    </tmpl_loop>
    <tmpl_if name=graphviz>
    <tr>
      <td colspan=100% align=left>
      <pre><tmpl_var name=graphviz></pre>
      <!-- <a href="http://graphviz-dev.appspot.com" target=graphvizencoded"_blank">GraphViz Tool</a> -->
      </td>
    </tr>
    </tmpl_if>
  </table>
  </center>
  <input type=hidden name=sessonID value="<tmpl_var name=sessonID>">
  </form>
  </body>

  </html>
EOF
  return \$stuff;
}

sub html_single
{
  my $stuff = <<EOF;
<html>
  <head>
  <title>Your AlertAway</title>
  <meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
  </head>
  <body  bgcolor=khaki>
  <form  action=/cgi-bin/admin/aaadmin.pl method=POST>
  <center>
  <input type=hidden name=dir value="<tmpl_var name=dir>">
  <table border=1>
  <tr><th align=center colspan=100%><font color=red><tmpl_var name=msg></font></th></tr>
    <tr>
        <th><input type=submit name="admin_state" value="Refresh"></th>
        <td></td>
    </tr>
    <tr>
        <th>System ID</th>
        <td align=left><tmpl_var name=id></td>
    </tr>
    <tr>
        <th>Pan ID</th>
        <td align=left><tmpl_var name=pan_id></td>
    </tr>
    <tr>
        <th>Pass Phrase</th>
        <td align=left><tmpl_var name=pass_phrase></td
    </tr>
    <tr>
        <th>Primary email</th>
        <td align=left><tmpl_var name=primary_email></td>
    </tr>
    <tr>
        <th>Default email</th>
        <td align=left><tmpl_var name=default_email></td>
    </tr>
    <tr>
        <th>Last Contact</th>
        <td align=left><tmpl_var name=date></td>
    </tr>
    <tr>
        <th>Your Alertaway Server<br>*You must be on your local LAN</th>
        <td align=left><a href="http://<tmpl_var name=ip_addr>:9001">Your location</a></td>
    </tr>
  </table>
  <input type=hidden name=sessonID value="<tmpl_var name=sessonID>">
  </form>
  </body>
  </html>
EOF
  return \$stuff;
}


sub graph_html
{
    my $stuff =<<EOF;
    <html>
    <head>
    <title><tmpl_var name=title></title>
    <meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
    </head>
    <body  bgcolor=khaki>
    <form action='https://chart.googleapis.com/chart' method='POST' target="_blank">
    <input type='hidden' name='cht' value='gv:circo' />
    <input type='hidden' name='chof' value='gif' />
    <input type='hidden' name='chl' value='<tmpl_var name=graphvizencoded>' />
    <input type="submit" value='View Network' />
    </form>
    </body>
    </html>
EOF

 return \$stuff;
}

use constant HTTPCONTENT         => "Content-Type: text/html\n\n";
sub login_html
{
    my ($parms) = @_;

    #print STDERR "login_html: ".Dumper $parms;

    my $template = HTML::Template->new_scalar_ref(get_logon_html());

    $template->param(
        Message => $parms->{Message},
        pass => $parms->{pass},
        user => $parms->{user},
        usermax => $parms->{usermax},
        passmax => $parms->{passmax},
        Form_Action => $parms->{Form_Action}
    );
    print HTTPCONTENT.$template->output();
}

sub get_logon_html
{

my $logon_html = <<EOF;
<!doctype html public "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
<title>Login</title>
<style type="text/css">
<!--
body { color: black; background-color: white; }
td.fieldname { text-align: right; width: 40%}
td.fieldvalue { text-align: left; width: 60%}
table.main { width: 100%; border: none; }
table.login { width: 40%; background-color: #E4E4E4; border: thin solid black; margin-left: auto; margin-right: auto;}
-->
</style>
</head>

<body OnLoad="document.forms[0].elements[0].focus();">
<table class="main">
    <tr><td style="background: #CCCCCC; text-align: center; font-family:Tahoma ;">
            <h1>AlertAway</h1>
    </td></tr>
    <tr><td style="text-align: center">
            <h3>Please Log In</h3>
            <p>
                <!-- TMPL_VAR NAME=Message -->
            </p>
    </td></tr>
    <tr><td style="text-align: center">
        <form method="post" action="<TMPL_VAR Name=Form_Action>">
            <table class="login" style="text-align: center">
                <tr>
                    <td class="fieldname">
                        <p><!-- TMPL_VAR NAME=user -->:</p>
                    </td>
                    <td class="fieldvalue">
                        <input type="text" name="user", size=<!-- TMPL_VAR NAME=usermax -->>
                    </td>
                </tr>
                <tr>
                    <td class="fieldname">
                        <p><!-- TMPL_VAR NAME=pass -->:</p>
                    </td>
                    <td class="fieldvalue">
                        <input type="text" name="pass", size=<!-- TMPL_VAR NAME=passmax -->>
                    </td>
                </tr>
            </table>
            <input type=submit name="Login" value="Login">
        </form>
    </td></tr>
</table>
</body>
</html>

EOF

return \$logon_html;
}

