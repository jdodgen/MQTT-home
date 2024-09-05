package extern;
use strict;

use filterPrint;
use constant DBG => 1;
my $fp = filterPrint->new();

sub do_extern_device
{
    my ($dt, $location, $device, $action, $wemo, $EvaluateQueue, $XbeeSendQueue) = @_;
    my $wemo_AND = $wemo ? " AND devices.allow_wemo = 'checked'" : "";
    DBG&&$fp->prt("processing external override for device[%s][%s] action[%s]", $location, $device, $action);
    my ($status, $rowid, $ah,$al, $na, $endpoint, $profile_id, $port, $logic, $toggle_port,
        $default_state, $override_state, $external_override, $invert_wemo, $raw_value) = $dt->get_rec(<<EOF, $device, $location);
    SELECT devices.rowid, devices.ah, devices.al, wireless_devices.na,
        wireless_devices.endpoint, wireless_devices.profile_id, devices.port,
        port_types.logic, port_types.toggle_port,
        devices.default_state, devices.override_state, devices.external_override,
        coalesce(devices.invert_wemo,'', raw_value)
    FROM devices
    JOIN wireless_devices
        ON wireless_devices.ah = devices.ah
        AND wireless_devices.al = devices.al
    JOIN device_types
        ON device_types.part_nbr = wireless_devices.part_nbr
    JOIN port_types
        ON port_types.part_nbr =  device_types.part_nbr
        AND port_types.port = devices.port
    WHERE coalesce(devices.port_name,'') = %s
        AND coalesce(wireless_devices.physical_location,'') = %s $wemo_AND
EOF
    if ($status)
    {
        my $new;
        $action = lc($action);
        if ($action eq 'true')
        {
            $new = $invert_wemo eq 'checked'? 0:1;
        }
        elsif ($action eq 'false')
        {
            $new = $invert_wemo eq 'checked'? 1:0;
        }

        my ($new_override, $new_external_override) = external_override_logic($override_state, $external_override, $new);
        #DBG&&$fp->prt("raw_value[%s]", $raw_value);
        my $status = $dt->do("UPDATE devices SET override_state = %s, external_override = %s,  raw_value = null WHERE rowid = %s", $new_override, $new_external_override, $rowid);
        # experiment if ($default_state == -1) # this is special because it will not automaticly change state because of a On or Off inside evaluate.pm
        {
            my $request = ($action eq 'true') ? 'DEVICE_ON' : 'DEVICE_OFF';
            DBG&&$fp->prt("action[%s] raw_value[%s]", $action, $request);
            $XbeeSendQueue->enqueue({request => $request, ah => $ah, al =>  $al, na => $na, endpoint => $endpoint,
                port => $port, toggle_port => $toggle_port, logic =>  $logic, profile_id => $profile_id,  from => 'do_extern_device'});
            # pub heater test
            $XbeeSendQueue->enqueue({request => $request, ah => $ah, al =>  $al, na => $na, endpoint => $endpoint,
                port => $port, toggle_port => $toggle_port, logic =>  $logic, profile_id => $profile_id,  from => 'do_extern_device'});
        }
        #else
        #{
            #$EvaluateQueue->enqueue();
        #}
     }
    else
    {
        DBG&&$fp->prt("ERROR query get_rec returned nothing");
    }
}

sub external_override_logic
{
    my ($override_state, $external_override, $new_state) = @_;
    DBG&&$fp->prt("old override_state[%s], external_override[%s], new_state[%s]", $override_state, $external_override, $new_state);
    my $new_external_override;
    my $new_override_state;
    if (!$external_override) # no current external override)
    {
        $new_external_override = 1;
        $new_override_state = $new_state;
    }
    else # we have an exisitng external override
    {
        if ($override_state != $new_state) #state change so clear unset override
        {
            $new_external_override = undef;
            $new_override_state = undef;
        }
        else # nothing changed
        {
            $new_external_override = $external_override;
            $new_override_state = $override_state;

        }
    }
    DBG&&$fp->prt("new override_state[%s] external_override[%s]", $new_override_state, $new_external_override);
    return ($new_override_state, $new_external_override);
}

