# !/usr/bin/perl
use strict;
my $yn;
print "auto run all steps (Yn)?";
my $runall = <STDIN>;
get_packages();
build_pm();
#make_python();
make_fauxmo();
fix_bashrc();
enlarge_msg_queues();
fix_swappiness();
make_directories();
edit_mingetty();
##make_posix_mq();

$ENV{'PERL_LWP_SSL_VERIFY_HOSTNAME'} = 0;

sub get_packages
{

    print "apt-get packages(Yn)? ";
    $yn = ($runall =~ /n/) ? <STDIN> : 'Y';
    return if ($yn =~ /n/);
    print "doing updates and upgrades\n";
    system ('yes \'\' | apt-get update');
    system ('yes \'\' | apt-get upgrade');
    system ('yes \'\' | apt-get dist-upgrade');

    print "installing packages\n";

    system ('yes \'\' | apt-get install autoconf automake pkgconf libtool build-essential  libzip-dev unzip libffi-dev');
    #system ('yes \'\' | apt-get install ffmpeg libavformat-dev  libavcodec-dev   libavutil-dev   libswscale-dev transcode');  ##  libav-tools

    print "installing other packages\n";
    system ('yes \'\' | apt-get install pkg-config gcc zlib1g-dev mingetty libssl-dev make libz-dev yasm sqlite3 iputils-ping');

    print "remove cloud-init\n";
    system ('yes \'\' | apt-get purge cloud-init');
    system ('rm -rf /etc/cloud/');
    system ('rm -rf /var/lib/cloud/');

    system ('yes \'\' | apt install net-tools preload unzip python3-pip');
    system ('yes \'\' | pip3 install requests');
    system ('yes \'\' | apt-get remove brltty');
    system ('yes \'\' | apt-get autoremove');


    print "packages loaded\n";

}

#sub fix_sudoers
#{
    #print "fix_sudoers (Yn)? ";
    #$yn = ($runall =~ /n/) ? <STDIN> : 'Y';
    #return if ($yn =~ /n/);
    #my $tail = <<EOF;
#www-data ALL=(ALL) NOPASSWD:ALL
#EOF
     #open(PLOT,">>/etc/sudoers") || die("sudoers file will not open!");
     #print PLOT $tail;
     #close(PLOT);
     #print "sudoers modified\n";
#}

sub enlarge_msg_queues
{
    print "enlarge_msg_queues (Yn)? ";
    $yn = ($runall =~ /n/) ? <STDIN> : 'Y';
    return if ($yn =~ /n/);
    my $tail = <<EOF;
* hard msgqueue 8388608
* soft msgqueue 8388608
EOF
     open(PLOT,">>/etc/security/limits.conf") || die("limits.conf file will not open!");
     print PLOT $tail;
     close(PLOT);
     print "queue space enlarged\n";
}

sub fix_bashrc
{
    print "fix_bashrc (Yn)? ";
    $yn = ($runall =~ /n/) ? <STDIN> : 'Y';
    return if ($yn =~ /n/);

     my $tail = <<EOF;
echo
echo '********************************************'
echo 'this is the AlertAway start up'
echo 'Copyright 2012-2020 Jim Dodgen'
echo 'control C to interupt now'
umask 0000
preload
setterm -blank 0
ulimit -q 536870912
sleep 20
/usr/bin/perl /root/loader.pl
cd /alertaway
/usr/bin/perl -I /alertaway /alertaway/alertaway_init.pl
/usr/bin/perl -I /alertaway /alertaway/HomeMonitor.pl
echo rebooting now control C to stop reboot
sleep 20
reboot
EOF
     open(PLOT,">>.bashrc") || die(".bashrc file will not open!");
     print PLOT $tail;
     close(PLOT);
     print "bashrc modified\n";
}

sub fix_swappiness
{
    print "fix_swappiness (Yn)? ";
    $yn = ($runall =~ /n/) ? <STDIN> : 'Y';
    return if ($yn =~ /n/);
    {
        my $tail = <<EOF;
vm.swappiness=10
EOF

        open(PLOT,">>/etc/sysctl.conf") || die(".bashrc file will not open!");
        print PLOT $tail;
        close(PLOT);

        print "bashrc modified\n";
   }
}

sub make_directories
{
    mkdir "/root/pgm";
    mkdir "/root/perl";
}

sub build_pm
{
    print "Make perl modules (Yn)? ";
    $yn = ($runall =~ /n/) ? <STDIN> : 'Y';
    return if ($yn =~ /n/);

    my @modules = split /\n/, <<EOF;
CPAN
inc::latest
Try::Tiny
YAML
YAML::Tiny
File::Remove
Mozilla::CA
Digest::HMAC
Net::IP
Authen::SASL
Net::SSLeay
IO::Socket::SSL
IO::Pty
libnet
Convert::UU
DBI
DBD::SQLite
Net::HTTP
libwww::perl
HTTP::Date
HTTP::Message
HTML::Parser
LWP::UserAgent
Device::SerialPort
File::ShareDir
HTML::Template
Locale::Msgfmt
Net::DNS
Net::OpenSSH
Net::SFTP::Foreign
LWP::Protocol::https
URI
LWP::MediaTypes
Filesys::Df
Crypt::Password
Math::Int64
CryptX
File::HomeDir
File::Which
Crypt::Curve25519
Path::Class
Crypt::Password
Astro::Sunrise
POSIX::RT::MQ
Text::CSV
EOF

# Net::FTPSSL, Net::SSH::Perl, Net::SFTP  not used anymore

    foreach my $m (@modules)
    {
        printf "\n>>>>installing [%s]<<<<<\n\n", $m;
        system ("yes '' | cpan install $m");
    }
}

sub edit_mingetty
{
    # my $systemd = q(sed -i '/^ExecStart/ c\ExecStart=-/sbin/mingetty --autologin root tty1' /etc/systemd/system/getty.target.wants/getty@tty1.service);
    print "edit_mingetty (Yn)? ";
    $yn = ($runall =~ /n/) ? <STDIN> : 'Y';
    return if ($yn =~ /n/);
    if (-d '/etc/systemd/system/getty.target.wants')  # using systemd
    {
        my $systemd = <<EOF;
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I 38400 linux
EOF

        mkdir '/etc/systemd/system/getty@tty1.service.d';
        open(TTY,q(>/etc/systemd/system/getty@tty1.service.d/autologin.conf)) || die("autologin.conf file will not open/create!");
        print TTY $systemd;
        close(TTY);
    }
    elsif (-d '/etc/init')  # pre 15 ubuntu
    {
        system 'vi /etc/init/tty1.conf'; # (ubuntu)
    }
    else
    {
        system 'vi /etc/inittab'; #  (debian)
    }
}

sub make_python
{
    chdir '/root';
    system 'tar -xvf Python-3.8.2.tgz*';
    chdir "Python-3.8.2";
    system './configure';
    system 'make';
    system 'make install';
    chdir '/root';
}

sub make_fauxmo
{
    chdir '/root';
    #system "unzip fauxmo-master.zip"
    #chdir "fauxmo-master";
    #system('python3 -m venv .venv');
    system('python3 -m pip install fauxmo');
}

#sub make_posix_mq
#{
    #system 'tar -xvf POSIX-RT-MQ.tar.gz';
    #system ("cd POSIX-RT-MQ*;yes \"\" | perl Makefile.PL;yes \"\" | make;make install;cd ..");
#}



