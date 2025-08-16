package ZigbeeHomeAutomation;

use strict;
use Carp;
use Data::Dumper;

use filterPrint;
my $fp = filterPrint->new();
use constant DBG => 1;

#Changes supporting ZHA and ZLL for xbee devices
#Zigbee Stack Profile  (ZS) 2  Note: all devices must be set the same
#Encryption Enable  (EE) 1
#Encryption Options (EO) 0
#Encryption Key  (KY) 5a6967426565416c6c69616e63653039
#also good to set voltage reporting threshold V+ to ffff so it always reports voltage

require Exporter;
our ( @ISA, @EXPORT_OK, %EXPORT_TAGS );

use constant NEIGHBOR_TABLE_REQUEST  => 0x0031; ## Management LQI (Neighbor Table) Request
use constant NEIGHBOR_TABLE_RESPONCE => 0x8031; ## Management LQI (Neighbor Table) Response
use constant ROUTING_TABLE_REQUEST   => 0x0032; ## Management Rtg (Routing Table) Request
use constant ROUTING_TABLE_RESPONCE  => 0x8032; ## Management Rtg (Routing Table) Response

use constant ZDO_COMMAND_TO_STRING => {
    0x0031 => 'NEIGHBOR_TABLE_REQUEST',
    0x8031 => 'NEIGHBOR_TABLE_RESPONCE',
    0x0032 => 'ROUTING_TABLE_REQUEST',
    0x8032 => 'ROUTING_TABLE_RESPONCE'
};

sub new
{
    my ($class, $options) = @_;
    my $self = {};
    $self->{dt} = $options->{dt};
    $self->{name} = 'ZHA';

    $self->{api} = $options->{api};
    bless $self, $class;
    return $self;
}

sub ha_simple_desc
{
    my ($self, $addr_high,$addr_low, $na,  $endpoint) = @_;
    my $cluster_id = 0x0004;
    my $profile_id = 0;
    my $payload = pack('CvC', 0xAA,  $na, $endpoint);
    my $fid = 2;
    DBG&&$fp->prt(":ha_simple_desc $endpoint\n");
    die "ZigbeeHomeAutomation:IdentifyDevice: aborting, Failed to transmit"
    unless $self->{api}->ZBExp(
      {
      sh        => $addr_high,
      sl        => $addr_low,
      na        => $na,
      frame_id  => $fid,
      source_endpoint => 0,
      destination_endpoint =>  0
      }, $profile_id, $cluster_id, $payload);
    return $fid;
}

sub ha_endpoints
{
    my ($self, $addr_high, $addr_low, $na) = @_;
    my $cluster_id = 0x0005;
    my $profile_id = 0;
    my $payload = pack('Cv', 0xAA,  $na);
    my $fid = 2;
    DBG&&$fp->prt("get");
    die "ZigbeeHomeAutomation:IdentifyDevice: aborting, Failed to transmit"
    unless $self->{api}->ZBExp(
      {
      sh        => $addr_high,
      sl        => $addr_low,
      na        => $na,
      frame_id  => $fid,
      source_endpoint => 0,
      destination_endpoint =>  0
      }, $profile_id, $cluster_id, $payload);
    return $fid;
}

sub turn_on_off
{
    my ($self, $addr_high, $addr_low, $na, $endpoint, $profile_id, $logic, $state, $fid) = @_;
    if ($logic eq 'BINARY')
    {
        #$profile_id = 0x104;
        my $cluster_id = 0x0006;
        my $payload = pack('C*', 0x11, 0xbb, $state);
        #my $payload = pack('C*', 0x01, 0x00, $state);

        DBG&&$fp->prt("end_point[%0X] %s Profile_id[%0X] state[%0X]\n",
             $endpoint, tools::location_string($addr_low), $profile_id||0, $state);
        die "ZigbeeHomeAutomation:turn_on_off: aborting, Failed to transmit"
        unless $self->{api}->ZBExp(
          {
          sh        => $addr_high,
          sl        => $addr_low,
          na        => $na,
          frame_id  => $fid,
          source_endpoint => 0,
          destination_endpoint => $endpoint, #1, #$endpoint
          }, $profile_id, $cluster_id, $payload);
          get_on_off($self, $addr_high, $addr_low, $na, $endpoint, $profile_id, 1);
          # get_on_off($self->{api}, $addr_high, $addr_low, $na, $endpoint, $profile_id);
    }
}

sub get_on_off
{
    my ($self, $addr_high, $addr_low, $na, $endpoint, $profile_id, $fid) = @_;
    my $cluster_id = 0x0006;
    # my $profile_id = 0x0104;
    my $payload = pack('C*', 0x0,0xee,0x00,0x00,0x00,0x00,0x10,0x00,0x00,0x00,0x40,0x00,0x00);
    DBG&&$fp->prt("%s Profile_id[%0X]", tools::location_string($addr_low), $profile_id||0);
    die "ZigbeeHomeAutomation:get_on_off: aborting, Failed to transmit fid[$fid]"
    unless $self->{api}->ZBExp(
      {
      sh        => $addr_high,
      sl        => $addr_low,
      na        => $na,
      frame_id  => $fid,
      source_endpoint => 0,
      destination_endpoint =>  $endpoint
      }, $profile_id, $cluster_id, $payload);
}

sub match_descriptor_responce  # from a 8004
{
    my ($self, $addr_high, $addr_low, $na, $profile_id) = @_;
    my $cluster_id = 0x8006;
    #my $profile_id = 0x104;
    my $payload = pack('CCvCc',  0x0,0xbb,$na,0x01,0x19);
    my $fid = 2;
    DBG&&$fp->prt("sent");
    die "ZigbeeHomeAutomation:match_descriptor_responce: aborting, Failed to transmit"
    unless $self->{api}->ZBExp(
      {
      sh        => $addr_high,
      sl        => $addr_low,
      na        => $na,
      frame_id  => $fid,
      source_endpoint => 0,
      destination_endpoint => 0
      }, $profile_id, $cluster_id, $payload);
    return $fid;
}

sub set_unit_type # from a 8004     simple switch [Device ID: 0x010a]
{
    my ($self, $rx) = @_;
    DBG&&$fp->prt("data %s\n",  tools::hexDumper("",$rx->{data}));
    my $data = $rx->{data};
    my $device_type;
    my $valid_ha_ll_profile_id = 0;
    DBG&&$fp->prt("profile_id[%0x] device_type [%0x]", $data->{profile_id}||0x99999999, $data->{device_type});
    #if ($data->{profile_id} == 0xc105 && $data->{device_type} == 0x1) # ZHA home automation profile ? GE wall switch ?
    #{
            #$device_type = 'ZHAx100';
            #$valid_ha_ll_profile_id = 1;
    #}
    if ($data->{profile_id} == 0x104) # ZHA home automation profile
    {
        if ($data->{device_type} == 0x100)
        {
            $device_type = 'ZHAx100';
            $valid_ha_ll_profile_id = 1;
        }
        elsif ($data->{device_type} == 0x09 or $data->{device_type} == 0x51)
        {
            $device_type = 'ZHAx9';
            $valid_ha_ll_profile_id = 1;
        }
        elsif ($data->{device_type} == 0x101)
        {
            $device_type = 'ZHA0x101';
            $valid_ha_ll_profile_id = 1;
        }
        elsif ($data->{device_type} == 0x402)
        {
            $device_type = 'ZHA0x402';
            $valid_ha_ll_profile_id = 1;
        }
        else
        {
            $device_type = 'HA unknown ';
            DBG&&$fp->prt("set_unit_type HA  profile_id[%0x] unknown device_type[%0X]\n", $data->{profile_id}, $data->{device_type});
        }
    }
    elsif ($data->{profile_id} == 0xC05E) # GLL  Light Link profile
    {
        if ($data->{device_type} == 0x1)
        {
            $device_type = 'GLLx1';
            $valid_ha_ll_profile_id = 1;
        }
        elsif ($data->{device_type} == 0x0)
        {
            $device_type = 'GLLx0';
            $valid_ha_ll_profile_id = 1;
        }
        elsif ($data->{device_type} == 0x10)
        {
            $device_type = 'GLLx10';
            $valid_ha_ll_profile_id = 1;
        }
        elsif ($data->{device_type} == 0x100)
        {
            $device_type = 'GLLx100';
            $valid_ha_ll_profile_id = 1;
        }
        else
        {
            $device_type = 'LL unknown';
        }
    }
    else
    {
        DBG&&$fp->prt("set_unit_type unknown profile_id %s, device_type = %s", $data->{profile_id}, $data->{device_type});
    }

    # this code
    if ($valid_ha_ll_profile_id)
    {
        my ($status, $pn) = $self->{dt}->get_rec("SELECT  part_nbr FROM wireless_devices WHERE ah = %s AND al = %s", $rx->{sh}, $rx->{sl});
        if (!$status)
        {
            insert_ha($self, $rx->{sh}, $rx->{sl},$rx->{na},'ZHA', time, time);
        }
        $status = $self->{dt}->do(<<EOF,  $device_type, $data->{profile_id}, $data->{endpoint}, $rx->{sh}, $rx->{sl});
            UPDATE wireless_devices SET part_nbr = %s, profile_id = %s, endpoint =  %s  WHERE ah = %s AND al = %s
EOF
        process_packet::insert_port_rows($self->{dt}, $rx->{sh}, $rx->{sl}, $rx->{timestamp});
    }
}

sub insert_ha
{
    my ($self, $addr_high, $addr_low, $na, $part_nbr_in, $now, $prev) = @_;
    my $loc_string = tools::location_string($addr_low);
    $self->{dt}->do(<<EOF, $addr_high, $addr_low, $na, $loc_string, $part_nbr_in, $now, $prev);
    INSERT OR REPLACE INTO wireless_devices (ah, al, na, physical_location, part_nbr, last_time_in, previous_time_in)
        VALUES (%s,%s,%s,%s,%s,%s,%s);
EOF
}

1;
