use Net::OpenSSH;
use strict;

$Net::OpenSSH::debug = (~512);

$IO::Tty::DEBUG = 1;

my $ssh = Net::OpenSSH->new("192.168.0.5",
    user => "foo",
    password => "bar",
    # master_opts => [-o => "StrictHostKeyChecking=no"]
    );
if ($ssh)
{
    printf(">>>>>>>>>>connected[%s]\n", $ssh->error);
}
else
{
    print(">>>>>>>>>>failed[%s]\n", $ssh->error);
}

my ($in, $out, $pid) = $ssh->open2("cat")
        or die "unable to write file: " . $ssh->error;

print(">>>>>>>>>>after system\n");

print $in "hello,world\n";
print (">>>>>>>>>>after send\n");
my $result = readline($out);
chomp $result;
printf ("result 1 [%s]\n", $result);

print $in "How are you doing\n";
print (">>>>>>>>>>after send\n");
$result = readline($out);
chomp $result;
printf ("result 2 [%s]\n", $result);

sleep(60);


=run
$ sudo perl ssh_test.pl
# open_ex: ['ssh','-V']
# io3 mloop, cin: 0, cout: 1, cerr: 0
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 60 at offset 0
#> 4f 70 65 6e 53 53 48 5f 37 2e 36 70 31 20 55 62 75 6e 74 75 2d 34 75 62 75 6e 74 75 30 2e 33 2c | OpenSSH_7.6p1 Ubuntu-4ubuntu0.3,
#> 20 4f 70 65 6e 53 53 4c 20 31 2e 30 2e 32 6e 20 20 37 20 44 65 63 20 32 30 31 37 0a             |  OpenSSL 1.0.2n  7 Dec 2017.
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 0 at offset 60
# leaving _io3()
# _waitpid(32231) => pid: 32231, rc: 0, err: 
# OpenSSH version is 7.6p1
# ctl_path: /root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4, ctl_dir: /root/.libnet-openssh-perl/
# _is_secure_path(dir: /root/.libnet-openssh-perl, file mode: 16832, file uid: 0, euid: 0
# _is_secure_path(dir: /root, file mode: 16832, file uid: 0, euid: 0
# set_error(0 - 0)
trying posix_openpt()...
trying grantpt()...
trying unlockpt()...
trying ptsname_r()...
trying to open /dev/pts/4...
trying to I_PUSH ptem...
trying to I_PUSH ldterm...
trying to I_PUSH ttcompat...
# call args: ['ssh','-o','ServerAliveInterval=30','-o','ControlPersist=no','-2MNx','-o','NumberOfPasswordPrompts=1','-o','PreferredAuthentications=keyboard-interactive,password','-S','/root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4','-l','foo','192.168.0.5','--']
# master state jumping from _STATE_START to _STATE_LOGIN
# file object not yet found at /root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4, state:_STATE_LOGIN
# file object not yet found at /root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4, state:_STATE_LOGIN
# file object not yet found at /root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4, state:_STATE_LOGIN
# passwd/passphrase requested (foo@192.168.0.5's password:)
# file object not yet found at /root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4, state:_STATE_AWAITING_MUX
# file object not yet found at /root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4, state:_STATE_AWAITING_MUX
# file object found at /root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4
# master state jumping from _STATE_AWAITING_MUX to _STATE_RUNNING
# call args: ['ssh','-O','check','-T','-S','/root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4','-l','foo','192.168.0.5','--']
# open_ex: ['ssh','-O','check','-T','-S','/root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4','-l','foo','192.168.0.5','--']
# io3 mloop, cin: 0, cout: 1, cerr: 0
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 28 at offset 0
#> 4d 61 73 74 65 72 20 72 75 6e 6e 69 6e 67 20 28 70 69 64 3d 33 32 32 33 32 29 0d 0a             | Master running (pid=32232)..
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 0 at offset 28
# leaving _io3()
# _waitpid(32233) => pid: 32233, rc: 0, err: 
>>>>>>>>>>connected[0]
# call args: ['ssh','-S','/root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4','-l','foo','192.168.0.5','--','cat']
# open_ex: ['ssh','-S','/root/.libnet-openssh-perl/a58e1bb1623e93c13f137e35c6e909f4','-l','foo','192.168.0.5','--','cat']
>>>>>>>>>>after system
>>>>>>>>>>after send
result 1 [hello,world]
>>>>>>>>>>after send
result 2 [How are you doing]
=end
