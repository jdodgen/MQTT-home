# $Id: Secure.pm,v 1.17 2021/03/27 07:05:46 jdodgen Exp $
package Secure;

use strict;
use Carp;
use DBI;
use HTML::Template;
use Crypt::PasswdMD5;

use vars qw/$VERSION/;
$VERSION = '0.1';

use constant DBG => 1;

# This delimiter cannot be a regex special character, unfortunately, since it
# is used with split.  So, for instance, the pipe (|) is not allowed, as well
# as the dash (-), caret (^), dot (.), etc...
#use constant DELIMITER => ':';

=pod

=head1 NAME

CGI::Auth - Simple session-based password authentication for CGI applications

=head1 SYNOPSIS

    require CGI::Auth;

    my $auth = new CGI::Auth({
        -authdir        => 'auth',
        -formaction     => "myscript.pl",
        -authfields     => [
            {id => 'user', display => 'User Name', hidden => 0, required => 1},
            {id => 'pw', display => 'Password', hidden => 1, required => 1},
        ],
    });
    $auth->check;

=head1 DESCRIPTION

C<CGI::Auth> provides password authentication for web-based applications.  It
uses server-based session files which are referred to by a parameter in all
links and forms inside the scripts guarded by C<CGI::Auth>.

At the beginning of each script, a C<CGI::Auth> object should be created and
its C<check> method called.  When this happens, C<check> checks for a
'session_file' CGI parameter.  If that parameter exists and has a matching
session file in the session directory, C<check> returns, and the rest of the
script can execute.

If the session file parameter or the file itself doesn't exist, C<check>
presents the user with a login form and exits the script.  The login form will
then be submitted to the same script (specified in C<-formaction>).  When
C<check> is called this time, it verifies the user's login information in the
userfile, creates a session file and provides the session file parameter to the
rest of the script.

=head1 CREATING AND CONFIGURING

Before anything can be done with C<CGI::Auth>, an object must be created:

    my $auth = new CGI::Auth( \%options );

=head2 Parameters to C<new>

The C<new> method creates and configures a C<CGI::Auth> object using
parameters that are passed via a hash reference that can/should contain the
following items (optional ones are indicated):

=over 4

=item C<-cgi>

I<(optional)>

This parameter provides C<CGI::Auth> with a CGI object reference so that the
extra overhead of creating another object can be avoided.  If your script is
going to use CGI.pm, it is most efficient to create the CGI object and pass it
to C<CGI::Auth>, rather than both your script and Auth having to create
separate objects.

Note:  As of version 2.4.3, C<CGI::Auth> can now be used with C<CGI::Simple>.
This hasn't been tested thoroughly yet, so use caution if you decide to do so.

=item C<-admin>

I<(optional if C<-formaction> given)>

This parameter should be used by command-line utilities that perform
administration of the user database.  If Auth is given this parameter, it will
only allow command-line execution (execution from CGI will be aborted).

=item C<-authdir>

I<(required)>

Directory where Auth will look for its files.  In other words, if C<-sessdir>,
C<-userfile>, C<-logintmpl>, C<-loginheader> or C<-loginfooter> are scalars
and do not begin with a slash (i.e., are not absolute paths), this directory
will be prepended to them.

=item C<-sessdir>

I<(optional, default = 'sess')>

Directory where Auth will store session files.  These files should be pruned
periodically (i.e., nightly or weekly) since a session file will remain here if
a user does not log out.

=item C<-userfile>

I<(optional, default = 'user.dat')>

File containing definitions of users, including login information and any extra
parameters.  This file will be created, edited and read by C<CGI::Auth> and its
command-line administration tool.

=item C<-logintmpl>

I<(optional, excludes C<-loginheader> and C<-loginfooter> if present)>

Template for use with C<HTML::Template>.  The template can be given in one of
three ways:

=over 4

=item 1

An C<HTML::Template> object reference,

=item 2

A hash containing parameters for C<HTML::Template-E<gt>new>, or

=item 3

A filename (then C<-logintmplpath> can be the path parameter).

=back

The template must contain a form for the user to fill out, and it is
recommended that the form not contain any elements with names beginning with
'auth_', since these are reserved for C<CGI::Auth> fields.

A sample template file (C<login.html>) is included in the extra subdirectory of
this package.

For a list of what should be included in the template, see
L<Template Variables> and L<Template Loops> below.

=item C<-logintmplpath>

I<(optional, default = [])>

List of search path(s) for C<HTML::Template> files (the 'path' option).  This
is used only if C<-logintmpl> is a filename.  Otherwise, the path option must
be passed to C<HTML::Template-E<gt>new> directly.

=item C<-loginheader>

I<(optional, default = 'login.head' or a simple default header)>

Header for login screen.

NOTE: C<-loginheader> and C<-loginfooter> are ignored if C<-logintmpl> is
provided.

=item C<-loginfooter>

I<(optional, default = 'login.foot' or a simple default footer)>

Footer for login screen.

NOTE: C<-loginheader> and C<-loginfooter> are ignored if C<-logintmpl> is
provided.

=item C<-formaction>

I<(optional if C<-admin> given)>

URL of calling script.  This is used by the login screen as the form's "action"
property.

=item C<-authfields>

I<(required)>

Array of hashes defining fields in user database.  This requires at least one
field, which must be 'required' and not 'hidden'.  Any other fields can be used
to authenticate the user or to contain information about the user such as
groups, access levels, etc.  Once a user has logged on, all of his fields are
available through the C<data> method.  However, any fields that are marked
'hidden' will be crypted and not readable by the script.

Each field in the C<-authfields> anonymous array is a hash containing 4 keys:

    'id'        ID of the field.  This must be unique across all fields.
    'display'   Display string which is presented to the user.
    'hidden'    Flag (0 or 1) that determines whether this field is hidden
                on the login screen and encrypted in the user file.
    'required'  Flag (0 or 1) indicating whether this field must be given
                for authentication.
    'length'    The maximum length allowed for this field. this is important
                to avoid denial of service attacks. default is 16.

Here is an example of a simple username/password scheme, with one extra data
parameter:

    -authfields     => [
        {id => 'user', display => 'User Name', hidden => 0, required => 1, length => 12},
        {id => 'pw', display => 'Password', hidden => 1, required => 1, length => 16},
        {id => 'group', display => 'Group', hidden => 0, required => 0, length => 30},
    ],

=item C<-timeout>

I<(optional, default = 60 * 15, 15 minutes)>

The timeout value in seconds after which an unused session file will expire.

=item C<-cgiprune>

I<(optional, default = false)>

Whether to allow calls to prune in CGI mode.  If your CGI scripts need (or
want) to delete old session files, this will have to be set to true.  I can't
think of any particular reason not to allow this, but it isn't allowed by
default.

=item C<-md5pwd>
=item C<-unix_md5_crypt>

I<(optional, default = Perl crypt)>

Whether to use an MD5 hash for hidden fields in the user data file.  If false,
the Perl built-in C<crypt> is used twice (via the C<DoubleCrypt> sub below), so
hidden fields are restricted to 16 characters.  If true, MD5 hashes are used,
and there is no length restriction for hidden fields.

If this option is changed, the user data file will have to be recreated using
MD5 hashes, so it's best to make this decision at the beginning.

Using MD5 hashes will result in a slight performance hit when logging in.  This
will probably not be noticeable at all.

md5pwd uses Digest::MD5

unix_md5_crypt uses Crypt::PasswdMD5 which is better, being salted.




=back

=item C<-dbi>

I<(optional, excludes C<-userfile> )>

This parameter provides C<CGI::Auth> with a DBI object reference.
This allows the access of definitions of users, including login information and any extra parameters stored in a Database.
The use of this feature requires the following:

=over 4

=item 1

You must supply a Database C<-query>  statment to return the fields in the same order as defined in the C<-authfields> this select will be called printf style supplying the "user".

    SELECT password FROM your_table WHERE user = %s

=item 2

The C<-authfields> "hidden" field(s) returned in the query must have been previously encrypted using the C<encrypt_data> routine.

=back

Here are the changes to the SYNOPSIS above

    my $dbh = DBI->connect(your database of choice);
    my $auth = new CGI::Auth({
        -authdir                => 'auth',
        -formaction             => "myscript.pl",
        -authfields             => [
            {id => 'user', display => 'User Name', hidden => 0, required => 1, length => 12},
            {id => 'pw', display => 'Password', hidden => 1, required => 1, length => 16},
        ],
        -dbi => $dbh,
        -query => "SELECT password FROM your_table WHERE user = %s",

    });

=back

=item C<-query>

I<(optional, required if  C<-dbi>)>

select string returning the authfields specified values. It is called printf style supplying the user id for the %s.

    SELECT password FROM your_table WHERE user = %s

=back

=head2 Template Variables

These template variables are required.  The names of these are case-insensitive
by default.  See L<HTML::Template> for more information.

=over 4

=item C<Message>

A message to the user, such as "Login failed", "Session expired", etc...

NOTE: This variable might be left blank when the form is created.  So don't
depend on it having a value.

=item C<Form_Action>

The 'action' property of the form that submits the authentication information.

=item C<Button_Name>

The 'name' property of the submit button on the form.  The tag for the button
should look something like this:

    <input type=submit name="<TMPL_VAR Name=Button_Name>" value="Submit">

The 'value' property of the submit button can be anything.

=back

=head2 Template Loops

These loops must exist in the template.  The names of these are case-insensitive
by default.  See L<HTML::Template> for more information.

=over 4

=item C<Auth_Fields>

Provides variables for each required Auth field.  These are the fields which
will be filled in by the user when logging in.  The following variables are
provided:

=over 4

=item C<Display_Name>

The display name of the field, e.g., "User Name" or "Password".

=item C<Input_Name>

The 'name' property of the text input for the field.

=item C<Input_Type>

The type, 'text' or 'password', of the input, depending on whether this
field is hidden or not.

=back

=back

=head1 PUBLIC METHODS

There are two groups of public methods in CGI::Auth.  The CGI-mode methods are
called from CGI scripts for the purposes of authenticating a user and managing
sessions.  The command-line methods are used only in command-line scripts,
such as the authman.pl sample userbase manager script.  The latter methods
will abort execution if they are run in a CGI environment.

=head2 Initialization Methods

These are used for creating a C<CGI::Auth> object.

=over 4

=item C<new>

Constructor.  It accepts as a parameter a hash reference holding named
options.  For a list and descriptions of these options, see
L<Parameters to C<new>>.

=cut

use constant CREATE_SESSION_TBL  => "CREATE TABLE IF NOT EXISTS  crypstore (sessid TEXT PRIMARY KEY, user TEXT, date INT, ipaddress TEXT)";
use constant GET_SESSION         => "SELECT user, date, ipaddress from crypstore WHERE sessid = %s";
use constant INSERT_SESSION      => "INSERT OR REPLACE INTO crypstore (sessid, user, date, ipaddress) VALUES (%s,%s,%s,%s)";
use constant DELETE_A_SESSION    => "DELETE FROM crypstore WHERE sessid = %s OR date > %s";
use constant UPDATEDATE          => "UPDATE crypstore set DATE = %s WHERE sessid = %s";

sub new
{
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $self = {};
    bless $self, $class;

    $self->init(@_) or return undef;

    return $self;
}

=pod

=item C<init>

Performs processing of options passed to C<new>.  This should not be called
directly.

=cut

# Called by new--all parameters to new are passed off to init for processing.
sub init
{
    my ($self, $param) = (shift, shift);
    my $msg = '';
    return 0 unless (UNIVERSAL::isa($param, 'HASH'));

    # Parameters in an anonymous hash.
    # All config options are passed here... no config file!
    $self->{logintmpl} = $param->{-logintmpl};
    $self->{LoginForm} = $param->{-LoginForm};
    $self->{formaction} = $param->{-formaction};
    $self->{user} = $param->{-user};
    $self->{pass} = $param->{-pass};
    $self->{userquery} = $param->{-userquery}; # sql select to get encrypted password
    $self->{check} = $param->{-check};
    $self->{timeout} = $param->{-timeout};


    if ( ! $param->{-dbi} )
    {
        if ( ! $param->{-dbpath} )
        {
            $self->PrintLoginForm("Using internal SQLite DBI but missing -dbpath");
            exit(0);
        }
        my %attr = (PrintError => 0,RaiseError => 0,AutoCommit => 1);
        my $dbh = DBI->connect("dbi:SQLite:".$param->{-dbpath},"","",\%attr);
        if (!defined($dbh))
        {
            croak("could not connect to ".$param->{-dbpath});
        }
        $self->{dbi} = $dbh;
    }
    else
    {
        $self->{dbi} = $param->{-dbi};
        if ( $param->{-dbpath} )
        {
            $self->PrintLoginForm("Confused: using external DBI -dbi and also have a -dbpath");
            exit(0);
        }
        DBG&&printf STDERR  "using program supplied DBI for password valadation\n";
    }
    $self->do(CREATE_SESSION_TBL);
    #$self->{webserver} = $param->{-webserver};





    unless ($self->{logintmpl})
    {
        $self->{loginheader}    = 'login.head'  unless ($self->{loginheader});
        $self->{loginfooter}    = 'login.foot'  unless ($self->{loginfooter});
    }
    $self->{timeout}        = 60 * 15       unless ($self->{timeout});

    # Create authdata hash.
    $self->{authdata} = {};
    return 1;
}


=pod

=back

=head2 CGI-mode Methods

These methods are called from CGI scripts.

=over 4

=item C<check>

Ensures authentication.  If the session file is not present or has expired, a
login form is presented to the user.  A call to this method should occur in
every script that must be secured, before the script prints B<anything> to the
browser.

=cut

sub check
{
    my ($self) = @_;

    if ($self->{check}->{sessonID})
    {
        my $sesionID = $self->{check}->{sessonID};
        my ($status, $user, $date, $ipaddress) = $self->get_rec(GET_SESSION, $sesionID);   # get session record
        DBG&&printf STDERR  "check: id [%s] 'user' [%s]\n", $sesionID, $user;
        if ($status)
        {
            if ( $ipaddress and $ipaddress ne $ENV{REMOTE_ADDR} )
            {
                # IP address doesn't match.
                # Return error: unable to access session file.
                $self->PrintLoginForm("Invalid user or password.");
                exit(0);
            }
            my $now = time;
            my $age = $now - $date;        # How old is the session file?

            # Check age against timeout value.
            if ($age > $self->{timeout})
            {

                $self->endsession();
                $self->PrintLoginForm("Your session has expired.  Please log in again.");
                exit(0);
            }
            # looks good so reset date and return
            $self->do(UPDATEDATE, $now, $sesionID);
            return ($user, $sesionID);
        }
        else
        {
            $self->PrintLoginForm("You are not logged in");
            DBG&&printf STDERR ("check: You are not logged in");
            exit(0);
        }
    }
    else # no sessionID so chek for login
    {
        DBG&&printf STDERR  "check: logging in: u[%s] p[%s]\n", $self->{check}->{user}, $self->{check}->{password};
        if (length $self->{check}->{user} == 0 or length $self->{check}->{password} == 0)
        {
           $self->PrintLoginForm('');
           exit(0);
        }
        if ( length $self->{check}->{user} > $self->{user}->{max})
        {
            $self->PrintLoginForm( $self->{user}->{display} . " Length must be less than " . $self->{user}->{max}." characters");
            #&carp( $self->{user}->{display} . " too long. Must be " . $self->{user}->{max} . " characters or less." );
            exit(0);
        }
        if ( length $self->{check}->{password} > $self->{pass}->{max})
        {
            $self->PrintLoginForm( $self->{pass}->{display} . " Length must be less than " . $self->{pass}->{max}." characters");
            #&carp( $self->{pass}->{display} . " too long. Must be " . $self->{pass}->{max} . " characters or less." );
            exit(0);
        }
        my ($status, $encrypted) = $self->get_rec($self->{userquery}, $self->{check}->{user});
        DBG&&printf STDERR "after get_rec status[%s] encrypted[%s]\n", $status, $encrypted;
        if ( $status == 1 and compare_encryptions($self->{check}->{password}, $encrypted) )
        {
            my $sessonID = $self->InsertSesson( $self->{check}->{user} );
            return ($self->{check}->{user}, $sessonID); # got a good one
        }
        else
        {
            $self->PrintLoginForm("Authentication failed!  Check login information and try again.");
            exit(0);
        }
    }
    #we never get here
    return undef;

}

=pod

=item C<endsession>

Deletes the session file so that the user must log in again to gain access.

Returns 1 if session file deleted successfully, 0 if an error occurred ($! will
contain the error), or -1 if the session file did not exist.

=cut

sub endsession
{
    my $self = shift;
    # Also check ages against timeout value. self cleaning.
    $self->do(DELETE_A_SESSION, $self->{check}->{sessonID}, time - $self->{timeout});
    $self->PrintLoginForm("Good bye.");
    exit(0);
}

=pod

=item C<setdata>

Sets auth data fields.

=cut

sub setdata
{
    my $self = shift;
    my @data = @_;

    return 0 if (@data != @{$self->{authfields}}); # same number of login inputs example: user and password would be 2

    for (my $idx = 0; $idx < @data; ++$idx)
    {
        next if ($self->{authfields}->[$idx]->{hidden}); # hidden are encrypted so we ignore

        # Store non-hidden data in authdata for program to access.
        $self->{authdata}->{$self->{authfields}->[$idx]->{id}} = $data[$idx]; #stored by ID ... thisis usualy just the 'user' in pain text
    }

    return 1;
}

=pod

=item C<data>

Returns a given data field.  The field's ID is passed as the parameter, and the
data is returned.  The special field 'sess_file' returns the name of the
current session file in the C<-sessdir> directory.

=cut

sub data
{
    my $self = shift;
    my $key = shift;

    if ($key eq 'sess_file')
    {
        return $self->{sess_file};
    }

    return $self->{authdata}->{$key};
}

=pod

=item C<sfparam_name>

Returns the name of the session file parameter (i.e., 'auth_sessfile').

=cut

sub sfparam_name
{
    'auth_sessfile';
}

=pod

=item C<sfparam_value>

Returns the value of the session file parameter (i.e., the name of the session file).

=cut

sub sfparam_value
{
    my $self = shift;

    $self->data('sess_file');
}

=pod

=item C<formfield> B<(deprecated)>

B<(deprecated)> - Use of C<urlfield> and C<formfield> is discouraged in favour
of C<sfparam_name> and C<sfparam_value> because the latter provide much more
flexibility.  For example, they allow you to create elements that are
XHTML-compliant, whereas the data returned from C<formfield> is only valid for
HTML 4.

Returns the session file parameter as a hidden input field suitable for
inserting in a E<lt>FORME<gt>, e.g.:

    '<input type="hidden" name="auth_sessfile" value="DBEEL87CXV7H">'

=cut

sub formfield
{
    my $self = shift;

    my $name = $self->sfparam_name;
    my $value = $self->sfparam_value;

    return qq(<input type="hidden" name="$name" value="$value">);
}

=pod

=item C<urlfield>

B<(deprecated)> - Use of C<urlfield> and C<formfield> is discouraged in favour
of C<sfparam_name> and C<sfparam_value> because the latter provide much more
flexibility.  For example, they allow you to create elements that are
XHTML-compliant, whereas the data returned from C<formfield> is only valid for
HTML 4.

Returns the session file parameter as a field suitable for tacking onto the end
of an URL (such as in a link), e.g.:

    'auth_sessfile=DBEEL87CXV7H'.

=cut

sub urlfield
{
    my $self = shift;

    my $name = $self->sfparam_name;
    my $value = $self->sfparam_value;

    return qq($name=$value);
}

=pod

=back

=head2 Command-line Methods

These methods are used for user maintenance.  They cannot be run under a CGI
environment.  Use them only in command-line programs as an administrator (or as
a user with write access to the user data file).

=over 4

#=item C<adduser>

#The parameters are an ordered list of data values for the @authfields.  For
#example:

    #$auth->adduser('KAM', 'smokey');  # Branchname, Password

#=cut

#sub adduser
#{
    #my $self = shift;

    #&DenyCGI;

    #my @userdata = @_;
    #DBG&&printf STDERR  "adduser: input [%s]\n", join( DELIMITER, @userdata );

    #&croak("Bad user data") if (@userdata != @{$self->{authfields}});

    ## Append user to user file.

    #for (my $idx = 0; $idx < @userdata; ++$idx)
    #{
        #my $authfield = $self->{authfields}->[$idx];
        #if ( $authfield->{hidden} )
        #{
             #$userdata[$idx] = encrypt_data($self->{cryptipe}, $userdata[$idx] );
             #if ( !$userdata[$idx] )
             #{
                #&croak( "Hidden field '" . $authfield->{display} . "' cannot have length greater than 16 characters when using crypt" );
             #}
            ##if ( $self->{md5pwd} )
            ##{
                ##$userdata[$idx] = MD5Crypt( $userdata[$idx] );
            ##}
            ##else
            ##{
                ##if ( length $userdata[$idx] > 16 )
                ##{
                    ##&croak( "Hidden field '" . $authfield->{display} . "' cannot have length greater than 16 characters when using crypt" );
                ##}
                ### Store encrypted.
                ##$userdata[$idx] = DoubleCrypt( $userdata[$idx], join '', ('.', '_', 0..9, 'A'..'Z', 'a'..'z')[rand 64, rand 64] );
            ##}
        #}
    #}

    #open USER, ">> " . $self->{userfile}
        #or return 0;
    #DBG&&printf STDERR  "adduser: output \n%s", join( DELIMITER, @userdata ), "\n";
    #print USER join( DELIMITER, @userdata ), "\n";
    #close USER;
#}

#=pod

#=item C<listusers>

#Prints a list of users in the user file.

#=cut

#sub listusers
#{
    #my ($self) = @_;

    #&DenyCGI;

    #open USER, "< " . $self->{userfile} or return;
    #while (<USER>)
    #{
        #my ($br) = split( DELIMITER, $_, 2 );
        #print "$br\n";
    #}
    #close USER;
#}

#=pod

#=item C<viewuser>

#Prints details for one user.  The parameter is the user's 'field 0' value.

#=cut

#sub viewuser
#{
    #my ($self, $field0) = @_;

    #&DenyCGI;

    #my @userdata = $self->GetUserData($field0);

    #if (@userdata == 0)
    #{
        #print "$field0 does not exist.\n";
        #return 0;
    #}
    #&croak("Bad user data for $field0") if (@userdata != @{$self->{authfields}});

    #for (my $idx = 0; $idx < @userdata; ++$idx)
    #{
        #my $msg = $self->{authfields}->[$idx]->{display};
        #$msg .= " (required)" if ($self->{authfields}->[$idx]->{required});
        #$msg .= " (hidden)" if ($self->{authfields}->[$idx]->{hidden});
        #$msg .= ": " . $userdata[$idx] . "\n";

        #print $msg;
    #}
#}

#=pod

#=item C<deluser>

#Deletes a user.  The parameter is the user's 'field 0' value.

#=cut

#sub deluser
#{
    #my ($self, $field0) = @_;

    #&DenyCGI;

    #$self->viewuser($field0);

    #print "\nDelete this user? ";
    #my $resp = <STDIN>;

    ## If the response begins with a 'y' (or 'Y'), ie. 'yes' or 'y' or 'you better not!'...
    #if ( $resp =~ /^[yY]/ )
    #{
        #open USER, "< " . $self->{userfile} or &croak("Unable to read userfile: $!");
        #my @userfile = <USER>;
        #close USER;

        #open USER, "> " . $self->{userfile} or &croak("Unable to write userfile: $!");
        #for (@userfile)
        #{
            #if (!/^$field0\b/i)
            #{
                #print USER $_;
            #}
        #}
        #close USER;
        #print "\nUser deleted.\n";
    #}
    #else
    #{
        #print "\nUser not deleted.\n";
    #}
#}

#=pod

#=item C<prune>

#Prunes the session file directory by deleting session files that have expired.
#This can be called in CGI mode if '-cgiprune' is set to true.

#=cut

#sub prune
#{
    #my $self = shift;

    #&DenyCGI unless ( $self->{cgiprune} );

    #my $pruned = 0;

    #opendir SESSDIR, $self->{sessdir};
    #while (my $file = readdir(SESSDIR))
    #{
        #$file = $self->{sessdir} . '/' . $file;
        #next unless (-f $file);

        #my $mtime = (stat _)[9];
        #my $now = time;
        #my $age = $now - $mtime;

        #$pruned += unlink $file if ($age > $self->{timeout});
    #}
    #closedir SESSDIR;

    #return $pruned;
#}

#=pod

=back

=head1 ENCRYPTING ROUTINES

These routines is used for Programmers to create the "hidden" encrypted values
typicaly for use in a Database.
Note:  the items you encrypt must match up positionaly with the -authfields hidden items
in your -query Database Query.

=over 4

=item C<encrypt_data>

The parameter is a the value to be encrypted.
if you are using the C<-md5pwd> in your program you need to set use_MD5Crypt = 1
For example:

    Auth::encrypt_data('Sm0key band1t');  #  Typicaly a Password

=cut

sub encrypt_data
{
    my ($data) = @_;

    return Crypt::PasswdMD5::unix_md5_crypt($data, Crypt::PasswdMD5::random_md5_salt());
}

=item C<compare_encryptions>

The parameters are the MD5 flag, key to check, correct value.

if you are using the C<-md5pwd> in your program you need to set MD5Crypt = 1

this is usefull when updating the encrypted fields in a database.
note when not using MD5 this value will change everytime it is re calculated.
It is a best practice to not replace this value unless the "password" actualy changes.
not a problem with MD5

For example:

    Secure::compare_encryptions(the_one_you_ar_checking, the stored_encrypted_value);

=cut


sub compare_encryptions
{
    my ($formvalue, $userdata ) = @_;

    my $tocheck = Crypt::PasswdMD5::unix_md5_crypt($formvalue, $userdata);
    DBG&&printf STDERR "F[%s]\n",$formvalue;
    DBG&&printf STDERR "T[%s]\n",$tocheck;
    DBG&&printf STDERR "U[%s]\n",$userdata;
    if ($tocheck ne $userdata )
    {
        return;
    }
    return 1;
}

=pod

=back

=head1 PRIVATE METHODS

There are also some private methods.  Use of them by unauthorized dirrty
scripts is a federal offence in some jurisdictions, carrying a maximum sentence
of yearly noogies by yours-truly.  This may or may not be legal in your
country.

=over 4

=item C<GetUserData>

Fetches a user's auth data from the user file.  The data fields are returned as
a list, in the order in which they appear in the data file.

=cut

sub GetUserData
{
    my ($self, $field0) = @_;   # $field0 usualy user

    DBG&&printf STDERR  "GetUserData [%s]\n", $field0;
    unless ( $field0 )
    {
        warn "Field0 not given";
        return;
    }
    my @userdata;

        DBG&&printf STDERR  "GetUserData using Database\n";
        my ($status, @things) = $self->get_rec($self->{query}, $field0);
        if ($status)
        {
            DBG&&printf STDERR  "GetUserData status[%s] things[%s]\n", $status, @things;
            @userdata = ($field0, @things);
        }
        else
        {
            return;
        }

    return @userdata;
}

=pod

=item C<PrintLoginForm>

Prints the login form using either an C<HTML::Template> or a header and footer.

This is called by C<check> when the user is not authenticated.

This method hands off either to C<PLF_template> or to C<PLF_headerfooter>.

=cut

use constant HTTPOK              => "HTTP/1.0 200 OK\n";
use constant HTTPCONTENT         => "Content-Type: text/html\n\n";

#sub PrintLoginForm
#{
    #my ($self, $msg) = @_;

    #my $template = HTML::Template->new_scalar_ref( $self->{logintmpl});

    #$template->param(
        #Message => $msg,
        #pass => $self->{pass}->{display},
        #user => $self->{user}->{display},
        #usermax => $self->{user}->{max},
        #passmax => $self->{pass}->{max},
        #Form_Action => $self->{formaction},

    #);
    #print HTTPOK if lc(($self->{webserver}) eq 'perl');
    #print HTTPCONTENT.$template->output();
#}



sub PrintLoginForm
{
    my ($self, $msg) = @_;

    $self->{LoginForm}(
        {Message => $msg,
        pass => $self->{pass}->{display},
        user => $self->{user}->{display},
        usermax => $self->{user}->{max},
        passmax => $self->{pass}->{max},
        Form_Action => $self->{formaction}}
    );
}

=pod

=item C<PLF_template>

Prints the login form using an HTML::Template.  It uses the value of the
logintmpl property to get the template.

=cut

sub PLF_template
{
    my ($self, $msg) = @_;

    require HTML::Template;

    # logintmpl can be one of three things (which are all true values):
    # 1. An HTML::Template object reference,
    # 2. A hash containing parameters for HTML::Template->new, or
    # 3. A filename (then logintmplpath can be the path parameter).
    my $template = $self->{logintmpl};
    unless ( UNIVERSAL::isa( $template, 'HTML::Template' ) )
    {
        $template = new HTML::Template(
            UNIVERSAL::isa( $template, 'HASH' )
            ? %{ $self->{logintmpl} }
            : (
                filename => $template,
                path => $self->{logintmplpath},
            )
        );
    }

    # Create parameters for Auth_Fields <TMPL_LOOP>.
    my @fields = ();
    foreach my $authfield (@{$self->{authfields}})
    {
        if ($authfield->{required})
        {
            push @fields, {
                Display_Name => $authfield->{display},
                Input_Name => 'auth_' . $authfield->{id},
                Input_Type => $authfield->{hidden} ? 'password' : 'text',
            };
        }
    }

    $template->param(
        Message => $msg,
        Auth_Fields => \@fields,
        Button_Name => 'auth_submit',
        Form_Action => $self->{formaction},
        Form_Fields => $self->FormFields,
    );
    print $template->output();
}

=pod

=item C<FormFields>

Returns HTML code for placing existing CGI parameters on a form so that the
login process is transparent to the calling script.

For any single-valued parameters, it creates a hidden C<< <input> >> control,
and for any multi-valued parameters, it creates a hidden (i.e.,
C<style="display: none">) C<< <select> >> control with all of its values.

=cut

sub FormFields
{
    my ($self) = shift;

    my $formfields = '';

    for my $name ($self->{cgi}->param)
    {
        next if ($name =~ /^auth_/);
        my @values = $self->{cgi}->param($name);

        if (@values < 2)    # i.e., 0 or 1 values.
        {
            my $val = $values[0] || '';
            $formfields .= qq(<input type=hidden name="$name" value="$val">\n);
        }
        else
        {
            $formfields .= join ("\n",
                qq(<select multiple name="$name" style="display:none">),
                (map {qq(<option selected value="$_" style="display:none">$_</option>)} @values),
                qq(</select>),
                ''      # For a \n at the end.
            );
        }
    }

    return $formfields;
}

=pod

=item C<InsertSession>

Inserts session record.

=cut

sub InsertSesson
{
    my ($self, $user) = @_;

    my @chars = (0..9, 'A'..'Z');

    # Verify format and untaint.
    my $remoteaddr = $ENV{REMOTE_ADDR} || '';
    $remoteaddr =~ /([\dA-F\.:]+)/;     # IPv4 or IPv6 address.
    $remoteaddr = $1 || '';

    my $sessID;
    my $trycount = 5;
    while ($trycount--)
    {
        $sessID = join '', map {$chars[rand 36]} (1..12);
        DBG&&printf STDERR "sessionID[%s]\n", $sessID;
        my ($status) = $self->do(INSERT_SESSION, $sessID, $user, time,  $remoteaddr);
        last if ($status);
        if ($self->{dbi}->err == 1) # generic error
        {
            # might be the table has not been created yet
        }
        DBG&&printf STDERR "sqlite status[%s] error code[%s]\n", $status, $self->{dbi}->err;
    }
    return $sessID;
}

=pod

=item C<OpenSessionFile>

Opens the session file and returns the user's id (field0) if successful.

The return value is one of three things:

=over 4

=item 1

B<Field 0> value from session file if successful,

=item 2

B<0> if the session has expired, or

=item 3

B<undef> if the session file doesn't exist or can't be opened.

=back

=cut

sub OpenSessionFile
{
    my $self = shift;

    my $sessfile = $self->{sessdir} . "/" . $self->{sess_file};
    if (-f $sessfile)
    {
        my $mtime = (stat _)[9];
        my $now = time;
        my $age = $now - $mtime;        # How old is the session file?

        # Check age against timeout value.
        if ($age > $self->{timeout})
        {
            # Too old!
            unlink $sessfile;
            return 0;
        }

        # Attempt to open file.
        if (open (SESS, "< $sessfile"))
        {
            # Read information from file.
            my $field0 = <SESS>;
            my $file_ra = <SESS>;
            close SESS;

            # If $field0 has any invalid chars, return error.
            # This also untaints $field0.
            my $validchars = $self->{validchars};
            if ( $field0 =~ /^([$validchars]+)$/ )
            {
                $field0 = $1;
            }
            else
            {
                warn "UserID [$field0] found in session file is invalid";
                return undef;
            }

            $file_ra =~ /^(\S*?)$/;
            $file_ra = $1;
            # Verify remote IP address, if present in file.
            # What this does is ensure that if the REMOTE_ADDR was available at
            # login time, it must be available now and must be the same.
            if ( $file_ra and $file_ra ne $ENV{REMOTE_ADDR} )
            {
                # IP address doesn't match.
                # Return error: unable to access session file.
                warn "Address [$file_ra] found in session file does not match REMOTE_ADDR [" . $ENV{REMOTE_ADDR} . "]";
                return undef;
            }

            # Update modification time for timeout.
            utime $now, $now, $sessfile;

            # Return Field 0 (ie, user name).
            return $field0;
        }

        # File couldn't be opened.
        &carp("Couldn't open session file $sessfile because '$!'");
    }

    # Non-existent or inaccessible session file.
    return undef;
}

=pod

=back

=head1 HELPER FUNCTIONS (not members)

Feel free to use and abuse these.  They just do dirty little jobs.

=over 4

=item C<DenyCGI>

Exits if run as CGI.  This could be made a little more intelligent.  The
command-line methods call this function as their very first act.

=cut

sub DenyCGI
{
    if ( $ENV{GATEWAY_INTERFACE} || $ENV{REQUEST_METHOD} || $ENV{REMOTE_ADDR} )
    {
        print <<ERRORDOC;
Content-type: text/html

<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<html><head><title>Forbidden</title></head>
<body><h1>Access Denied</h1><p>You are not allowed to access this page.</p></body>
</html>
ERRORDOC
        exit;
    }
}

=pod

=item C<DoubleCrypt>

Performs two crypt calls with the same salt, so that the limit of characters
in passwords is doubled from 8 to 16.  It's probably a good idea to use an MD5
hash or some other, more sophisticated alternative.

=cut

#sub DoubleCrypt
#{
    #my ($str, $salt) = @_;

    ## Eliminates warnings about substr beyond end of string.
    #if (length($str) > 8)
    #{
        #return crypt(substr($str, 0, 8), $salt) . crypt(substr($str, 8, 8), $salt);
    #}
    #else
    #{
        #return crypt($str, $salt) . crypt('', $salt);
    #}
#}

=pod

=item C<MD5Crypt>

Performs an MD5 hash on the password given and returns the hash as a 24-byte
Base64 string of the hash.  Requires the Digest::MD5 module.

This is used instead of DoubleCrypt if the -md5pwd option is set.

=cut

#sub MD5Crypt
#{
    #my ( $str ) = @_;

    #require Digest::MD5;
    #return Digest::MD5->new->add( $str )->b64digest;
#}

=pod

=back

=head1 NOTE ON SECURITY

Any hidden fields such as passwords are sent over the network in clear
text, so anyone with low-level access to the network (such as an ISP
owner or a lucky/skilled hacker) could read the passwords and gain
access to your application.  C<CGI::Auth> has no control over this since
it is currently a server-side-only solution.

If your application must be fully secured, an encryption layer such as
HTTPS should be used to encrypt the session so that passwords cannot be
snooped by unauthorized individuals.

It would be adequate to use HTTPS only for the login process, and avoid the
overhead of encryption during the rest of the session.  But I expect that this
would require modification of this module.

=head1 SEE ALSO

=over 4

=item *

L<CGI>

=item *

L<CGI::Simple>

=item *

L<HTML::Template>

=item *

L<CGI::Session>

=item *

L<CGI::Session::Auth>

=back

=head1 BUGS

C<CGI::Auth> doesn't use cookies, so it is left up to the script author to
ensure that auth data (i.e., the session file) is passed around consistently
through all links and entry forms.

=head1 AUTHOR

C. Chad Wallace, cmdrwalrus@canada.com

If you have any suggestions, comments or bug reports, please send them to me.
I will be happy to hear them.

=head1 COPYRIGHT AND LICENCE

Copyright (c) 2001, 2002, 2003 C. Chad Wallace.
All rights reserved.

This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself.

THIS PACKAGE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF
MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.

=cut

#package DatabaseTools;
#use strict;
#use Carp;
#use constant DBG => 1;
#sub new
#{
  #my $pkg = shift;
  #my $self; { my %hash; $self = bless(\%hash, $pkg); }

  #for (my $x = 0; $x <= $#_; $x += 2)
  #{
    #defined($_[($x + 1)]) or &croak("DBTOOLS::new() called with odd number of option parameters - should be of the form option => value");
    #$self->{lc($_[$x])} = $_[($x + 1)];
    ##print "loading hash lc($_[$x]) = $_[($x + 1)]\n";
  #}
  ##if ($self->{debug})
  ##{
    ##$fp->trace_if(1);
  ##}
  ##else
  ##{
    ##$fp->trace_if(0);
  ##}
  ##print "new called \n";
  #return $self;
#}

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
        $parms[$i] = $self->quote($parms[$i]);
        $self->{login_comments} .= "parm=".$parms[$i]."\n" if (exists($self->{trace}));
      }
      $sql = sprintf($rsql, @parms);
   }
   else
   {
      $sql = $rsql;
   }
   #DBG&&printf STDERR  ("\n".tools::trim_block($sql));
   $self->{login_comments} .= "get_rec [$sql]\n" if (exists($self->{trace}));
   ## print "$sql\n";
   ###   my $sth = $dbh->prepare("SELECT * FROM mytable");
   my @results = $self->{dbi}->selectrow_array($sql);
   # cluck if (!@results);
   $self->{login_comments}.="get_rec selectrow_array col returned = $#results [$sql]\n" if (exists($self->{trace}));
   if ($#results == 0 && defined($self->{dbi}->err))   # this is an sql error
   {
      $self->{login_comments} .= "get_rec selectrow_array failed $results[0]".$self->{dbi}->err.", ".$self->{dbi}->errstr."\n" if (exists($self->{trace}));
      return (0, $self->{dbi}->errstr);
   }
   elsif ($#results < 0) # this is nothing returned from query
   {
      $self->{login_comments} .= "get_rec returned zero records\n" if (exists($self->{trace}));
      return (0, "nothing found");
   }
   # print "[$self->{login_comments}]\n";
   return (1, @results);
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
        if (!defined $parms[$i] or $parms[$i] eq "")
        {
           $parms[$i]="NULL";
        }
        else
        {
          $parms[$i] = $self->quote($parms[$i]);
          $self->{login_comments} .= "parm=".$parms[$i]."\n" if (exists($self->{trace}));
        }
      }
       $sql = sprintf($rsql,@parms);
   }
   else
   {
      $sql = $rsql;
   }

   #print "do [".$sql."]\n";
   $self->{login_comments} .= "do [".$sql."]\n" if (exists($self->{trace}));
   for (my $i = 0; $i < 10; $i++)
   {
      my $stat = $self->{dbi}->do($sql);
      $self->{rows} = $stat;
      if (!$stat)
      {
         if ($self->{dbi}->err == 5) # locked
         {
             sleep(1);  # just a little wait for it to unlock
         }
         else
         {
            $self->{login_comments} .=  "sql do failed\n$sql\nUnable execute ".$self->{dbi}->err.", ".$self->{dbi}->errstr."\n";
            return (0, "sql do failed\n$sql\nUnable execute ".$self->{dbi}->err.", ".$self->{dbi}->errstr);
         }
      }
      else
      {
        return 1;
      }
   }
   return 0;
}

sub quote
{
   my ($self, $thing) = @_;
   return $self->{dbi}->quote($thing);
}

#sub get_pass
#{
   #my ($self, $user) = @_;
   #chomp $rsql;
   #$rsql=$self->trim($rsql);
   #my $sql;
   #if (@parms)
   #{
      #for (my $i = 0; $i <= $#parms; $i++)
      #{
        #if(!defined $parms[$i] or $parms[$i] eq "")
        #{
           #$parms[$i]="NULL";
        #}
        #else
        #{
          #$parms[$i] = $self->{dbi}->quote($parms[$i]);
          #$self->{login_comments} .= "parm=".$parms[$i]."\n" if (exists($self->{trace}));
        #}
      #}
       #$sql = sprintf($rsql,@parms);
   #}
   #else
   #{
      #$sql = $rsql;
   #}

   ##print "do [".$sql."]\n";
   #$self->{login_comments} .= "do [".$sql."]\n" if (exists($self->{trace}));
   #for (my $i = 0; $i < 10; $i++)
   #{
      #my $stat = $self->{dbi}->do($sql);
      #$self->{rows} = $stat;
      #if (!$stat)
      #{
         #if ($self->{dbi}->err == 5) # locked
         #{
             #sleep(1);  # just a little wait for it to unlock
         #}
         #else
         #{
            #$self->{login_comments} .=  "sql do failed\n$sql\nUnable execute ".$self->{dbi}->err.", ".$self->{dbi}->errstr."\n";
            #return 0, "sql do failed\n$sql\nUnable execute ".$self->{dbi}->err.", ".$self->{dbi}->errstr;
         #}
      #}
      #else
      #{
        #return 1;
      #}
   #}
   #return 0;
#}

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

sub parse_http_request
{
    my ($request) = @_;
    my %form;
    DBG&&printf STDERR  ("%s", $request);
    my $method;
    if ( $request =~ m'^(GET|POST|PUT) /(.*) HTTP/1\.[01]' )
    {
       my $get_or_post = $1;
       my $get_string = $2;
       DBG&&printf STDERR  ("get_or_post = %s", $get_or_post);
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
          DBG&&printf STDERR  ("post_string = [%s]", $p);
       }
       DBG&&printf STDERR  ("method = [%s]", $method||'?');
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
         DBG&&printf STDERR  ("[%s] = [%s]", $name, $value);

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

1;
