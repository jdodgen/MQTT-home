use Net::OpenSSH;
use strict;

$Net::OpenSSH::debug = (~512);

$IO::Tty::DEBUG = 1;

my $ssh = Net::OpenSSH->new("192.168.0.5",
    user => "foo",
    password => "bar",
    );
if ($ssh)
{
    printf(">>>>>>>>>>connected[%s]\n", $ssh->error);
}
else
{
    printf(">>>>>>>>>>failed[%s]\n", $ssh->error);
}

my ($in, $out, $pid) = $ssh->open2("cat")
        or die "unable to write file: " . $ssh->error;

printf ">>>>>>>>>>after open2[%s]\n", $ssh->error;

=pod
--------------output----------------
$ sudo perl -I . ssh_test_with_strict.pl
# open_ex: ['ssh','-V']
# io3 mloop, cin: 0, cout: 1, cerr: 0
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 60 at offset 0
#> 4f 70 65 6e 53 53 48 5f 37 2e 36 70 31 20 55 62 75 6e 74 75 2d 34 75 62 75 6e 74 75 30 2e 33 2c | OpenSSH_7.6p1 Ubuntu-4ubuntu0.3,
#> 20 4f 70 65 6e 53 53 4c 20 31 2e 30 2e 32 6e 20 20 37 20 44 65 63 20 32 30 31 37 0a             |  OpenSSL 1.0.2n  7 Dec 2017.
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 0 at offset 60
# leaving _io3()
# _waitpid(14652) => pid: 14652, rc: 0, err:
# OpenSSH version is 7.6p1
# ctl_path: /root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80, ctl_dir: /root/.libnet-openssh-perl/
# _is_secure_path(dir: /root/.libnet-openssh-perl, file mode: 16832, file uid: 0, euid: 0
# _is_secure_path(dir: /root, file mode: 16832, file uid: 0, euid: 0
# set_error(0 - 0)
trying posix_openpt()...
trying grantpt()...
trying unlockpt()...
trying ptsname_r()...
trying to open /dev/pts/3...
trying to I_PUSH ptem...
trying to I_PUSH ldterm...
trying to I_PUSH ttcompat...
# call args: ['ssh','-o','ServerAliveInterval=30','-o','ControlPersist=no','-2MNx','-o','NumberOfPasswordPrompts=1','-o','PreferredAuthentications=keyboard-interactive,password','-S','/root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80','-l','foo','192.168.0.5','--']
# master state jumping from _STATE_START to _STATE_LOGIN
# file object not yet found at /root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80, state:_STATE_LOGIN
# file object not yet found at /root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80, state:_STATE_LOGIN
# file object not yet found at /root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80, state:_STATE_LOGIN
# passwd/passphrase requested (foo@192.168.0.5's password:)
# file object not yet found at /root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80, state:_STATE_AWAITING_MUX
# file object not yet found at /root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80, state:_STATE_AWAITING_MUX
# file object found at /root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80
# master state jumping from _STATE_AWAITING_MUX to _STATE_RUNNING
# call args: ['ssh','-O','check','-T','-S','/root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80','-l','foo','192.168.0.5','--']
# open_ex: ['ssh','-O','check','-T','-S','/root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80','-l','foo','192.168.0.5','--']
# io3 mloop, cin: 0, cout: 1, cerr: 0
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 28 at offset 0
#> 4d 61 73 74 65 72 20 72 75 6e 6e 69 6e 67 20 28 70 69 64 3d 31 34 36 35 34 29 0d 0a             | Master running (pid=14654)..
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 0 at offset 28
# leaving _io3()
# _waitpid(14655) => pid: 14655, rc: 0, err:
>>>>>>>>>>connected[0]
# call args: ['ssh','-S','/root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80','-l','foo','192.168.0.5','--','cat']
# open_ex: ['ssh','-S','/root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80','-l','foo','192.168.0.5','--','cat']
>>>>>>>>>>after open2[0]
# DESTROY(Net::OpenSSH=HASH(0x55c6d4387dd0), pid: 14654)
# sending exit control to master
# call args: ['ssh','-O','exit','-T','-S','/root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80','-l','foo','192.168.0.5','--']
# open_ex: ['ssh','-O','exit','-T','-S','/root/.libnet-openssh-perl/def0802dc7ea01567816b6d8b3ccec80','-l','foo','192.168.0.5','--']
# io3 mloop, cin: 0, cout: 1, cerr: 0
# io3 fast, cin: 0, cout: 1, cerr: 0
mux_client_request_session: read from master failed: Broken pipe
# stdout, bytes read: 20 at offset 0
#> 45 78 69 74 20 72 65 71 75 65 73 74 20 73 65 6e 74 2e 0d 0a                                     | Exit request sent...
# io3 fast, cin: 0, cout: 1, cerr: 0
# stdout, bytes read: 0 at offset 20
# leaving _io3()
# _waitpid(14657) => pid: 14657, rc: 0, err:
# set_error(1 - aborted)
# master state jumping from _STATE_RUNNING to _STATE_KILLING
# master 14654 exited, rc:65280, err:
# master state jumping from _STATE_KILLING to _STATE_GONE
jim@dev:~/Dropbox/source/aav6$ foo@192.168.0.5's password:
Permission denied, please try again.
foo@192.168.0.5's password:
Permission denied, please try again.
foo@192.168.0.5's password:
foo@192.168.0.5: Permission denied (publickey,password).
=cut
