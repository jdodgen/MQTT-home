package db;
# Copyright 2011 - 2024 by James E Dodgen Jr.  MIT Licence.
# work in progress: moving alertaway internal IOT handling to home-broker
#
use DBI;
use DBTOOLS;
use strict;
use Carp;
use IO::Compress::Gzip;
use Data::Dumper;
use filterPrint;

my $fp = filterPrint->new();
#use constant DBG => 1;

sub open
{
    my ($dbname,$options) = @_;

    my %sqlite_attr = (
    PrintError => 1,
    RaiseError => 0,
    ShowErrorStatement => 1 #,
    #AutoCommit => exits $options->{commit}?0:1
    );
    #print "sqlite open ".$sqlite_attr{AutoCommit};
    my $dbh = DBI->connect( "dbi:SQLite:$dbname", "", "", \%sqlite_attr );
    if ( !defined($dbh) )
    {
        confess("could not connect to $dbname");
    }
    #$dbh->trace(2);
    $options->{debug} = 0 if (! defined $options->{debug});
    #$dbh->{HandleError} = sub { confess(shift) };
    my $dt = new DBTOOLS( dbh => $dbh, debug => $options->{debug} );
    return $dt;
}

sub backup
{
    my ($dt, $todb) = @_;
    $dt->do("vacuum");
    $dt->{dbh}->sqlite_backup_to_file($todb);
}

sub create_or_copy
{
    my ($db_name, $save_database_as) =  @_;

    my $dt = db::open($db_name);

    if (-f $save_database_as)
    {
        $dt->{dbh}->sqlite_backup_from_file($save_database_as);
        apply_patch($dt);
        load_static_data($dt);
        $fp->prt("database copied to ram");
        my ($stat, $db_user_version) = $dt->get_rec('PRAGMA user_version');
        sleep 3;
        return;
    }
    $fp->prt("New database created");
    create_tables($dt);
    load_static_data($dt);
    $dt->{dbh}->sqlite_backup_to_file($save_database_as);
    sleep 5;
}

my $tables = <<EOF;
drop table if exists mqtt_devices;
CREATE TABLE mqtt_devices (
friendly_name PRIMARY KEY,
description,
source,
last_mqtt_time

);

/* OLD */
drop table if exists wireless_devices;
CREATE TABLE wireless_devices (
ah CHAR(8) NOT NULL ,
al CHAR(8) NOT NULL ,
na,
physical_location CHAR(100),
part_nbr CHAR(10),
last_time_in INTEGER DEFAULT NULL,
previous_time_in INTEGER DEFAULT NULL,
db_level INTEGER,
time_reported_gone INTEGER DEFAULT NULL,
parent_network_address INTEGER,
my_network_address INTEGER,
firmware_version,
endpoint,
profile_id,
trace,
PRIMARY KEY (al, ah)
);


drop table if exists subscribed_features;
CREATE TABLE subscribed_features (
/* message_processor maintains the existance */
friendly_name,
feature,
/* subscribed feature activity arrives to a queue */
description,
type,
last_mqtt_time
adjustment,
location,
alarm_value_low,
alarm_value_high,
current_value,
previous_value,
last_report_time,
last_range_state,
transition_time,
notified,
port_name,
PRIMARY KEY (friendly_name, feature)
);

/* OLD */
drop table if exists sensor;
CREATE TABLE sensor (
id INTEGER PRIMARY KEY,
ah,
al,
port,
adjustment,
location,
alarm_value_low,
alarm_value_high,
current_value,
previous_value,
last_report_time,
last_range_state,
transition_time,
notified,
port_name,
validated /* NO, or IODS what validates the current value */
);
CREATE UNIQUE INDEX out_sensorx1 ON sensor (ah, al, port);

drop table if exists publish_feature;
CREATE TABLE publish_feature (
friendly_name,
feature,
last_mqtt_time
type,
description,
true_value,
false_value,
topic,
default_state,
override_state,
external_override,  /* this is a toggle to tell if the override came from wemo or other outside event */
override_expire_time INTEGER,
last_report_time,
try_count,
current,
port_name,  /* was unique */
PRIMARY KEY (friendly_name, feature)
);


drop table if exists devices;
CREATE TABLE devices ( /* these are from 0x92 packets reporting current value of sent items, also set by positive ack */
ah CHAR(8),
al CHAR(8),
port CHAR(8),
default_state,
override_state,
external_override,  /* this is a toggle to tell if the override came from wemo or other outside event */
override_expire_time INTEGER,
raw_value,
validated, /* NO, ACK, IODS what validates the current value */
last_report_time,
frame_id,
try_count,
current,
allow_wemo,
invert_wemo,
port_name,  /* was unique */
ip_wemo_nbr integer,
fauxmo_state,
PRIMARY KEY (ah, al, port)
);



drop table if exists alerts; /* contacts to send messages to when sensors change */
CREATE TABLE alerts (
friendly_name,
feature,
last_range_state,
contact CHAR(50) NOT NULL  DEFAULT 'NULL',
threshold_from, /* only valid for logic types like temps analog  things */
threshold_to,
last_date,
PRIMARY KEY (friendly_name, feature, contact)
);


drop table if exists actions;
CREATE TABLE actions (
action_id INTEGER PRIMARY KEY,
friendly_name,
feature,
toggle_port,
part_nbr,
logic,
device_friendly_name,
device_feature,
device_toggle_feature,
device_part_nbr,
device_logic,
disabled INTEGER,
priority INTEGER,
duration INTEGER,
sensor_on_or_off,  /* defines when action needed ON or OFF */
action_on_or_off,  /* does this turn it ON or OFF --- Example:  when sensor is OFF turn the action ON */
on_time,
off_time, /* on and off are both epoch times to turn this off  9999999 is forever as in FOLLOWING */
current_state, /* ON OFF or UNK */
requested_state
);

CREATE INDEX actionsx1 ON actions (device_friendly_name, device_feature);
CREATE INDEX actionsx2 ON actions (friendly_name, feature);


drop table if exists alert_pictures;
CREATE TABLE alert_pictures (
friendly_name,
feature,
camera_name CHAR DEFAULT NULL,
repeat_count INTEGER DEFAULT NULL,
repeat_delay INTEGER DEFAULT NULL,
PRIMARY KEY (friendly_name, feature, camera_name)
);


drop table if exists emails;
CREATE TABLE emails (
contact CHAR(50) DEFAULT NULL REFERENCES alerts (contact),
email_address CHAR(10) DEFAULT NULL,
requires_short_messages CHAR DEFAULT NULL,
PRIMARY KEY (contact, email_address)
);

drop table if exists config;
CREATE TABLE config (
problem_reporting_frequency INTEGER NOT NULL ,
primary_contact CHAR(50) NOT NULL  REFERENCES emails (contact),
connection_type CHAR DEFAULT NULL,
external_http_port INTEGER DEFAULT NULL,
static_ip CHAR DEFAULT NULL,
subnet_mask CHAR DEFAULT NULL,
gateway CHAR DEFAULT NULL,
dns1 CHAR DEFAULT NULL,
dns2 CHAR DEFAULT NULL,
metric_units CHAR NOT NULL  DEFAULT 'NULL',
lw_connection_type CHAR DEFAULT NULL,
lw_external_http_port INTEGER DEFAULT NULL,
lw_static_ip CHAR DEFAULT NULL,
lw_subnet_mask CHAR DEFAULT NULL,
lw_gateway CHAR DEFAULT NULL,
lw_dns1 CHAR DEFAULT NULL,
lw_dns2 CHAR DEFAULT NULL,
watchdog_sleep_time INTEGER DEFAULT 30,
lost_device_wait INTEGER DEFAULT 120,
internal_http_port INTEGER DEFAULT 80,
version_number INTEGER DEFAULT NULL,
upgrade_problem CHAR DEFAULT NULL,
problem_server_version_number INTEGER DEFAULT 0,
server_version INTEGER DEFAULT NULL,
pan_id INTEGER DEFAULT NULL,
pan_id_64 INTEGER,
pan_id_16 INTEGER,
operating_channel INTEGER,
stack_profile INTEGER,
process_start_time INTEGER DEFAULT NULL,
ident CHAR DEFAULT NULL,
sh INTEGER,
sl INTEGER,
default_email char default null,
timezone CHAR,
timezone_offset,
latitude,
longitude,
password,
network_address INTEGER,
ip_set_status,
time_offset,
dvr_ip,
dvr_port,
dvr_user,
dvr_password,
ethernet_port
);

drop table if exists messages;
CREATE TABLE messages (
short CHAR NOT NULL  DEFAULT 'NULL' PRIMARY KEY,
long CHAR DEFAULT NULL
);

drop table if exists errors;
CREATE TABLE errors (
id INTEGER DEFAULT NULL PRIMARY KEY AUTOINCREMENT,
time CHAR DEFAULT NULL,
message CHAR DEFAULT NULL
);

drop table if exists wan_activity;
CREATE TABLE wan_activity (
ip_addr CHAR NOT NULL  PRIMARY KEY,
hits INTEGER DEFAULT NULL,
date INTEGER DEFAULT NULL
);

drop table if exists timed_events;
CREATE TABLE timed_events
(
friendly_name,
feature,
days, /* a comma seperated string of days 0 thru 6 */
start_type,  /* dawn, dusk, or fixed */
start_hour,  /* used for fixed times */
start_minute, /* used for fixed times */
start_offset, /* use for dawn dusk */
stop_type,  /* dawn, dusk, or fixed */
stop_hour,  /* used for fixed times */
stop_minute, /* used for fixed times */
stop_offset, /* use for dawn dusk */
/* duration, not sure if still needed */
time_to_stop,  /* calculated every day at midnight + 1 second */
time_to_start, /* calculated every day at midnight + 1 second */
seconds_from_midnight INTEGER, /* calculated every day at midnight+ a second  not sure if needed */
state INTEGER
);

drop table if exists queue_size;
CREATE TABLE queue_size
(
    queue TEXT PRIMARY KEY,
    mq_msgsize INTEGER,
    largest_msg INTEGER,
    mq_maxmsg INTEGER,
    nbr_in_queue INTEGER

);

drop table if exists frame_id_ack;
CREATE TABLE frame_id_ack
(
    id INTEGER PRIMARY KEY
);

drop table if exists reason_started;
CREATE TABLE reason_started (code, descr, next_code, next_descr);
EOF


sub create_tables
{
    my ($dt) = @_;

    DBG&&$fp->prt("creating tables ...");
    my $errors = $dt->do_a_block($tables);
    $errors += $dt->do_a_block(<<EOF);

insert into config (problem_reporting_frequency,primary_contact,connection_type,lw_connection_type, external_http_port,metric_units,
watchdog_sleep_time,lost_device_wait,internal_http_port,dvr_ip, dvr_port)
values (120,"none","DHCP","DHCP",9000,"no",60,180,80,"local",80);
EOF
    if ( $errors > 0 )
    {
        DBG&&$fp->prt("found %d errors during db create ", $errors);
    }
}

sub apply_patch
{
    my ($dt) = @_;
    #                  return;
    #add_new_column($dt,'config', 'pass_phrase');
    if (see_if_patch_needed($dt, 'devices', 'trash1'))
    {
        my $errors = $dt->do_a_block(<<EOF);
        ALTER TABLE devices RENAME COLUMN port_name TO trash1;
        ALTER TABLE devices ADD COLUMN port_name;
EOF
    }
    if (see_if_patch_needed($dt, 'config', 'wemo_port_base'))
    {
        my $errors = $dt->do_a_block(<<EOF);
        ALTER TABLE config ADD COLUMN wemo_port_base;
        update config set wemo_port_base = 52004;
EOF
    }
    return;
}

sub add_new_column
{
    my ($dt, $table, $column) = @_;
    if (see_if_patch_needed($dt, $table, $column))
    {
        $fp->prt("applying patch tbl[%s] col[%s]",$table, $column);
        my $errors = $dt->do_a_block(<<EOF);
ALTER TABLE $table ADD COLUMN $column;
EOF
    }
}

sub see_if_patch_needed
{
    my ($dt, $table, $col) = @_;
    my ($status, $junk) = $dt->get_rec("select type from sqlite_master where type = 'table' and tbl_name  = %s and sql like %s",
               $table, '%'.$col.'%');
    $fp->prt("table %s field = %s needed? %s", $table, $col, $status?'NO':'yes');
    return !$status;
}

sub load_static_data
{
 my ($dt) = @_;
## load static data
    my $errors = $dt->do_a_block(<<EOF);


delete from messages;

drop table if exists processes;
CREATE TABLE processes
(
    pid INTEGER,
    name PRIMARY KEY
);

DROP TABLE if exists device_types;
CREATE TABLE device_types (
part_nbr TEXT NOT NULL  PRIMARY KEY,
Desc TEXT NOT NULL ,
part_type TEXT,
allowed_away_time INTEGER NOT NULL
);

insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("EW1","Water sensor","S",900);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RW1","Water sensor","S",180);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RTM1","Temp/Button","S",180);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RT1","Thermometer","S",180);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("ETM1","Temp/Button","S",1500);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("ET1","Thermometer","S",1500);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("EM1","Button","S",300);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("EM2","Button","S",900);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RTS1","Temp/Switch","S",180);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("ETS1","Temp/Switch","S",900);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("ES1","Switch","S",900);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RS1","Switch with LED","S",900);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RPANEL1","Switch panel","S",80);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("EACM1","16VAC bell","S",900);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RALARM1","Alarm","S",60);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RALARM2","Alarm","S",60);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RMOT","Motion Detector","S",80);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RSD1","Single Switched Device","S",80);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RSD2","Switched Device","S",80);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RSD3","Quad Switched Device","S",80);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RSD4","Dual Switched Device","S",80);

insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RBV1","Ball Valve Controller old","B",80);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RBV2","Ball Valve Controller","B",80);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("RSD2M2","Dual switched, Dual Button","S",80);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("ZHAx100","Wall Switch","HA",30000000);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("GLLx1","GLLx1 On/Off Lightx104x100","HA",30000000);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("GLLx0","GLLx0 On/Off Light","HA",30000000);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("GLLx10","GLLx10 On/Off Lightx104x100","HA",30000000);

insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("ZHAx9","ZHAx9 Power Outlet","HA",30000000);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("ZHA0x101","ZHA0x101 Dimmable Light","HA",30000000);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("ZHA0x402","ZHA0x402 Water Sensor","HA",30000000);
insert into device_types (part_nbr, desc, part_type, allowed_away_time) values ("GLLx100","GLLx100 Dimmable Light","HA",30000000);

drop table if exists port_types;
CREATE TABLE port_types (
part_nbr CHAR(10) NOT NULL  REFERENCES device_types (part_nbr),
port CHAR(8) NOT NULL ,
type CHAR NOT NULL ,
no_default_state,
desc CHAR(30) NOT NULL  DEFAULT 'NULL',
alarm_value_low INTEGER DEFAULT NULL,
alarm_value_high INTEGER DEFAULT NULL,
logic CHAR(2) NOT NULL  DEFAULT 'LT',
toggle_port CHAR DEFAULT NULL,
IO_direction INTEGER DEFAULT NULL,
force_notification INTEGER,
volatle_raw_value, /* the raw value does not follow the state of ON or OFF so use devices.current and other checks like the valve logic */
PRIMARY KEY (port, part_nbr)
);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EW1","A7", "2 AA Batteries",      2.2,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EW1","A1", "Water sensor",  0,1015, "H2O",1,  "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RW1","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RW1","A1", "Water sensor",  0,1015, "H2O",1,   "H","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RW1","D3", "LED",         3.1,3.4, "BINARY",0,   "NA","A",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RTM1","A7", "AC adapter",         3.1,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RTM1","A3","Thermometer",-99,9999,  "TMP36",1,   "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RTM1","D0","Button",       0,9999,  "MOMENTARY1",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RT1","A7", "AC adapter",         3.1,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RT1","A3","Thermometer",-99,9999,  "TMP36",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ETM1","A7", "2 AA Batteries",         2.2,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ETM1","A3","Thermometer",-99,9999,  "TMP36",1,   "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ETM1","D0","Button",       0,9999,  "MOMENTARY0",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ET1","A7", "2 AA Batteries",         2.2,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ET1","A3","Thermometer",-99,9999,  "TMP36",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EM1","A7", "2 AA Batteries",         2.2,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EM1","D0","Button",       0,9999,  "MOMENTARY0",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RS1","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RS1","D4", "LED",         0,9999, "BINARY",0,   "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RS1","D0","Switch",       0,9999,  "SW0",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EM2","A7", "2 AA Batteries",         2.2,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EM2","D4","Button",       0,9999,  "MOMENTARY0",1, "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RTS1","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RTS1","A3","Thermometer",-99,9999,  "TMP36",1,   "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RTS1","D0","Switch",       0,9999,  "SW1",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ETS1","A3","Thermometer",-99,9999,  "TMP36",1,   "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ETS1","A7", "2 AA Batteries",         2.2,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ETS1","D0","Switch",       0,9999,  "SW0",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ES1","A7", "2 AA Batteries",         2.2,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ES1","D0","Switch",       0,9999,  "SW0",1,   "NA","S",1);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EACM1","A7", "2 AA Batteries",         2.2,3.4, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EACM1","D0","Front",       0,9999,  "MOMENTARY0",1,   "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("EACM1","D1","Rear",       0,9999,  "MOMENTARY0",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM1","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM1","D0","Buzzer",       0,9999, "HIGH",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM1","D5","Loud, Obnoxious",       2,9999, "HIGH",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM1","D4", "LED",         0,9999, "HIGH",0,   "NA","A",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RPANEL1","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RPANEL1","D0","Buzzer",       0,9999, "HIGH",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RPANEL1","D5","Switch",       0,9999,  "SW0",1,   "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RPANEL1","D4", "LED",         0,9999, "BINARY",0,   "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RPANEL1","A3","Thermometer",-99,9999,  "TMP36",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD1","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD1","D0","Relay",   0,9999, "BINARY",0,        "NA","A",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD2","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD2","D4","Relay",   0,9999, "BINARY",0,        "NA","A",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD3","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD3","D0","Relay 1",   0,9999, "BINARY",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD3","D1","Relay 2 ",   0,9999, "BINARY",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD3","D2","Relay 3",   0,9999, "BINARY",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD3","D3","Relay 4",   0,9999, "BINARY",0,        "NA","A",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD4","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD4","D0","Relay",   0,9999, "BINARY",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD4","D1","Relay",   0,9999, "BINARY",0,        "NA","A",0);


insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RBV1","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification, volatle_raw_value) values ("RBV1","D0","Valve",   1,0, "VALVE",0,        "D1","A",0,1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RBV1","D2","Valve Open",   0,9999, "OPEN",1,        "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RBV1","D3","Valve Closed",   0,9999, "CLOSED",1,        "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RBV2","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification, volatle_raw_value) values ("RBV2","D1","Valve",   1,0, "VALVE",0,        "D2","A",0,1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RBV2","D4","Valve Open",   0,9999, "OPEN",1,        "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RBV2","D7","Valve Closed",   0,9999, "CLOSED",1,        "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RBV2","A3", "Water sensor",  0,1015, "H2O",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD2M2","D1","Relay 1",   0,9999, "BINARY",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD2M2","D2","Relay 2",   0,9999, "BINARY",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD2M2","D4","Button 1", 0,9999, "MOMENTARY0",1, "NA","S",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RSD2M2","D7","Button 2", 0,9999, "MOMENTARY0",1, "NA","S",0);


insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM2","A7", "AC adapter",         3.1,3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM2","D0","Play all",       1,9999, "LOW",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM2","D1","Ding Dong",       1,9999, "LOW",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM2","D2","Ding Ding",       1,9999, "LOW",0,        "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM2","D3", "Westminister Bell",         1,9999, "LOW",0,   "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RALARM2","D4","Button",       0,9999,  "MOMENTARY0",1, "NA","S",0);


insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RMOT","A7", "AC adapter",         3.1, 3.6, "VOLT",1,   "NA","S",1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("RMOT","D4","Sensor",       0,9999,  "MOMENTARY1",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification, no_default_state) values ("ZHAx9","HA6","On/Off",       0,9999,  "BINARY",0,   "NA","A",0,1);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification, no_default_state) values ("ZHAx100","HA6","On/Off",       0,9999,  "BINARY",0,   "NA","A",0,1);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification, no_default_state) values ("GLLx1","HA6","On/Off",       0,9999,  "BINARY",0,   "NA","A",0,1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification, no_default_state) values ("GLLx0","HA6","On/Off",       0,9999,  "BINARY",0,   "NA","A",0,1);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification, no_default_state) values ("GLLx10","HA6","On/Off",       0,9999,  "BINARY",0,   "NA","A",0,1);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ZHA0x101","HA6","On/Off",       0,9999,  "BINARY",0,   "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ZHA0x101","HA8","Dim",       0,9999,  "HADIM",0,   "NA","A",0);


insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("ZHA0x402","HA6","Water sensor",       0,9999,  "H2O",1,   "NA","S",0);

insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("GLLx100","HA6","On/Off",       0,9999,  "BINARY",0,   "NA","A",0);
insert into port_types (part_nbr, port,desc,alarm_value_low, alarm_value_high,logic, IO_direction, toggle_port,type, force_notification) values ("GLLx100","HA8","Dim",       0,9999,  "HADIM",0,   "NA","A",0);


insert into messages (short, long) values ("volt_prob", "Batteries need to be replaced");
insert into messages (short, long) values ("h20_prob", "Water detected");

DROP TABLE IF EXISTS event_description;
CREATE TABLE event_description (
desc CHAR NOT NULL  PRIMARY KEY,
text_to_display_in_range CHAR,
text_to_display_out_of_range CHAR
);
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('Water sensor','Moisture detected','Dry');
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('2 AA Batteries','Voltage ok','Voltage is low, time to replace');
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('AC adapter','AC Power is good','AC Power is out of specification');
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('Thermometer','Within your range','Out of desired range');
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('Button','Was pressed','Was pressed');
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('Switch','Closed','Open');
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('Front','Doorbell detected','Doorbell detected');
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('Rear','Doorbell detected','Doorbell detected');
INSERT INTO event_description (desc, text_to_display_in_range, text_to_display_out_of_range) VALUES ('USB Attached Camera','Camera','Camera');

UPDATE wireless_devices SET parent_network_address = NULL, my_network_address = NULL;

UPDATE actions SET disabled = 0;


DROP TABLE IF EXISTS xbee_changes;
CREATE TABLE xbee_changes (
part_nbr CHAR NOT NULL  PRIMARY KEY,
cmd CHAR DEFAULT NULL,
parm CHAR DEFAULT NULL
);



DROP TABLE IF EXISTS routing;
CREATE TABLE routing (
ah CHAR(8) NOT NULL ,
al CHAR(8) NOT NULL ,
na INTEGER,
dest_addr INTEGER,
next_hop  INTEGER,
PRIMARY KEY (ah,al,na,dest_addr,next_hop)
);

DROP TABLE if exists frames;
CREATE TABLE frames (
frame_id  INTEGER PRIMARY KEY,
xmit_time,
ah,
al,
port
);

EOF
    foreach my $i (2 .. 255)
    {
        $dt->do("INSERT INTO frames (frame_id) values (%s)", $i);
    }
    if ( $errors > 0 )
    {
        DBG&&$fp->prt("found %d errors during db data load", $errors);

    }
    #my ($s,$rid) = $dt->get_rec("select last_insert_rowid()");
    #printf STDERR "db: last_insert_rowid stat[%s] rid[%s]\n",$s,$rid;
}


sub dumpDB
{
    my ($db_name) = @_;
    my $z = new IO::Compress::Gzip 'db.gz' or die "IO::compress open failed";

    my $dt = db::open($db_name);

    my @lines = split /\n/, $tables;
    foreach my $l (@lines)
    {
        if ($l =~ /create\s*table\s*([a-z_]*)\s*\(/i)
        {
            my $table_name = $1;
            DBG&&$fp->prt("processing $table_name");
            my $rows = $dt->query_to_array_of_hash("SELECT * FROM $table_name");
            if ($rows)
            {
                my $sql = "INSERT INTO $table_name (";
                foreach my $r (@$rows)
                {
                   my @keys = keys %$r;
                   foreach my $f (@keys)
                   {
                       if ($r->{$f})
                       {
                           $sql .=  $f.',';
                       }
                   }
                   chop $sql;
                   $sql .= ') values (';
                   foreach my $f (@keys)
                   {
                       if ($r->{$f})
                       {
                           $sql .= $dt->quote($r->{$f}).',';
                       }
                   }
                   chop $sql;
                   $sql .= ")\n";
                   $z->print($sql);
                }
            }
        }
    }

}
#
# test area
main() if not caller();
sub main {
    my $dt = db::open("test.db"); 
    create_tables($dt);
}

1;
