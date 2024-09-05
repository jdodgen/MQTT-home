package route_collection;

#use strict;
use Carp;
use Data::Dumper;
use XBeeZDO;
use cfg;
use filterPrint;

use tools;
use constant DEBUG => tools::DEBUG_route_collection;

my $fp = filterPrint->new();

# require Exporter;
# our ( @ISA, @EXPORT_OK, %EXPORT_TAGS );

sub save
{
    my ($dt, $rxin, $XbeeSendQueue) = @_;
    my $decoded = XBeeZDO::routing_table_responce($rxin->{data});
    my $list = $decoded->{list};
    $dt->do("update wireless_devices set na = %s, parent_network_address = %s where ah = %s AND al = %s",
           $rxin->{na}, 0xfffe,  $rxin->{sh}, $rxin->{sl});
    foreach my $entry (@$list)
    {
        #print "entry ", Dumper $entry, "\n";
        if ($entry->{rt_status} == 0)
        {
           # printf "route_collection::save ROUTE %x:%x na=%x dest=%x next=%x\n", $rxin->{sh}, $rxin->{sl}, $rxin->{na}, $entry->{dest_addr}, $entry->{next_hop};
           $dt->do("INSERT OR REPLACE INTO routing (ah,al,na,dest_addr,next_hop) VALUES (%s,%s,%s,%s,%s)",
               $rxin->{sh}, $rxin->{sl}, $rxin->{na}, $entry->{dest_addr}, $entry->{next_hop});
        }
    }
    # print "raw payload x", unpack("H*", $rxin->{data}), "\n";
    #printf "reply: %s\n",  Dumper $decoded;
    #printf "route_collection::save %s\n", Dumper $rxin;
}


sub clean
{
    my ($dt) = @_;
    $dt->do("update wireless_devices set na = NULL, parent_network_address = NULL");
    $dt->do("delete from routing");
}

sub get
{
    my ($dt, $XbeeSendQueue) = @_;
    my @routers =  $dt->tmpl_loop_query(<<EOF, (qw(part_nbr addr_h addr_l na)));
            SELECT part_nbr||'', ah, al, na FROM wireless_devices WHERE ah <> 'camera'
EOF
    foreach my $d (@routers){
        single($XbeeSendQueue,  $d->{part_nbr}, $d->{addr_h}, $d->{addr_l},  $d->{na});
    }
}

sub single
{
    my ($XbeeSendQueue, $part_nbr, $ah, $al, $na) = @_;

    DBG&&$fp->prt("route_collection:single: %s %s\n", $part_nbr||"none",  tools::location_string($al));
    #if ($part_nbr =~ /^R/) {

    if ($part_nbr)
    {
        if ($part_nbr =~ /^E/) {
        #    $XbeeSendQueue->enqueue({request => 'READ_REMOTE_XBEE_REGISTER', ah => $ah, al => $al, reg => "MP"}); # na + parent network address
        }
        else {
            $XbeeSendQueue->enqueue({request => 'ZDO', ah => $ah, al => $al, na => $na, cluster_id => 0x0032, payload => XBeeZDO::routing_table_request(0)});
        }
    }

}


1;



