#!/usr/bin/perl

use lib ".";
use Secure;
use constant MAIN_DB_PATH => '/home/alerta/main.db';
use CGI;
use Data::Dumper;

my $dbh = DBI->connect("dbi:SQLite:".MAIN_DB_PATH,"","",\%attr);
if (!defined($dbh))
{
  croak("could not connect to ".MAIN_DB_PATH);
}
my $cgi = new CGI;
printf STDERR "from form u[%s] p[%s] sid[%s]\n", ''.$cgi->param('user'), ''.$cgi->param('pass'), ''.$cgi->param('sessonID');

my $sec = new Secure({
        #-dbi            => $dbh,
        -dbpath         => MAIN_DB_PATH,
        -userquery      => "SELECT pass_phrase FROM systems WHERE pan_id = %s",
        -formaction     => "test.pl",
        -check          => {user => ''.$cgi->param('user'), password => ''.$cgi->param('pass'), sessonID => ''.$cgi->param('sessonID')},
        -user           => {display => "USER", min => 8, max =>20},
        -pass           => {display => "PASSWORD", min => 8, max =>35},
        -timeout        => 60 * 4,
        -LoginForm      => \&login_html,
        #-logintmpl      => login_html()
    });

my ($user, $sessionID) = $sec->check;

if (''.$cgi->param('auth_submit') eq 'logout')
{
    $sec->endsession;
}

print "Content-Type: text/html\n\n".work($sessionID);

print STDERR "at end\n";

sub work
{
    my ($sessonID) = @_;
    printf STDERR "in work [%s]\n", $sessonID;

my $stuff = <<EOF;
<!doctype html public "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
<title>work</title>
<style type="text/css">
<!--
body { color: black; background-color: white; }
td.fieldname { text-align: right; width: 40%}
td.fieldvalue { text-align: left; width: 60%}
table.main { width: 100%; border: none; }
table.login { width: 60%; background-color: #E4E4E4; border: thin solid black; }
-->
</style>
</head>

<body OnLoad="document.forms[0].elements[0].focus();">
<table class="main">

    <tr>
        <td style="text-align: center">
            <h3>hello world</h3>
            <form method="post" action="test.pl">
                <input type=submit name="auth_submit" value="foobar">
                <input type=submit name="auth_submit" value="logout">
            <input type=hidden name=sessonID value="$sessonID">
            </form>
        </td>
    </tr>
</table>
</body>
</html>

EOF
return $stuff;
}
use constant HTTPCONTENT         => "Content-Type: text/html\n\n";
sub login_html
{
    my ($parms) = @_;

    print STDERR "login_html: ".Dumper $parms;

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


