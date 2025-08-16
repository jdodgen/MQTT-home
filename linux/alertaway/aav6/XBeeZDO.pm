package XBeeZDO;

use strict;
use Carp;
use Data::Dumper;

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

sub routing_table_request
{
    my ($start_index) = @_;
    my $data = pack 'CC',5, $start_index;
    #print "sending raw payload x", unpack("H*", $data), "\n";
    return $data;
}

sub routing_table_responce
{
    my ($data) = @_;
    my %resp;
    ($resp{Trans_seq_nbr}, $resp{status}, $resp{routing_table_entries}, $resp{start_index}, my $routing_table_list_count, my $entries)
           = unpack 'CCCCCa*', $data;
    $resp{routing_table_list_count} = $routing_table_list_count;
    my @list;
    while ($routing_table_list_count--) {
        my %entry;
        ($entry{dest_addr}, my $bits, $entry{next_hop},$entries) = unpack 'vCva*', $entries;
        $entry{reserved} = ( $bits >> 6 ) & 0x3;
        $entry{route_rec_req} = ( $bits >> 5 ) & 0x1;
        $entry{many_to_one_flag} = ( $bits >> 4 ) & 0x1;
        $entry{memory_const_flag} = ( $bits >> 3 ) & 0x1;
        $entry{rt_status} = $bits & 0x7;
        push @list, \%entry;
    }
    $resp{list} = \@list;
    # printf "rtr %s\n", Dumper \%resp;
    return \%resp;
}
1;
