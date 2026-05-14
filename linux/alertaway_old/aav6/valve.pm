package valve;
use strict;

use constant RELAY_ON  => 1;
use constant RELAY_OFF  => 0;
use constant VALVE_AT_LIMIT  => 0;
use constant VALVE_NOT_AT_LIMIT  => 1;
use constant MAX_TRYS  => 6;

use tools qw (:debug);
use constant DEBUG => 1;  #tools::DEBUG_valve;

sub check
{
    my ($XbeeSendQueue, $needed_state, $ah, $al, $na, $open_limit_switch, $close_limit_switch, $open_relay, $close_relay) = @_;
    use constant PORT => 'D1';
    use constant TOGGLE_PORT => 'D2';
    #printf "valve:check: [%0x:%0x] needed state[%s] open_limit[%s] close_limit[%s] open_relay[%s] close_relay[%s]\n",
         #$ah,  $al, $needed_state,  $open_limit_switch, $close_limit_switch, $open_relay, $close_relay if DEBUG;
    #printf "valve:check:  OPEN_RLY %s, OPEN_SIG %s\n",
          #$open_relay, $open_limit_switch == VALVE_NOT_AT_LIMIT?"VALVE_NOT_AT_LIMIT":"VALVE_AT_LIMIT" if DEBUG;
    #printf "valve:check:  CLOSE_RLY %s, CLOSE_SIG %s\n",
         #$close_relay, $close_limit_switch== VALVE_NOT_AT_LIMIT?"VALVE_NOT_AT_LIMIT":"VALVE_AT_LIMIT" if DEBUG;

    # a quick check to see if it is correct

    if (($needed_state == 1 && $open_limit_switch == VALVE_AT_LIMIT)
       ||
       ($needed_state == 0 && $close_limit_switch == VALVE_AT_LIMIT))
    {
       # valve is in correct position
       # check to see if any active relays, and turn them off
       #printf"valve:check: Valve is in correct position\n" if DEBUG;
       if ($open_relay == RELAY_ON  || $close_relay == RELAY_ON)
       {
         printf"valve:check: a relay is on, so turning both off\n" if DEBUG;
            $XbeeSendQueue->enqueue({request => 'MOTORIZED VALVE RELAY OFF',
                                 ah => $ah, al => $al, na => $na, port =>  PORT, toggle_port => TOGGLE_PORT}, from => 'correct position and realy on');
        }
    }
    else
    {
        printf"valve:check: Valve not correct needs to be [%s]\n", $needed_state if DEBUG;
        if ($needed_state == 1 && $open_limit_switch == VALVE_NOT_AT_LIMIT) # should be open
        {
            printf"valve:check: valve is CLOSED and needs to be opened[%s,%s]\n", PORT, TOGGLE_PORT if DEBUG;
            $XbeeSendQueue->enqueue({request => 'OPEN MOTORIZED VALVE',
                        al => $al, ah => $ah, na => $na,
                       port =>  PORT, toggle_port => TOGGLE_PORT});
        }
        elsif ($needed_state == 0 && $close_limit_switch == VALVE_NOT_AT_LIMIT) # should be closed
        {
            printf"valve:check: valve is OPEN and needs to be closed [%s,%s]\n", PORT, TOGGLE_PORT if DEBUG;
            $XbeeSendQueue->enqueue({request => 'CLOSE MOTORIZED VALVE',
                    al => $al, ah => $ah, na => $na,
                    port =>  PORT, toggle_port => TOGGLE_PORT});
        }
        elsif ($open_relay == RELAY_OFF && $close_relay == RELAY_OFF)  # both relays OFF, that is normal
        {
            if ($open_limit_switch == VALVE_NOT_AT_LIMIT && $close_limit_switch == VALVE_NOT_AT_LIMIT)  # looks like the valve is part open
            {
                printf"valve:check: part open found %s\n", PORT if DEBUG;
                #watch out for the race condition, cold be in the middle of a transition
                #if ($time_requested + 15 < $rx->{timestamp}) # timed out, looks like it never got moved
                #{
                    # try again
                    if ($needed_state == 1)
                    {
                        $XbeeSendQueue->enqueue({request => 'OPEN MOTORIZED VALVE',
                                 al => $al, ah => $ah, na => $na,
                                 port =>  PORT, toggle_port => TOGGLE_PORT});
                    }
                    else
                    {
                        $XbeeSendQueue->enqueue({request => 'CLOSE MOTORIZED VALVE',
                                 al => $al, ah => $ah, na => $na,
                                 port =>  PORT, toggle_port => TOGGLE_PORT});
                    }
                #}
            }
        }
        elsif (($open_relay == RELAY_ON && $open_limit_switch == VALVE_AT_LIMIT)  # it is fully open or closed now, so turn off relay(s)
               ||
               ($close_relay == RELAY_ON && $close_limit_switch == VALVE_AT_LIMIT))
        {
            printf"valve:check: need to turn relays off\n" if DEBUG;

            $XbeeSendQueue->enqueue({request => 'MOTORIZED VALVE RELAY OFF',
                                     ah => $ah, al => $al, port =>  na => $na, PORT, toggle_port => TOGGLE_PORT, from => 'last check'});
        }
    }
}
1
