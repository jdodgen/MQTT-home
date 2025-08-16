#!/usr/bin/perl
use lib '/var/www/alertaway.com/cgi-bin/admin';
use CGI;
use HTML::Template;
use Auth;  # testing CGI::Auth
#require CGI::Auth;
use DBI;
use Data::Dumper;
use strict;

print STDERR "starting\n";

my $db_name = "/home/alerta/main.db";
my %attr = (PrintError => 0,RaiseError => 0,AutoCommit => 1);
my $dbh = DBI->connect("dbi:SQLite:$db_name","","",\%attr);
if (!defined($dbh))
{
    print("could not connect to $db_name\n");
}


my $t = HTML::Template->new_scalar_ref(login_html());
my $cgi = new CGI;
#print STDERR Dumper \$cgi;
#my $auth = new CGI::Auth({
my $auth = new Auth({ # testing
    -authdir                => 'auth',
    -sessdir                => 'sess',
    -md5pwd                 => 1,
    -dbi                    => $dbh,
    -query                  => "select pass_phrase from systems where pan_id = %s",
    -cgi => $cgi,
    -formaction             => "cgiauth.pl",
    -logintmpl              => $t,
    -authfields             => [
        {id => 'user', display => 'Pan ID', hidden => 0, required => 1},
        {id => 'pw', display => 'Passphrase', hidden => 1, required => 1},
    ],
});


#printf STDERR "test read $hex status[%s] passphrase[%s]\n", $stat, $passphrase;
#printf STDERR "cgi auth_sessfile [%s]\n", ''.$cgi->param('auth_sessfile');

$auth->check;

#my ($stat, $passphrase) = $auth->{dt}->get_rec("select ip_address from systems where pan_id = %s", $auth->data('user'));

my $sess_file = $auth->data('sess_file');

print STDERR "user [".$auth->data('user')."]\n";
#printf STDERR "sess_file  [%s]\n",  $sess_file[0];
#printf STDERR "data sess_file  [%s]\n",  $sess_file;
print "Content-Type: text/html\n\n".work($sess_file);

print STDERR "at end\n";

sub login_html
{
my $stuff = <<EOF;
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
table.login { width: 60%; background-color: #E4E4E4; border: thin solid black; }
-->
</style>
</head>

<body OnLoad="document.forms[0].elements[0].focus();">
<table class="main">
    <tr>
        <td style="background: #CCCCCC; text-align: center">
            <p><b>Authorization Required</b></p>
        </td>
    </tr>
    <tr>
        <td style="text-align: center;">
            <h3>Please Log In</h3>
            <p>
                <!-- TMPL_VAR NAME=Message -->
            </p>
            <form method="post" action="<TMPL_VAR Name=Form_Action>">
                <table class="login">
                    <!-- TMPL_LOOP NAME=Auth_Fields -->
                    <tr>
                        <td class="fieldname">
                            <p><!-- TMPL_VAR NAME=Display_Name -->:</p>
                        </td>
                        <td class="fieldvalue">
                            <input type="<TMPL_VAR Name=Input_Type>" name="<TMPL_VAR Name=Input_Name>">
                        </td>
                    </tr>
                    <!-- /TMPL_LOOP -->
                </table>
                <input type=submit name="<TMPL_VAR Name=Button_Name>" value="Login">
                <!-- TMPL_VAR NAME=Form_Fields -->
            </form>
        </td>
    </tr>
</table>
</body>
</html>

EOF
return \$stuff;
}
sub work
{
    my ($sess_file) = @_;
    printf STDERR "inwork [%s]\n", $sess_file;

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
        <td style="text-align: center;">
            <h3>hello world</h3>
            <form method="post" action="cgiauth.pl">
                <input type=submit name="auth_submit" value="foobar">
            <input type=hidden name=auth_sessfile value="$sess_file">
            </form>
        </td>
    </tr>
</table>
<input type=hidden name=auth_sessfile value="$sess_file">
<input type=hidden name="auth_user" value="foo">

</body>
</html>

EOF
return $stuff;
}

###
