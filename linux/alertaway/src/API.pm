package API;  #changed local copy jed

use strict;
use Carp;
use Data::Dumper;
$Data::Dumper::Sortkeys = 1;

require Exporter;
our ( @ISA, @EXPORT_OK, %EXPORT_TAGS );

our $VERSION = 0.6;

use IO::Select;
use constant 1.01;
use constant XBEE_API_TYPE__MODEM_STATUS                             => 0x8A;
use constant XBEE_API_TYPE__AT_COMMAND                               => 0x08;
use constant XBEE_API_TYPE__AT_COMMAND_QUEUE_PARAMETER_VALUE         => 0x09;
use constant XBEE_API_TYPE__AT_COMMAND_RESPONSE                      => 0x88;
use constant XBEE_API_TYPE__REMOTE_COMMAND_REQUEST                   => 0x17;
use constant XBEE_API_TYPE__REMOTE_COMMAND_RESPONSE                  => 0x97;
use constant XBEE_API_TYPE__ZIGBEE_TRANSMIT_REQUEST                  => 0x10;
use constant XBEE_API_TYPE__EXPLICIT_ADDRESSING_ZIGBEE_COMMAND_FRAME => 0x11;
use constant XBEE_API_TYPE__ZIGBEE_TRANSMIT_STATUS                   => 0x8B;
use constant XBEE_API_TYPE__ZIGBEE_RECEIVE_PACKET                    => 0x90;
use constant XBEE_API_TYPE__ZIGBEE_EXPLICIT_RX_INDICATOR             => 0x91;
use constant XBEE_API_TYPE__ZIGBEE_IO_DATA_SAMPLE_RX_INDICATOR       => 0x92;
use constant XBEE_API_TYPE__XBEE_SENSOR_READ_INDICATOR_              => 0x94;
use constant XBEE_API_TYPE__NODE_IDENTIFICATION_INDICATOR            => 0x95;
use constant XBEE_API_TYPE__ROUTE_RECORD_INDICATOR                   => 0xA1;

use constant XBEE_API_TYPE_TO_STRING => {
    0x00 => 'NOT FROM XBEE',
    0x8A => 'MODEM_STATUS',
    0x08 => 'AT_COMMAND',
    0x09 => 'AT_COMMAND_QUEUE_PARAMETER_VALUE',
    0x88 => 'AT_COMMAND_RESPONSE',
    0x17 => 'REMOTE_COMMAND_REQUEST',
    0x97 => 'REMOTE_COMMAND_RESPONSE',
    0x10 => 'ZIGBEE_TRANSMIT_REQUEST',
    0x11 => 'EXPLICIT_ADDRESSING_ZIGBEE_COMMAND_FRAME',
    0x8B => 'ZIGBEE_TRANSMIT_STATUS',
    0x90 => 'ZIGBEE_RECEIVE_PACKET',
    0x91 => 'ZIGBEE_EXPLICIT_RX_INDICATOR',
    0x92 => 'ZIGBEE_IO_DATA_SAMPLE_RX_INDICATOR',
    0x94 => 'XBEE_SENSOR_READ_INDICATOR_',
    0x95 => 'NODE_IDENTIFICATION_INDICATOR',
    0xA1 => 'ROUTE_RECORD_INDICATOR'
};

use constant XBEE_API_BAUD_RATE_TABLE => [
    1200,
    2400,
    4800,
    9600,
    19200,
    38400,
    57600,
    115200,
];

use constant XBEE_API_BROADCAST_ADDR_H          => 0x00;
use constant XBEE_API_BROADCAST_ADDR_L          => 0xFFFF;
use constant XBEE_API_BROADCAST_NA_UNKNOWN_ADDR => 0xFFFE;

{
    my @xbee_flags = map { /::([^:]+)$/; $1 }
     grep( /^API::XBEE_API_/, keys( %constant::declared ) );  # changed local copy jed

    @ISA       = ( 'Exporter' );
    @EXPORT_OK = ( @xbee_flags );

    %EXPORT_TAGS = ( 'xbee_flags' => [@xbee_flags], );
}

=head1 NAME

Device::XBee::API - Object-oriented Perl interface to Digi XBee module API
mode.

=head1 EXAMPLE

A basic example:

 use Device::SerialPort;
 use Device::XBee::API;
 use Data::Dumper;
 $Data::Dumper::Useqq = 1;

 my $serial_port_device = Device::SerialPort->new( '/dev/ttyU0' ) || die $!;
 $serial_port_device->baudrate( 9600 );
 $serial_port_device->databits( 8 );
 $serial_port_device->stopbits( 1 );
 $serial_port_device->parity( 'none' );
 $serial_port_device->read_char_time( 0 );        # don't wait for each character
 $serial_port_device->read_const_time( 1000 );    # 1 second per unfulfilled "read" call

 my $api = Device::XBee::API->new( { fh => $serial_port_device } ) || die $!;
 if ( !$api->tx( { sh => 0, sl => 0 }, 'hello world!' ) ) {
     die "Transmit failed!";
 }
 my $rx = $api->rx();
 die Dumper( $rx );

=head1 SYNOPSIS

Device::XBee::API is a module designed to encapsulate the Digi XBee API in
object-oriented Perl. This module expects to communicate with an XBee module
using the API firmware via a serial (or serial over USB) device.

This module is currently a work in progress and thus the API may change in the
future.

=head1 LICENSE

This module is licensed under the same terms as Perl itself.

=head1 CONSTANTS

A single set of constants, ':xbee_flags', can be imported. These constants
all represent various XBee flags, such as packet types and broadcast addresses.
See the XBee datasheet for details. The following constants are available:

 XBEE_API_TYPE__MODEM_STATUS
 XBEE_API_TYPE__AT_COMMAND
 XBEE_API_TYPE__AT_COMMAND_QUEUE_PARAMETER_VALUE
 XBEE_API_TYPE__AT_COMMAND_RESPONSE
 XBEE_API_TYPE__REMOTE_COMMAND_REQUEST
 XBEE_API_TYPE__REMOTE_COMMAND_RESPONSE
 XBEE_API_TYPE__ZIGBEE_TRANSMIT_REQUEST
 XBEE_API_TYPE__EXPLICIT_ADDRESSING_ZIGBEE_COMMAND_FRAME
 XBEE_API_TYPE__ZIGBEE_TRANSMIT_STATUS
 XBEE_API_TYPE__ZIGBEE_RECEIVE_PACKET
 XBEE_API_TYPE__ZIGBEE_EXPLICIT_RX_INDICATOR
 XBEE_API_TYPE__ZIGBEE_IO_DATA_SAMPLE_RX_INDICATOR
 XBEE_API_TYPE__XBEE_SENSOR_READ_INDICATOR_
 XBEE_API_TYPE__NODE_IDENTIFICATION_INDICATOR

 XBEE_API_BROADCAST_ADDR_H
 XBEE_API_BROADCAST_ADDR_L
 XBEE_API_BROADCAST_NA_UNKNOWN_ADDR

 XBEE_API_TYPE_TO_STRING
 XBEE_API_BAUD_RATE_TABLE

The above should be self explanatory (with the help of the datasheet). The
constant "XBEE_API_TYPE_TO_STRING" is a hashref keyed by the numeric id of the
packet type with the value being the constant name, to aid in debugging. The
constant XBEE_API_BAUD_RATE_TABLE is the baud rate table used by the BD API
command.

=head1 METHODS

=head2 new

Object constructor. Accepts a single parameter, a hashref of options. The
following options are recognized:

=head3 fh

Required. The filehandle to be used to communicate with. This object can be a
standard filehandle (that can be accessed via sysread() and syswrite()), or a
Device::SerialPort object.

=head3 packet_timeout

Optional, defaults to 20. Amount of time (in seconds) to wait for a read to
complete. Smaller values cause the module to wait less time for a packet to be
received by the XBee module. Setting this value too low will cause timeouts to
be reported in situations where the network is "slow".

When using standard filehandles, the timeout is implemented via select(). When
using a Device::SerialPort object, the timeout is done via Device::SerialPort's
read() method, and will expect the object to be configured with a
read_char_time of 0 and a read_const_time of 1000.

=head3 node_forget_time

If a node has not been heard from in this time, it will be "forgotten" and
removed from the list of known nodes. Defaults to one hour. See L<known_nodes>
for details.

=head3 auto_reuse_frame_id

All sent packets need a frame ID to uniquely identify them. There are only 254
available IDs and thus there can only be 254 outstanding commands sent to the
XBee. Normally frame IDs will be freed and reused once a command reply is
received, however there are scenarios where this can not be done (generally
those that involve local or remote AT commands, sleeping/offline nodes, etc).

Normally, when no frame IDs are available but one is needed, the module will
die with an error and the send attempt will be aborted. This condition could be
trapped by the caller (via eval) to retry later, or could be treated as fatal.

With this flag set, instead of dieing, the oldest frame ID will be reused. This
will help work around any issues with frame ID's "leaking", but could cause odd
behavior in cases where all outstanding frame IDs are still in use. This option
should be used with caution.

=head3 api_mode_escape

Optional. If set to a true value, the module will automatically escape outgoing
data and un-escape incoming data for use with XBee API mode 2. Defaults to
false.

See the XBee datasheet for details on API mode 2 and escaped characters.

=cut

sub new {
    my ( $class, $options ) = @_;
    my $self = {};

    die "Missing file handle!" unless $options->{'fh'};
    $self->{fh}                  = $options->{fh};
    $self->{packet_wait_time}    = $options->{packet_timeout} || 20;
    $self->{node_forget_time}    = $options->{node_forget_time} || 60 * 60;
    $self->{auto_reuse_frame_id} = $options->{auto_reuse_frame_id} ? 1 : 0;
    $self->{api_mode_escape}     = $options->{api_mode_escape} ? 1 : 0;

    $self->{in_flight_uart_frames} = {};
    $self->{known_nodes}           = {};
    # $self->{rx_queue}              = [];

    if (   ( ref $self->{fh} ne 'Device::SerialPort' )
        && ( ref $self->{fh} ne 'Win32::SerialPort' ) )
    {
        $self->{fh_sel} = IO::Select->new( $self->{fh} )
         || die "Failed to initialize IO::Select!";
    }

    if ( $self->{api_mode_escape} ) {
        $self->{api_mode_escape_table} = {};
        $self->{api_mode_unescape_table} = {};
        # Note the unescape re starts with the escape character.
        $self->{api_mode_escape_re} = "([";
        $self->{api_mode_unescape_re} = "\x7D([";
        # List of characters taken from XBee datasheet.
        foreach my $e ( 0x7E, 0x7D, 0x11, 0x13 ) {
            my $chr_e = chr( $e );
            my $chr_e_20 = chr( $e ^ 0x20 );
            $self->{api_mode_escape_table}->{ $chr_e } = $chr_e_20;
            $self->{api_mode_unescape_table}->{ $chr_e_20 } = $chr_e;
            $self->{api_mode_escape_re} .= quotemeta( $chr_e );
            $self->{api_mode_unescape_re} .= quotemeta( $chr_e_20 );
        }

        # Note the trailing "])" to terminate the character class.
        $self->{api_mode_escape_re} = qr/$self->{api_mode_escape_re}])/;
        $self->{api_mode_unescape_re} = qr/$self->{api_mode_unescape_re}])/;
    }

    bless $self, $class;
    return $self;
}

#sub read_bytes {
    #my ( $self, $to_read ) = @_;
    #die unless $to_read;
    #my $chars   = 0;
    #my $buffer  = '';
    #my $timeout = $self->{packet_wait_time};

    #if ( !$self->{fh_sel} ) {
        #while ( $timeout > 0 ) {
            #my ( $count, $saw ) = $self->{fh}->read( $to_read );    # will read _up to_ 255 chars
            #if (defined $count){
                #if ( $count > 0 ) {
                    #$chars += $count;
                    #$buffer .= $saw;
                    #if ( $chars >= $to_read ) { return $buffer; }
                #} else {
                    #$timeout--;
                    #print ">";
                #}
            #} else {
                #printf "XBee API error reading read_bytes = %s\n", $!;
            #}
        #}
    #} else {
        #my $read;
        #my $start_ts = time();
        #while ( $to_read > 0 ) {
            #if ( !$self->{fh_sel}->can_read( $timeout ) ) {
                #return undef;
            #}
            #my $c = sysread( $self->{fh}, $read, $to_read );
            #if ( $c ) {
                #$buffer .= $read;
                #$to_read -= $c;
                #$timeout = $self->{packet_wait_time} - ( time() - $start_ts );
                #if ( $timeout < 1 && $to_read > 0 ) { return undef; }
            #} else {
                #return undef;
            #}
        #}
        #return $buffer;
    #}
    #return undef;
#}

sub read_bytes {
    my ( $self, $to_read ) = @_;
    die unless $to_read;
    my $chars   = 0;
    my $buffer  = '';

    while ( 1 ) {
        my ( $count, $saw ) = $self->{fh}->read( $to_read );    # will read _up to_ 255 chars
        if (defined $count){
            if ( $count > 0 ) {
                $chars += $count;
                $buffer .= $saw;
                if ( $chars >= $to_read ) {
                    return $buffer;
                }
                print "short read\n";
            } else {
                last;
            }
        } else {
            printf "XBee API error reading read_bytes = %s\n", $!;
        }
    }
    return undef;
}


sub read_escape_packet {
    my ( $self ) = @_;
    my $l1 = $self->read_bytes( 1 );return unless defined $l1;
    if ($l1 eq "\x7D") {
      $l1 = $self->read_bytes( 1 );return unless defined $l1;
      $l1 ^= "\x20";
    }
    my $l2 = $self->read_bytes( 1 );return unless defined $l2;
    if ($l2 eq "\x7D") {
      $l2 = $self->read_bytes( 1 );return unless defined $l2;
      $l2 ^= "\x20";
    }
    my $packet_data_length = unpack( 'n', $l1.$l2 );
    my $data = $self->read_bytes( $packet_data_length + 1 );return unless defined $data;  # includes checksum

    #dump_data( "before check last", $data);

    if ($data =~ /\x7D$/){ # trailing escape
        my $tail = $self->read_bytes( 1 ); return unless defined $tail;
        $data .= $tail;
    }
    #dump_data( "Before unescape", $data);
    $data =~ s/$self->{api_mode_unescape_re}/$self->{api_mode_unescape_table}->{$1}/g;

    #dump_data( "after unescape ", $data);

    my $need_a_few_more = $packet_data_length - length($data) + 1;
    ## printf "need a few more because of escape w/cs pdl = %s lth = %s\n", $packet_data_length + 1 , length($data);
    while ($need_a_few_more--) {
        my $b = $self->read_bytes( 1 );return unless defined $b;
        if ($b eq "\x7D") {
           $b = $self->read_bytes( 1 ); return unless defined $b;
           $b ^= "\x20";
        }
        $data .= $b;
    }
    return ($packet_data_length, $data);
}

sub dump_data
{
    my ($msg, $data) = @_;
    my @i = unpack "C*", $data;
    my $num;
    $num .= sprintf "%d ", $_ for @i;
    printf "%s[%s]\n", $msg, $num;
}

sub read_packet {
    my ( $self ) = @_;
    my $d;
    my $packet_data_length;
    my $prereads = 0;
    do {
        return 1, "timeout 1" unless $d = $self->read_bytes( 1 );
       $prereads++;
    } while ( $d ne "\x7E" );
    if ($prereads > 1)
    {
        print ".... prereads = $prereads\n";
    }

    if ( $self->{api_mode_escape} ) { # ok need to read and un-escape
        ($packet_data_length, $d) = $self->read_escape_packet();
        return return 1, "ESCAPE PKT timeout" unless $packet_data_length;
    } else { ## just raw read
        return 1, "timeout 2" unless $d = $self->read_bytes( 2 );
        my ( $packet_data_length ) = unpack( 'n', $d );
        # print "packet data length = $packet_data_length\n";
       return 1, "timeout PARTIAL READ" unless $d = $self->read_bytes( $packet_data_length + 1 );
    }
    # good exit
    return 0,$d;
}

#sub free_frame_id {
    #my ( $self, $id ) = @_;
    #delete $self->{in_flight_uart_frames}->{$id};
#}

## id 0 is special, don't allocate it. I don't know if we should die here or
## return 0 on failure...
#sub alloc_frame_id {
    #my ( $self )    = @_;
    #my $start_id    = int( rand( 255 ) ) + 1;
    #my $id          = $start_id;
    #my $oldest_time = 0xFFFFFFFF;
    #my $oldest_id;
    #while ( 1 ) {
        #if ( !exists $self->{in_flight_uart_frames}->{$id} ) {
            #$self->{in_flight_uart_frames}->{$id} = time();
            #return $id;
        #} elsif ( $self->{in_flight_uart_frames}->{$id} < $oldest_time ) {
            #$oldest_time = $self->{in_flight_uart_frames}->{$id};
            #$oldest_id   = $id;
        #}
        #$id++;
        #if ( $id > 255 ) { $id = 1; }
        #if ( $id == $start_id ) {
            #if ( $self->{auto_reuse_frame_id} ) {
                #$self->{in_flight_uart_frames}->{$oldest_id} = time();
                #return $oldest_id;
            #}
            #die "Unable to allocate frame id!";
        #}
    #}
#}

sub parse_packet {
    my ( $self, $d) = @_;
    my @u;
    my $r;
    my $packet_data_length = length($d) - 2;
    if ($packet_data_length < 1)
    {
        return "PACKET DATA TOO SHORT $packet_data_length";
    }
    # printf "packet_data_length = %d\n", $packet_data_length;
    my ( $api_id, $api_data, $packet_checksum ) = unpack( "Ca[$packet_data_length]C", $d ); # ocasional errors
    ## printf "packet data length = %s checksum %d\n", $packet_data_length, $packet_checksum;
    my @hex_data = unpack "C*", $api_data;
    my $validate_checksum = $api_id + $packet_checksum;
    $validate_checksum += $_ for @hex_data;
#    foreach my $c (@hex_data) {
#       $validate_checksum += $c;
#   }
#    for ( my $i = 0; $i < $packet_data_length; $i++ ) {
#        $validate_checksum += unpack( 'C', substr( $api_data, $i, 1 ) );
#    }

    if ( ( $validate_checksum & 0xFF ) != 0xFF ) {
        # warn "Invalid checksum!";
        # dump_data( "invalid checksum $packet_checksum\n", $api_data);
        return "INVALID CHECKSUM";
    }
    if ( $api_id == XBEE_API_TYPE__AT_COMMAND_RESPONSE ) {
        $r = __parse_at_command_response( $api_data );

    } elsif ( $api_id == XBEE_API_TYPE__MODEM_STATUS ) {
        $r = __parse_modem_status( $api_data );

    } elsif ( $api_id == XBEE_API_TYPE__ZIGBEE_RECEIVE_PACKET ) {
        $r = __parse_zigbee_receive_packet( $api_data );

    } elsif ( $api_id == XBEE_API_TYPE__ZIGBEE_EXPLICIT_RX_INDICATOR ) {
        $r = __parse_zigbee_explicit_rx_indicator( $api_data );

    } elsif ( $api_id == XBEE_API_TYPE__ZIGBEE_TRANSMIT_STATUS ) {
        $r = __parse_zigbee_transmit_status( $api_data );

    } elsif ( $api_id == XBEE_API_TYPE__ZIGBEE_IO_DATA_SAMPLE_RX_INDICATOR ) {
        $r = __parse_zigbee_io_data_sample_rx_indicator( $api_data );

    } elsif ( $api_id == XBEE_API_TYPE__NODE_IDENTIFICATION_INDICATOR ) {
        $r = __parse_node_identification_indicator( $api_data );

    } elsif ( $api_id == XBEE_API_TYPE__REMOTE_COMMAND_RESPONSE ) {
        $r = __parse_remote_command_response( $api_data );

    } elsif ( $api_id == XBEE_API_TYPE__ROUTE_RECORD_INDICATOR ) {
        $r = __parse_route_record_indicator( $api_data );

    } elsif ( XBEE_API_TYPE_TO_STRING->{$api_id} ) {
        warn "No code to handle this packet: " . XBEE_API_TYPE_TO_STRING->{$api_id};
    } else {
        warn "Got unknown packet type: $api_id";
    }

    $r->{api_type} = $api_id;
    # $r->{api_data} = $api_data;

    ### $self->_add_known_node( $r );
    return 0,$r;
}

sub send_packet {
    my ( $self, $api_id, $data ) = @_;
    # dump_data( "send packet data", $data);
    my $xbee_data = pack( 'nC', length( $data ) + 1, $api_id );
    my $checksum = $api_id;

    for ( my $i = 0; $i < length( $data ); $i++ ) {
        $checksum += unpack( 'C', substr( $data, $i, 1 ) );
    }
    ## printf "sending checksum = %d\n", $checksum & 0xFF;
    $checksum = pack( 'C', 0xFF - ( $checksum & 0xFF ) );
    $xbee_data = $xbee_data . $data . $checksum;

    if ( $self->{api_mode_escape} ) {
        # Note we insert the \x7D here, it's not part of the table!
        $xbee_data =~ s/$self->{api_mode_escape_re}/\x7D$self->{api_mode_escape_table}->{$1}/g;
    }

    if ( !$self->{fh_sel} ) {
        $self->{fh}->write( "\x7E" . $xbee_data );
    } else {
        syswrite( $self->{fh}, "\x7E" . $xbee_data );
    }
}

=head2 at

Send an AT command to the module. Accepts two parameters, the first is the AT
command name (as two-character string), and the second is the expected data
for that command (if any). See the XBee datasheet for a list of supported AT
commands and expected data for each.

Returns the frame ID sent for this packet. This method does not wait for a
reply from the XBee, as the expected reply is dependent on the AT command sent.
To retrieve the reply (if any), call one of the L<rx> methods.

If no reply is expected, the caller should immediately free the returned frame
ID via L<free_frame_id> to prevent frame ID leaks.

=cut

sub at {
    my ( $self, $command, $data, $frame_id ) = @_;
    unless (defined $data)
    {
       $data = '';
    }
    unless (defined $frame_id)
    {
       $frame_id = 1;
    }
    $self->send_packet( XBEE_API_TYPE__AT_COMMAND, pack( 'C', $frame_id ) . $command . $data);
    return $frame_id;
}


=head2 remote_at

Send an AT command to a remote module. Accepts three parameters: a hashref with
endpoint addresses, command options, frame_id; the AT command name (as
two-character string); and the third as the expected data for that command (if
any). See the XBee datasheet for a list of supported AT commands and expected
data for each.

Endpoint addresses should be specified as a hashref containing the following
keys:

=over 4

=item sh

The high 32-bits of the destination address.

=item sl

The low 32-bits of the destination address.

=item naRMOT

The destination network address.

=item disable_ack

If included ack is disabled
RMOT
=item apply_changes

If included changes applied immediate, if missing an AC command must be sent to
apply changes

=item extended_xmit_timeout

If included the exteded transmission timeout is used

=back

Returns the frame ID sent for this packet. To retrieve the reply (if any), call
one of the L<rx> methods. If no reply is expected, the caller should immediately
free the returned frame ID via L<free_frame_id> to prevent frame ID leaks.

=cut

sub remote_at {
    #my ($package, $filename, $line) = caller;
    my ( $self, $tx, $command, $data) = @_;
    #printf "API::remote_at %s %s %s %s\n", $package, $filename, $line, $tx->{sl};
    # my @my_rx_queue;
    if ( !$command ) { confess "Invalid parameters"; }
    if ( !$tx && !$data ) { confess "Invalid parameters"; }
    if ( !defined $tx && defined $data ) {
        $tx = {};
    } elsif ( ref $tx ne 'HASH' ) {
        $data = $tx;
        $tx   = {};
    }

    if ($tx->{na} && $tx->{sl} == $tx->{na} && $tx->{sh} == 0)
    {
        #ok
    }
    elsif (   ( $tx->{sh} && !$tx->{sl} )
        || ( !$tx->{sh} && $tx->{sl} ) )
    {
        confess "Invalid parameters";
    }

    if ( !defined $tx->{na} ) {
        $tx->{na} = XBEE_API_BROADCAST_NA_UNKNOWN_ADDR;
    }
    if ( !defined $tx->{sh} ) {
        $tx->{sh} = XBEE_API_BROADCAST_ADDR_H;
        $tx->{sl} = XBEE_API_BROADCAST_ADDR_L;
    }
    my ( $ack, $chg, $timeout, $frame_id );
    if ( !defined $tx->{disable_ack} ) {
        $ack = 0x00;
    } else {
        $ack = 0x01;
    }
    if ( defined $tx->{apply_changes} ) {
        $chg = 0x02;
    } else {
        $chg = 0x00;
    }
    if ( defined $tx->{extended_xmit_timeout} ) {
        $timeout = 0x40;
    } else {
        $timeout = 0x00;
    }
    if ( defined $tx->{frame_id} ) {
        $frame_id = $tx->{frame_id};
    } else {
        $frame_id = 0;
    }
    my $options = $ack + $chg + $timeout;

    $data = '' unless defined $data;
    unless ($frame_id)
    {
       $frame_id = 1;
    }
    my $tx_req = pack( 'CNNnC', $frame_id, $tx->{sh}, $tx->{sl}, $tx->{na}, $options );
    $self->send_packet( XBEE_API_TYPE__REMOTE_COMMAND_REQUEST, $tx_req . $command . $data );
    return $frame_id;
}

sub ZBExp {
    my ( $self, $tx, $profile_id, $cluster_id, $payload) = @_;
    # my @my_rx_queue;
    #if ( !$cluster_id ) { confess "ZBExp Invalid parameters no cluster id"; }
    #if ( $profile_id ) { confess "ZBExp Invalid parameters no profile id"; }
    if ( !$tx && !$payload ) { confess "ZBExp Invalid parameters no payload"; }
    if ( !defined $tx && defined $payload ) {
        $tx = {};
    } elsif ( ref $tx ne 'HASH' ) {
        $payload = $tx;
        $tx   = {};
    }

    if (   ( $tx->{sh} && !$tx->{sl} )
        || ( !$tx->{sh} && $tx->{sl} ) )
    {
        confess "ZBExp Invalid parameters";
    }

    if ( !defined $tx->{na} || !$tx->{na}) {
        $tx->{na} = XBEE_API_BROADCAST_NA_UNKNOWN_ADDR;
    }
    if ( !defined $tx->{sh} ) {
        $tx->{sh} = XBEE_API_BROADCAST_ADDR_H;
        $tx->{sl} = XBEE_API_BROADCAST_ADDR_L;
    }
    my $frame_id;

    if ( defined $tx->{frame_id} ) {
        $frame_id = $tx->{frame_id};
    } else {
        $frame_id = 1;
    }
    my $broadcast_radius = 0;
    my $transmit_options = 0;
    my $tx_req = pack( 'CNNnCCnnCC', $frame_id, $tx->{sh}, $tx->{sl}, $tx->{na}, $tx->{source_endpoint}||0, $tx->{destination_endpoint}||0,
           $cluster_id, $profile_id, $broadcast_radius, $transmit_options);
    #printf("API::ZBExp [%s][%s]\n", unpack('H*', $tx_req), unpack('H*', $payload));

    $self->send_packet( XBEE_API_TYPE__EXPLICIT_ADDRESSING_ZIGBEE_COMMAND_FRAME, $tx_req.$payload);
    return $frame_id;
}

=head2 tx

Sends a transmit request to the XBee. Accepts three parameters, the first is the
endpoint address, the second is a scalar containing the data to be sent, and the
third is an optional flag (known as the async flag) specifying whether or not
the method should wait for an acknowledgement from the XBee.

Endpoint addresses should be specified as a hashref containing the following
keys:

=over 4

=item sh

The high 32-bits of the destination address.

=item sl

The low 32-bits of the destination address.

=item na

The destination network address. If this is not specified, it will default to
XBEE_API_BROADCAST_NA_UNKNOWN_ADDR.

=back

If both sh and sl are missing or the parameter is undefined,, they will default
to XBEE_API_BROADCAST_ADDR_H and XBEE_API_BROADCAST_ADDR_L.

The meaning of these addresses can be found in the XBee datasheet. Note: In
the future, a Device::XBee::API::Node object will be an acceptable parameter.

If the async flag is not set, the method will wait for an acknowledgement packet
from the XBee. Return values depend on calling context. In scalar context, true
or false will be returned representing transmission acknowledgement by the
remote XBee device. In array context, the first return value is the delivery
status (as set in the transmit status packet and documented in the datasheet),
and the second is the actual transmit status packet (as a hashref) itself.

If the async flag is set, the method will not wait for an acknowledgement packet
and the tx frame ID will be returned. The caller will need to then receive the
transmit status packet (via one of the L<rx> methods) and free the frame ID (via
L<free_frame_id>) manually.

No retransmissions will be attempted by this module, but the XBee
device itself will likely attempt retransmissions as per its configuration (and
subject to whether or not the packet was a "broadcast").

=cut

# API is goofy here. If called in scalar context, returns true or false if the
# packet was transmitted. If called in array context, returns the delivery
# status and the transmit status packet as an array. Note: the actual delivery
# status uses 0 (or false) to indicate success.
sub tx {
    my ( $self, $tx, $data, $frame_id ) = @_;
    # my @my_rx_queue;
    if ( !$tx && !$data ) { die "Invalid parameters"; }
    if ( !defined $tx && defined $data ) {
        $tx = {};
    } elsif ( ref $tx ne 'HASH' ) {
        $data = $tx;
        $tx   = {};
    }

    if ( ( $tx->{sh} && !$tx->{sl} ) || ( !$tx->{sh} && $tx->{sl} ) ) { die "Invalid parameters"; }

    if ( !defined $tx->{na} ) { $tx->{na} = XBEE_API_BROADCAST_NA_UNKNOWN_ADDR; }
    if ( !defined $tx->{sh} ) {
        $tx->{sh} = XBEE_API_BROADCAST_ADDR_H;
        $tx->{sl} = XBEE_API_BROADCAST_ADDR_L;
    }
    unless ($frame_id)
    {
       $frame_id = 0;
    }
    ### my $frame_id = $noframe_id ? 0 : $self->alloc_frame_id();
    my $tx_req = pack( 'CNNnCC', $frame_id, $tx->{sh}, $tx->{sl}, $tx->{na}, 0, ( $tx->{broadcast} ? 0x8 : 0 ) );
    $self->send_packet( XBEE_API_TYPE__ZIGBEE_TRANSMIT_REQUEST, $tx_req . $data );

    return $frame_id;

    ## Wait until we get the send result message.
    #my $rx = $self->rx_frame_id( $frame_id );
    #return undef unless defined $rx;

    ## Wonky return API.
    #if ( wantarray ) {
        #return ( $rx->{delivery_status}, $rx );
    #} else {
        #if ( $rx->{delivery_status} == 0 ) {
            #return 1;
        #} else {
            #return 0;
        #}
    #}
}

#sub _unshift_rx {
    #my ( $self, $rxq ) = @_;

    #if ( !$rxq ) { return; }
    #if ( ref $rxq eq '' ) {
        #unshift @{ $self->{rx_queue} }, $rxq;
    #} elsif ( ref $rxq eq 'ARRAY' ) {
        #unshift @{ $self->{rx_queue} }, @{$rxq};
    #} else {
        #die "Unknown parameter type";
    #}
#}

#sub _rx_no_queue {
    #my ( $self, $dont_free_id ) = @_;

    #my ( $type, $data ) = $self->read_packet();
    #return unless defined $type;
    #return $self->parse_packet( $type, $data, $dont_free_id );
#}

=head2 rx

Receives a packet from the XBee module. This packet may be a transmission from
a remote XBee node or a control packet from the local XBee module.

If no packet is received before the timeout period expires, undef is returned.

Returned packets will be as a hashref of the packet data, broken out by key for
easy access. Note, as this module is a work in progress, not every XBee packet
type is supported. Callers should check the "api_type" key to determine the
type of the received packet. When possible, packed integers will be unpacked
into the "data_as_int" key. If no packed integer is found this key will not be
present. If unpacking is not possible (due to an unknown packet type, etc), the
value will be undef.

Accepts a single parameter, a flag indicating the received frame ID should NOT
be freed automatically. See L<rx_frame_id> for why you might want to use this
flag (generally, cases when you expect multiple packets to arrive with the same
frame ID).

=cut

#sub rx {
    #my ( $self, $dont_free_id ) = @_;
    #### if ( scalar( @{ $self->{rx_queue} } ) > 0 ) { return shift @{ $self->{rx_queue} }; }
    #return $self->read_packet();
    ## return $self->_rx_no_queue( $dont_free_id );
#}

=head2 rx_frame_id

Like L<rx> but only returns the packet with the requested frame ID number and
then frees that frame ID. If no packet with the specified frame ID is received
within the object's configured packet_timeout time, undef will be returned. Any
other packets received will be enqueued for later processing by another rx
function call.

Accepts two parameters, the first being the desired frame ID and the second a
flag denoting that the frame ID should NOT be automatically freed. In cases
where multiple frames with the same ID are expected to be returned (such as
after an AT ND command), it is preferable to set this flag to a true value and
continue to call rx_frame_id until undef is returned, and then free the ID via
L<free_frame_id>.

=cut

#sub rx_frame_id {
    #my ( $self, $frame_id, $dont_free_id ) = @_;
    #my @ignored;
    #my $r;
    #my $start_time = time();

    #while ( 1 ) {
        #$r = $self->rx( $dont_free_id );
        #if ( $r ) {
            #if ( $r->{frame_id} && $r->{frame_id} == $frame_id ) {
                #last;
            #} else {
                #push @ignored, $r;
            #}
        #}
        #if ( time() - $start_time >= $self->{packet_wait_time} ) {
            #undef $r;
            #last;
        #}
    #}
    #if ( @ignored ) {
        #$self->_unshift_rx( \@ignored );
    #}
    #return $r;
#}

=head2 discover_network

Performs a network node discovery via the ND 'AT' command. Blocks until no
replies have been received in packet_timeout seconds.

=cut

#sub discover_network {
    #my ( $self ) = @_;
    #my $frame_id = $self->at( 'ND' );
    #while ( defined $self->rx_frame_id( $frame_id, 1 ) ) { }
    #$self->free_frame_id( $frame_id );
#}

#=head2 node_info

#=cut

#sub node_info {
    #my ( $self, $node ) = @_;
    #my $sn = __node_sn( $node );
    #if ( !$sn ) { return undef; }
    #$node->{sn} = $sn;
    #return $self->{known_nodes}->{$sn};
#}

#=head2 known_nodes

#Returns a hashref of all known nodes indexed by their full serial number (i.e.
#$node->{sh} . '_' . $node->{sl}).  Nodes that haven't been heard from in the
#configured node_forget_time will be automatically removed from this list if
#they've not been heard from in that time. Nodes are added to that list when a
#message is received from them or a discover_network call has been made.

#Note, the age-out mechanism may be susceptable to stepping of the system clock.

#=cut

#sub known_nodes {
    #my ( $self ) = @_;
    #$self->_prune_known_nodes();
    #return { %{ $self->{known_nodes} } };
#}

### Private methods

#sub _add_known_node {
    #my ( $self, $node ) = @_;

    #my $sn = __node_sn( $node );
    #if ( !$sn ) { return; }

    #$self->_prune_known_nodes();

    ## Update the node in-place in case someone else is holding onto a
    ## reference.
    #if ( $self->{known_nodes}->{$sn} ) {
        #my $sknsn = $self->{known_nodes}->{$sn};
        ## These are the only known values that should change for a node with a
        ## given serial number. The rest are burned into the chip.
        #foreach my $k ( qw/ ni profile_id / ) {
            #if ( $node->{$k}
                #&& ( !$sknsn->{$k} || $sknsn->{$k} ne $node->{$k} ) )
            #{
                #$sknsn->{$k} = $node->{$k};
            #}
        #}
        #$sknsn->{na} = $node->{na} || $node->{my};
        #$sknsn->{last_seen_time} = time();
    #} else {
        #$self->{known_nodes}->{$sn} = {
            #sn              => $sn,
            #sh              => $node->{sh},
            #sl              => $node->{sl},
            #na              => $node->{na} || $node->{my},
            #ni              => $node->{ni},
            #profile_id      => $node->{profile_id},
            #device_type     => $node->{device_type},
            #manufacturer_id => $node->{manufacturer_id},
            #last_seen_time  => time(),
        #};
    #}
# }

#sub _prune_known_nodes {
    #my ( $self ) = @_;
    #my $now = time();
    #my @saved_nodes;
    #while ( my ( $sn, $node ) = each( %{ $self->{known_nodes} } ) ) {
        #if ( $now - $node->{last_seen_time} > $self->{node_forget_time} ) {
            ## Set just in case a caller has held onto the reference for
            ## something.
            #$node->{forgotten} = 1;
            #delete $self->{known_nodes}->{$sn};
        #}
    #}
#}

### Private functions

#sub __node_sn {
    #my ( $node ) = @_;
    #if ( $node->{sn} )  { return $node->{sn} }
    #if ( !$node->{sh} ) { return undef; }
    #return $node->{sh} . '_' . $node->{sl};
#}

sub __get_bits {
    my ( $int ) = @_;
    my $and = 0x80;
    my @list;
    my $any_hits = 0;
    for ( 1 .. 8 ) {
        if ( $int & $and ) {
            # if the bit is set == 1
            push @list, 1;
            $any_hits = 1;
        } else {
            # if the bit is not set == 0
            push @list, 0;
        }

        # shift the constant using right shift
        $and = $and >> 1;
    }
    return ( $any_hits, @list );
}

sub __parse_at_command_response {
    my ( $api_data ) = @_;

    my @u = unpack( 'Ca[2]Ca*', $api_data );

    my $r = {
        frame_id             => $u[0],  # C
        command              => $u[1],  # a[2]
        status               => $u[2],  # C
       #  data                 => $u[3],  # a*
        is_ok                => $u[2] == 0,
        is_error             => $u[2] == 1,
        is_invalid_command   => $u[2] == 2,
        is_invalid_parameter => $u[2] == 3,
    };

    if ( $r->{command} eq 'ND' ) {
        (
            $r->{na},           $r->{sh},                     $r->{sl},
            $r->{ni},           $r->{parent_network_address}, $r->{device_type},
            $r->{source_event}, $r->{profile_id},             $r->{manufacturer_id},
        ) = unpack( 'nNNZ*nCCnna*', $u[3] );
        # The ND API calls it "my" but it's "na" everywhere else. Provide both
        # because the user may expect to see "my" after this packet arrives.
        # This module only uses "na".
        $r->{my} = $r->{na};
    } else {
        $r->{data_as_int} = __data_to_int( $u[3] );
    }

    return $r;
}

sub __data_to_int {
    my ( $data ) = @_;

    if ( length( $data ) == 1 ) {
        return unpack( 'C', $data );
    } elsif ( length( $data ) == 2 ) {
        return unpack( 'n', $data );
    } elsif ( length( $data ) == 4 ) {
        return unpack( 'N', $data );
    } elsif ( length( $data ) == 8 ) {
        my ( $h, $l ) = unpack( 'NN', $data );
        return ( $l | ( $h << 32 ) );
    }
    return undef;
}
sub __parse_modem_status {
    my ( $api_data ) = @_;
    my $u = unpack( 'C', $api_data );
    my $stat = {};
    $stat->{status} = $u;
    if ($u == 0) {$stat->{is_hardware_reset} = 1}
    elsif ($u == 1) {$stat->{is_wdt_reset} = 1}
    elsif ($u == 2) {$stat->{is_associated} = 1}
    elsif ($u == 3) {$stat->{is_disassociated} = 1}
    elsif ($u == 4) {$stat->{is_sync_lost} = 1}    # S1 only
    elsif ($u == 5) {$stat->{is_coord_realig} = 1}   # S1 only
    elsif ($u == 6) {$stat->{is_coord_start} = 1}
    elsif ($u == 7) {$stat->{is_net_seckey_upd} = 1}    # S2 only
    elsif ($u == 0x0D) {$stat->{is_volt_exceed} = 1} # S2/pro only
    elsif ($u == 0x11) {$stat->{is_mdm_conf_chg} = 1} # S2/pro only
    elsif ($u == 0x80) {$stat->{is_slack_error} = 1}  # S2 only
    return $stat;
}

#sub x__parse_modem_status {
    #my ( $api_data ) = @_;
    #my @u = unpack( 'C', $api_data );
    #printf "value of @u 0 = %s 1 = %s\n", $u[0], $u[1];
    #return {
        #status            => $u[1],
        #is_hardware_reset => $u[1] == 1,
        #is_wdt_reset      => $u[1] == 2,
        #is_associated     => $u[1] == 3,
        #is_disassociated  => $u[1] == 4,
        #is_sync_lost      => $u[1] == 5,
        #is_coord_realign  => $u[1] == 6,
        #is_coord_start    => $u[1] == 7,
    #};
#}

sub __parse_zigbee_receive_packet {
    my ( $api_data ) = @_;
    my @u = unpack( 'NNnCa*', $api_data );
    # sh sl and na are named to match the fields in a network discovery AT
    # packet response
    return {
        sh           => $u[0],
        sl           => $u[1],
        na           => $u[2],
        options      => $u[3],
        data         => $u[4],
        is_ack       => $u[3] & 0x01,
        is_broadcast => ( $u[3] & 0x02 ? 1 : 0 ),
    };
}

sub __parse_zigbee_explicit_rx_indicator {
    my ( $api_data ) = @_;
    my @u = unpack( 'NNnCCnnCa*', $api_data );
    #print "raw zigbee_explicit x", unpack("H*", $api_data), "\n";
    my $r = {
        sh                 => $u[0],
        sl                 => $u[1],
        na                 => $u[2],
        se                 => $u[3],
        de                 => $u[4],
        cluster_id         => $u[5],
        profile_id         => $u[6],
        options            => $u[7],
        data               => $u[8],
        is_ack             => $u[7] & 0x01,
        is_broadcast       => ( $u[7] & 0x02 ? 1 : 0 ),
        is_encrypted       => ( $u[7] & 0x20 ? 1 : 0 ),
        is_from_end_device => ( $u[7] & 0x40 ? 1 : 0 ),
    };
    if ($r->{cluster_id} == 0x92) {
        ($r->{number_samples}, $r->{digital_inputs}, $r->{analog_inputs}, $r->{diag}) = __parse_a_and_d_samples($u[8]);
    }
    elsif ($r->{cluster_id} == 0x8005) { # active entpoints responce
        my @d = unpack( 'CCvC*', $u[8] );
        $r->{seq} = $d[0];
        $r->{status} = $d[1];
        $r->{na} = $d[2];
        ## $r->{active_endpoint_count} = $d[3];
        my @list = @d[ 4 .. $#d];
        $r->{active_endpoint}{list} = [@list];
    }
    elsif ($r->{cluster_id} == 0x8004) { # simple descriptor responce
        my ($transaction, $status, $na, $lth, $endpoint, $profile_id, $device_type, $version, $desc) = unpack( 'CCvCCvvCa*', $u[8] );
        my $data;
        $data->{seq} = $transaction;
        $data->{status} = $status;
        $data->{na} = $na;
        $data->{lth} = $lth;
        $data->{endpoint} = $endpoint;
        $data->{profile_id} = $profile_id;
        $data->{device_type} = $device_type;
        $data->{version} = $version;
        $data->{desc} = $desc;

        my ($input_cluster_count, $clusters) = unpack( 'Ca*', $desc );
        $data->{input_cluster_count} = $input_cluster_count;
        my @c = unpack( "v${input_cluster_count}", $clusters);
        $data->{input_clusters} = [@c];
        my($output_cluster_count, @output_clusters) = unpack( 'Cv*', substr($clusters,$input_cluster_count*2));
        $data->{output_cluster_count} = $output_cluster_count;
        $data->{output_clusters} = [@output_clusters];
        $r->{data} = $data;
    }
    elsif ($r->{cluster_id} == 0x0006) {
        my ($frame_control, $tail) = unpack( 'Ca*', $u[8] );
        $r->{header}{disable_default_responce} = ($frame_control & 0b00010000)?1:0;
        $r->{header}{direction} = ($frame_control & 0b00001000)?1:0;
        $r->{header}{mfg_specific} = ($frame_control & 0b00000100)?1:0;
        $r->{header}{cluster_specific} = ($frame_control & 0b00000001)?1:0;
        if ($r->{header}{mfg_specific}) {
            ($r->{header}{mfg_code}, $r->{header}{tran_seq}, $r->{header}{cmd_id}, $r->{payload}) = unpack( 'vCCa*', $tail);
         }
        else {
            ($r->{header}{tran_seq}, $r->{header}{cmd_id}, $r->{payload}) = unpack( 'CCa*', $tail);
        }
    }
    elsif ($r->{cluster_id} == 0x95) {
        #print "0x95 raw zigbee_explicit x", unpack("H*", $u[8]), "\n";
        my @u = unpack( 'nNNZ*nCCnn', $u[8] );
        $r->{remote_na}      = $u[0];
        $r->{remote_sh}      = $u[1];
        $r->{remote_sl}      = $u[2];
        $r->{ni}             = $u[3];
        $r->{parent_address} = $u[4];
        $r->{device_type}    = $u[5];
        $r->{source_event}   = $u[6];
        $r->{profile_id}     = $u[7];
        $r->{mfg_id}         = $u[8];
    }
    return $r;
}

sub __parse_zigbee_transmit_status {
    my ( $api_data ) = @_;
    my @u = unpack( 'CnCCC', $api_data );
    return {
        frame_id         => $u[0],
        remote_na        => $u[1],
        tx_retry_count   => $u[2],
        delivery_status  => $u[3],
        discovery_status => $u[4]
    };
}

sub __parse_zigbee_io_data_sample_rx_indicator {
    my ( $api_data ) = @_;
    # my @u    = unpack( 'NNnCCCCCa*', $api_data );
    my @u    = unpack( 'NNnCa*', $api_data );
    print "0x92 0x", unpack("H*", $api_data), "\n";
    my $r    = {
        sh             => $u[0],
        sl             => $u[1],
        na             => $u[2],
        options        => $u[3],
        is_ack         => $u[3] & 0x01,
        is_broadcast   => ( $u[3] & 0x02 ? 1 : 0 )
    };

    ($r->{number_samples}, $r->{digital_inputs}, $r->{analog_inputs}, $r->{diag}) = __parse_a_and_d_samples($u[4]);
    return $r;
}

sub __parse_a_and_d_samples
{
    my ($raw) = @_;
    my @u    = unpack( 'CCCCa*', $raw );
    my $data = $u[4];

    my $number_samples = $u[0];
    my $r = {data => unpack( "h*", $data )};

    my ($any_d1, $any_d2, $any_a );
    my @bits;
    ( $any_d1, @bits ) = __get_bits( $u[1] );
    $r->{digital_channel_first} = [@bits];
    ( $any_d2, @bits ) = __get_bits( $u[2] );
    $r->{digital_channel_second} = [@bits];
    ( $any_a, @bits ) = __get_bits( $u[3] );
    $r->{analog_channel_bits} = [@bits];

    my @digital;
    # do we need grab the digital 16 bits?
    if ( $any_d1 + $any_d2 ) {
        my ( $d1, $d2 );
        ( $d1, $d2, $data ) = unpack( "CCa*", $data );

        my $trash;
        my @digital_status;
        ( $trash, @digital_status ) = __get_bits( $d1 );
        if ( $r->{digital_channel_first}[3] == 1 ) {
            $digital[12] = $digital_status[3];
        }
        if ( $r->{digital_channel_first}[4] == 1 ) {
            $digital[11] = $digital_status[4];
        }
        if ( $r->{digital_channel_first}[5] == 1 ) {
            $digital[10] = $digital_status[5];
        }
        ( $trash, @digital_status ) = __get_bits( $d2 );
        my $d_number = 7;
        for ( my $i = 0; $i < 8; $i++ ) {
            if ( $r->{digital_channel_second}[$i] == 1 ) {
                $digital[$d_number] = $digital_status[$i];
            }
            $d_number--;
        }
    }

    # now get the analog values, if any
    my @analog;
    for ( my $i = 7; $i >= 0; $i-- ) {
        if ( $r->{analog_channel_bits}[$i] == 1 ) {
            ( $analog[7 - $i], $data ) = unpack( 'na*', $data );
        }
    }
    return ($number_samples, \@digital, \@analog, $r);
}

sub __parse_node_identification_indicator {
    my ( $api_data ) = @_;
    my @u = unpack( 'NNnCnNNZ*nCCnn', $api_data );
    return {
        source_sh      => $u[0],
        source_sl      => $u[1],
        source_na      => $u[2],
        options        => $u[3],
        is_ack         => $u[3] & 0x01,
        is_broadcast   => ( $u[3] & 0x02 ? 1 : 0 ),
        remote_na      => $u[4],
        remote_sh      => $u[5],
        remote_sl      => $u[6],
        ni             => $u[7],
        parent_address => $u[8],
        device_type    => $u[9],
        source_event   => $u[10],
        profile_id     => $u[11],
        mfg_id         => $u[12]
    };
}

sub __parse_route_record_indicator
{
    my ( $api_data ) = @_;
    $api_data =~ s/(.)/sprintf("%x",ord($1))/eg;

     #printf "ROUTE_RECORD_INDICATOR value = %s\n", $api_data;
     return {};
}

sub __parse_remote_command_response {
    my ( $api_data ) = @_;
    my @u = unpack( 'CNNna[2]Ca*', $api_data );
     my $r    =  {
        frame_id                  => $u[0],
        sh                        => $u[1],
        sl                        => $u[2],
        na                        => $u[3],
        command                   => $u[4],
        status                    => $u[5],
        data                      => $u[6],
        data_as_int               => __data_to_int( $u[6] ),
        is_ok                     => $u[5] == 0,
        is_error                  => $u[5] == 1,
        is_invalid_command        => $u[5] == 2,
        is_invalid_parameter      => $u[5] == 3,
        is_remote_cmd_xmit_failed => $u[5] == 4,
    };
    if ($r->{command} eq 'IS')
    {
       ($r->{number_samples}, $r->{digital_inputs}, $r->{analog_inputs}, $r->{diag}) = __parse_a_and_d_samples($u[6]) if ($u[5] == 0);
    }
    return $r;
}

=head1 EXAMPLES

Miscellaneous code examples follow.

=head2 Fetch modem baud rage

 use Device::SerialPort;
 use Device::XBee::API;

 # From XBee datasheet pg 73.
 my @baud_rate_table = (
     1200,
     2400,
     4800,
     9600,
     19200,
     38400,
     57600,
     115200
 );

 # Configure the serial port
 my $serial_port_device = Device::SerialPort->new( '/dev/ttyU0' )
     || die $!;
 $serial_port_device->baudrate( 9600 );
 $serial_port_device->databits( 8 );
 $serial_port_device->stopbits( 1 );
 $serial_port_device->parity( 'none' );
 $serial_port_device->read_char_time( 0 );
 $serial_port_device->read_const_time( 1000 );

 # Create the API object
 my $api = Device::XBee::API->new( { fh => $serial_port_device } )
     || die $!;

 # Send the BD API command
 my $at_frame_id = $api->at( 'BD' );
 die "Transmit failed" unless $at_frame_id;

 # Receive the reply
 my $rx = $api->rx_frame_id( $at_frame_id );
 die "No reply received" if !$rx;
 if ( $rx->{status} != 0 ) {
     die "API error" if $rx->{is_error};
     die "Invalid command" if $rx->{is_invalid_command};
     die "Invalid parameter" if $rx->{is_invalid_parameter};
     die "Unknown error";
 }

 my $baud_rate = $baud_rate_table[ $rx->{data_as_int} ];
 if ( !$baud_rate ) {
     $baud_rate = $rx->{data_as_int};
 }

 print "Modem baud rate is $baud_rate bps.\n";


=head1 CHANGES

=head2 0.6, 20120624 - jeagle

Update documentation.

Add support for API mode 2 escapes. Needs testing.

Add constant for the "BD" baud rate table.

=head2 0.5, 20120401 - jeagle

Add support for Win32::SerialPort to enable Windows support. (Thanks Jerry)

Fix issue with tx() in async mode. (Thanks Vicente)

Add support for "explicit rx indicator" packets. (Thanks Vicente)

=head2 0.4, 20110831 - jeagle

Fix packet timeout bug reported by Dave S.

Replace call to die() in __data_to_int with return undef, update docs to
reflect this.

=head2 0.3, 20110621 - jeagle, jdodgen

Change from internal Device::SerialPort wrapper to accepting an fh.

Add asynchronous support to tx and add some helpful methods to support it.

Handle more command types (remote AT, ZigBee IO, node identification).

Add an option to re-use frame IDs under high tx load.

Many more changes!

=head2 0.2, 20101206 - jeagle

Initial release to CPAN.

=cut

1;
