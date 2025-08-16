package ip_tools;
# Copyright 2011,2012 by James E Dodgen Jr.  All rights reserved.

# use Net::DNS;
use Net::Ping;
use tools;
use strict;
use filterPrint;
my $fp = filterPrint->new();
#use constant DBG => 0;
my  $ifconfig = "/sbin/ifconfig"; #used for getting the IP address
my $last_ip_read_time = 1;
my $last_ip;
sub get_ip_addr
{
    my ($cfg, $WorkerBeeQueue) = @_;
    #lock $last_ip_read_time;
    my $interface = $cfg->{ethernet_port};
    DBG&&printf("[%s] Ethernet port [%s]\n", tools::whocalled(), $interface);
    my $now = time;
    my $tries = 10;
    while($tries--)
    {
        if ($now > $last_ip_read_time + 3600 || !$last_ip)  # Only check every hour
        {
           my @lines     = qx|$ifconfig $interface|
             or die( "Can't get info from ifconfig: " . $! . $interface);
           $last_ip = undef;
           foreach (@lines)
           {
               if (/inet\s(addr:)*([\d.]+)/)
               {
                   $last_ip = $2;
                   # print "new ";
                   $last_ip_read_time = $now;
                   last;
               }
           }
       }
       last if ($last_ip);
       sleep(1);
   }
   if ($last_ip)
   {
      # got it!
   }
   elsif ($WorkerBeeQueue)
   {
      my $msg = tools::whocalled();
      $WorkerBeeQueue->enqueue({request => "LOG", fmt => "no IP address found, probable DHCP fail, no connection? $msg"});
      $last_ip = 'NO.IP.ADDRESS.found';
   }
   return $last_ip;
}

sub set_ip
{
    my ($dt) = @_;

    my $rc = 0;

    my $cfg = tools::get_config($dt);
    if ($cfg->{connection_type} eq 'DHCP') # this works all the time, so just get out
    {
        set_ip_dhcp($cfg->{ethernet_port});
        $rc = 0;
    }
    else # lets see if the primary one works
    {
        set_ip_static($cfg->{ethernet_port},$cfg->{static_ip},$cfg->{subnet_mask},
                     $cfg->{gateway},  $cfg->{dns1}, $cfg->{dns2});
        if (check_network_health() == 0) # did not work
        {
             if ($cfg->{lw_connection_type} eq 'DHCP') # this works all the time, so just get out
             {
                set_ip_dhcp($cfg->{ethernet_port});
                $rc = 1;
             }
             else # lets try the secondary (AKA last working lw_ )
             {
               set_ip_static($cfg->{ethernet_port},$cfg->{lw_static_ip},$cfg->{lw_subnet_mask},
                             $cfg->{lw_gateway},  $cfg->{lw_dns1}, $cfg->{lw_dns2});
               if (check_network_health() == 0) # did not work again
               {
                   set_ip_dhcp($cfg->{ethernet_port});
                   $rc = 2;
               }
               else
               {
                   $rc = 1;
               }
             }

         }
         else # primary worked
         {
            $rc = 0;
         }
    }
    $last_ip_read_time=0;
    if ($cfg->{camera_ip} && $cfg->{camera_ip} > '' && $cfg->{camera_ethernet_port} && $cfg->{camera_ethernet_port} > "")
    {
        my $camaraNet = "ip addr add ".$cfg->{camera_ip}."/24 dev ".$cfg->{camera_ethernet_port};
        system($camaraNet);
    }

    return $rc; # 0 = primary worked, 1 = backup worked, 2 = both failed reverted to DHCP
}

sub set_ip_dhcp
{
  my ($port) = @_;
  my $interfaces_file = <<EOF;
# configured from AlertAway DHCP
#
network:
 ethernets:
  $port:
   dhcp4: yes
EOF
  drop_netplan($interfaces_file);
}

##sudo ip addr add 192.168.2.2/24 dev enp1s0

##sudo ip link set dev enp1s0 up



sub save_port
{
    my ($dt) = @_;
    my $port;
    while (1)
    {
        my @result = split "\n", `netstat -r | grep "^default"`;
        my ($default, @other) = @result;
        #print "ip_tools::save_port: netstat line [$default]\n";
        chomp $default;
        $default =~ /.+\s(.*)$/;
        $port = $1;
        $fp->prt("ip_tools::save_ports: primary port = [$port]");
        last if ($port);
        sleep(2);
    }
    $dt->do("update config set ethernet_port = %s", $port) if $dt;
}

#save_ports();


sub set_ip_static
{
    my ($port, $ip, $mask, $gw, $dns1, $dns2) = @_;
    my $cider = mask_to_cidr($mask);
    my $dns_string1 ='';
    my $dns_string2 ='';
    if ($dns1 && $dns2)
    {
        $dns_string1 = "nameservers:";
        $dns_string2 = "addresses: [$dns1, $dns2]";
    }
    elsif ($dns1)
    {
        $dns_string1 = "nameservers:";
        $$dns_string2 = "addresses: [$dns1]";
    }
    elsif ($dns2)
    {
        $dns_string1 = "nameservers:";
        $dns_string2 = "addresses: [$dns2]";
    }
  my $interfaces_file = <<EOF;
# configured from simpleNVR static IP
#
network:
 version: 2
 ethernets:
  $port:
    dhcp4: no
    addresses: [$ip/$cider]
    gateway4: $gw
    optional: true
    $dns_string1
      $dns_string2
EOF
  drop_netplan($interfaces_file);
}

sub drop_netplan
{
  my($interfaces_file) = @_;
  my $yaml = "/etc/netplan/01-net.yaml";
  system('sudo rm  /etc/netplan/*.yaml');
  system("sudo touch $yaml");
  system("sudo chmod 666 $yaml");
  open FILE, '>'.$yaml or die "cannot open $yaml for writing: $!";
  print FILE $interfaces_file;
  close FILE;
  system('sudo /usr/sbin/netplan apply');
}

sub check_network_health
{
    system ($ifconfig);
    return 1;

    my $host = 'gmail.com';
    my $rc = 0;
    for (my $i=0;$i < 10; $i++)
    {
        my $p = Net::Ping->new();
        if ($p->ping($host))
        {
            DBG&&$fp->prt("$host is alive.");
            $rc = 1;
            last;
        }
        $p->close();
        sleep 1;
    }
    return $rc;
}

sub mask_to_cidr
{
    my($mask) = @_;
    my($byte1, $byte2, $byte3, $byte4) = split(/\./,$mask);
    my $num = ($byte1 * 16777216) + ($byte2 * 65536) + ($byte3 * 256) + $byte4;
    my $bin = unpack("B*", pack("N", $num));
    return ($bin =~ tr/1/1/);
}

#printf "port = %s\n", get_port();
#printf "port = %s\n", get_port();

#printf "ip=%s\n", scalar get_ip_addr();
print mask_to_cidr("255.255.255.0");
1;
