package html;
# Copyright 2011,2018 by James E Dodgen Jr.  All rights reserved.
use strict;
use Carp;

my $styles = <<EOF;
<style>
hr {
    display: block;
    margin-top: 0.5em;
    margin-bottom: 0.5em;
    margin-left: auto;
    margin-right: auto;
    border-style: inset;
    border-width: 3px;
}
input[type=checkbox] {width:20px; height:20px;}
table.tbody, tr, td, th{
    border-collapse: collapse;
    }
table.tbody, tr td, th {
    border: 1px solid black;
    }

tr.dark {
    background-color:#B0B0B0 ;
    border: 1px solid black;
    border-collapse: collapse;
}
tr.top {
    vertical-align: top;
    text-align: center;
}
tr.alert {background-color:red;
    border: 1px solid black;
    border-collapse: collapse;
}

body {
    background-color: tan;
}

a:hover {
    background-color: yellow;
}

div.header {
    background-color:#888888;
    color:white;
    font-family: "Comic Sans MS", cursive, sans-serif;
    text-align:left;
    padding-left:5px;
}
div.nav {
    line-height:130%;
    background-color:#888888;
    width:115px;
    padding-left:5px;
    padding-right:5px;
    position:fixed;
    font-family: "Verdana", sans-serif;
    xfont-size: 130%;
    border: 2px solid brown;
    border-radius: 10px;
    text-align: center;
}
div.body {
    padding-left:135px;
    xwidth:600px;
}
div.border {
    xfloat:left;
    padding:5px;
    font-family: "Verdana", sans-serif;
    xborder: 4px solid #a1a1a1;
    xborder-radius: 10px;
}


}
div.footer {
    background-color:black;
    color:white;
    clear:both;
    text-align:left;
    padding:7px;
    font-family: "Comic Sans MS", cursive, sans-serif;
}
</style>
EOF




sub cgi_menu
{
    my $stuff = <<EOF;
     <div class=header>
     <h1>AlertAway</h1>
     </div>
    <div class="nav">
    <table border=1>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=main">Home</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=commission">Commission<br>New Devices</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=configuration">Change<br>Configuration</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=contacts">Contacts</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=alerts">Alerts</a></th></tr>
     <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=date">Set<br>Date/Time</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=trace">Diagnostic<br>Output</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl">admin page</a></th></tr>
      <tmpl_if name=state>
          <tr><th align=left><input type=submit name="state" value="<tmpl_var name=state>"></th></tr>
      </tmpl_if>
      <input type=hidden name=pan_id value=<tmpl_var name=pan_id>>
      <input type=hidden name=method value=<tmpl_var name=method>>
      <input type=hidden name=admin_state value="Edit:<tmpl_var name=pan_id>">
    </table>
    </div>
EOF
  return \($styles.$stuff);
}

sub menu
{
    my $stuff = <<EOF;

<div class=header>
<title>AlertAway&#64;Home</title>
<h1>AlertAway</h1>
</div>
<div class="nav">
      <a href="/">Home</a><br>
      <hr>
      <a href="configuration">Change<br>Configuration</a><br>
      <hr>
      <a href="contacts">Contacts</a><br>
      <hr>
      <a href="alerts#here">Alerts</a><br>
      <hr>
      <a href="location">Set<br>Location</a><br>
      <hr>
      <a href="system">Systems<br>Information</a>
      <!-- <hr>
      <a href="Debug">debug<br>Information</a> -->
      <tmpl_if name=state>
         <hr><br><input type=submit name="state" value="<tmpl_var name=state>">
      </tmpl_if>
</div>
EOF

  return \($styles.$stuff);
}


sub main_page
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<tmpl_var name=menu>
<div class="body">
<div class=border>
    <div>
    <div><tmpl_var name=sysid></div>
    <tmpl_if name=version>
       <div>Your Version = <tmpl_var name=version></div>
    </tmpl_if>
    <div>Restart reason - <tmpl_var name=restart_descr> (<tmpl_var name=restart_code>)</div>
    <div>Process run time <tmpl_var name=run_time></div>
    </div>
      <table class="tbody">
        <tr>
          <td colspan=100% align=left>
            <font color=red><tmpl_var name=msg></font>
          </td>
        </tr>
        <tr  class="dark">
          <th colspan=12 align=center>
            <font color=green size=+1>DEVICE STATUS</font>
          </th>
        </tr>
        <tr class="dark">
          <th>
            <input type=submit name="state" value="Update"><br>
            <input type=submit name="state" value="Commission ON"><br>
            <input type=submit name="state" value="Commission OFF"><br>
            <input type=submit name="state" value="Broadcast Node Discovery">
          </th>
          <th>Unit<br>Type</th>
          <th>Location</th>
          <th>Last</th>
          <th>Prev</th>
          <th>Signal<br>Strength</th>
          <th>Router<br><input type=submit name="state" value="Refresh"></th>
          <th>Device<br>and<br>Name</th>
          <th>Default<br>State<br></th>
          <th>Manual<br>Override<br></th>
          <th>WeMo<br>Emulation</th>
          <th>Status</th>
          <!-- <th><font color=red>Last<br>Change</font></th>  -->
        </tr>

        <tmpl_loop name=wireless_devices>
        <tmpl_unless name=supress_row>
        <tr <tmpl_if name=alert>class="alert"</tmpl_if>>
          <tmpl_if name=display>
          <td>
            <input type=submit name="state" value="Remove <tmpl_var name=drowid>" onClick="return confirm('are you sure you want to delete <tmpl_var name=physical_location> if it is still around it will return?')">
            <br>
            <input type=submit name="state" value="Update">
            <!-- <input type="hidden" name="<tmpl_var name=drowid>:trace" value="nothing">
            <br>Trace<input type="checkbox" name="<tmpl_var name=drowid>:trace" value="checked" <tmpl_var name=trace>> -->

          </td>
        <!-- <tmpl_var name=ah>   <tmpl_var name=al> <tmpl_var name=na> -->
          <td align=left>

          <abbr  title="Address: <tmpl_var name=addr_high_hex>:<tmpl_var name=addr_low_hex>:<tmpl_var name=na_hex> Device type: <tmpl_var name=part_nbr> Net addr: <tmpl_var name=na> Parent addr: <tmpl_var name=parent_network_address>"><tmpl_var name=part_desc></abbr>

          </td>
          <td align=left>

               <tmpl_if name=allow_loc>
                  <input size=12 value="<tmpl_var name=physical_location>" name="<tmpl_var name=drowid>:loc">
               <tmpl_else>
                  <b><tmpl_var name=physical_location></b>
               </tmpl_if>

          </td>
          <td align=center>
            <tmpl_if name=red_time> <font color=red> </tmpl_if>
            <tmpl_var name=last_time_in_cooked>
            <tmpl_if name=red_time> </font> </tmpl_if>
          </td>
          <td align=center>
            <tmpl_var name=previous_time_in_cooked>
          </td>
          <td align=center>
            <abbr  title="-dB level: <tmpl_var name=db_level>"><tmpl_var name=strength></abbr>
          </td>
          <td>
            <tmpl_var name=router>
          </td>
        <tmpl_else>
          <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td>
        </tmpl_if>
          <td align=left>

            <tmpl_if name=red_time> <font color=red> </tmpl_if>
            <abbr  title="Port: <tmpl_var name=port>"><tmpl_var name=port_desc></abbr>
            <tmpl_if name=red_time> </font> </tmpl_if>
            <tmpl_if name=wemo_device>
             <br>
             <input size=12 value="<tmpl_var name=port_name>" name="<tmpl_var name=srowid>:port_name">
            </tmpl_if>
          </td>


          <td>
             <tmpl_if name=default_can_change>
               <abbr  title="On/Off force the state. None ignores any manual setting of device">
               <input type="radio" name="<tmpl_var name=srowid>:default_state" value="-1" <tmpl_var name=default_none_checked>><tmpl_var name=port_none><br>
               <input type="radio" name="<tmpl_var name=srowid>:default_state" value="1" <tmpl_var name=default_on_checked>><tmpl_var name=port_on><br>
               <input type="radio" name="<tmpl_var name=srowid>:default_state" value="0" <tmpl_var name=default_off_checked>><tmpl_var name=port_off>
             </tmpl_if>
          </td>
           <td>
             <tmpl_if name=default_can_change>
               <abbr  title="Overrides remain in effect until another action like a Timed event or default takes place">
               <input type="radio" name="<tmpl_var name=srowid>:override_state" value="-1" <tmpl_var name=override_none_checked>><tmpl_var name=override_none><br>
               <input type="radio" name="<tmpl_var name=srowid>:override_state" value="1" <tmpl_var name=override_on_checked>><tmpl_var name=override_on><br>
               <input type="radio" name="<tmpl_var name=srowid>:override_state" value="0" <tmpl_var name=override_off_checked>><tmpl_var name=override_off><br>
               <tmpl_var name=external_override>
               </abbr>
             </tmpl_if>
          </td>
          <td align=left>
            <tmpl_if name=adjustable_device>
             Adjustment <input size=8 value="<tmpl_var name=adjustment>" name="<tmpl_var name=srowid>:adj"> <br>
             Alarm Low <input size=8 value="<tmpl_var name=alarm_low>" name="<tmpl_var name=srowid>:low">  <br>
             Alarm High <input size=8 value="<tmpl_var name=alarm_high>" name="<tmpl_var name=srowid>:high">
            </tmpl_if>
            <tmpl_if name=wemo_device>
             <input type="hidden" name="<tmpl_var name=srowid>:allow_wemo" value="nothing">
             <input type="checkbox" name="<tmpl_var name=srowid>:allow_wemo" value="checked" <tmpl_var name=allow_wemo_checked>>Emulate<br>
             <input type="hidden" name="<tmpl_var name=srowid>:invert_wemo" value="nothing">
             <input type="checkbox" name="<tmpl_var name=srowid>:invert_wemo" value="checked" <tmpl_var name=invert_wemo_checked>>Invert
            </tmpl_if>
          </td>
          <td align=center>
          <tmpl_if name=red_time> <font color=red> </tmpl_if>
           <!-- <tmpl_var name=value>  <tmpl_var name=current> -->
           <abbr  title="Raw value: <tmpl_var name=raw_value>"><tmpl_var name=value></abbr>
           <tmpl_if name=red_time> </font> </tmpl_if>
          </td>
         <!--  <td align=center>
            <abbr  title="<tmpl_var name=problem_date>"><font color=red><tmpl_var name=problem_time></font></abbr>
          </td> -->
        </tr>
        </tmpl_unless>
        </tmpl_loop>
      </table>
<table class="tbody">
  <tr class="dark">
    <th>
        <input type=submit name="state" value="Clear log">
    </th>
    <th>
      Message Log
    </th>
  </tr>
  <tr class="dark">
    <th>
      Date
    </th>
    <th>
      Message
    </th>
  </tr>
  <tmpl_loop name=error_log>
  <tr>
    <td>
      <tmpl_var name=time>
    </td>
    <td>
      <tmpl_var name=message>
    </td>
  </tr>
  </tmpl_loop>
</table>
</div>
</div>

<pre>
<tmpl_var name=email_string>
<tmpl_var name=login_comments>
</pre>
<!-- <tmpl_var name=login_comments> -->
</html>
EOF
return \$stuff;
}

#sub debug
#{
#my $stuff = <<EOF;
#<html>
#<tmpl_var name=form_action>
#<tmpl_loop name=hidden>
  #<input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
#</tmpl_loop>
#<tmpl_var name=menu>
#<div class="body">
#<div class=border>
      #<table class="tbody">
        #<tr>
          #<td colspan=100% align=left>
            #<font color=red><tmpl_var name=msg></font>
          #</td>
        #</tr>
        #<tr  class="dark">
          #<th colspan=100% align=center>
            #<font color=green size=+1>Debug</font>
          #</th>
        #</tr>
        #<tr class="dark">
          #<th colspan=100%>
            #<input type=submit name="state" value="Trace on">
            #&nbsp;&nbsp;<input type=submit name="state" value="Trace off">
            #&nbsp;&nbsp;<input type=submit name="state" value="Reboot" onClick="return confirm('are you sure?');">
          #</th>
        #</tr>
        #<tmpl_loop name=wireless_devices>
        #<tr>
          #<td>
            #<input type="hidden" name="<tmpl_var name=drowid>:trace" value="nothing">
            #<br>Trace<input type="checkbox" name="<tmpl_var name=drowid>:trace" value="checked" <tmpl_var name=trace>>
          #</td>
          #<td align=left>
            #<tmpl_var name=part_desc>
          #</td>
          #<td align=left>
               #<b><tmpl_var name=physical_location></b>
          #</td>
        #</tr>
        #</tmpl_loop>
      #</table>
#</div>
#</div>
#</html>
#EOF
#return \$stuff;
#}

sub emailed_status
{
my $stuff = <<EOF;
<table border=1>
<tr>
  <th>Unit<br>Type</th>
  <th>Location</th>
  <!-- <th>Signal<br>Strength</th>
     <th>Router</th> -->
  <th>Last<br>Sent</th>
  <th>Sensor<br>Type</th>
          <!-- <abbr  title="Address: <tmpl_var name=addr_high_hex>:<tmpl_var name=addr_low_hex>:<tmpl_var name=na_hex> Device type: <tmpl_var name=part_nbr> Net addr: <tmpl_var name=na> Parent addr: <tmpl_var name=parent_network_address>"><tmpl_var name=display><tmpl_var name=part_desc></abbr> -->
  <th>Name</th>
  <th>Current</th>
  <!-- <th>Last<br>Event</th> -->
</tr>
<tmpl_loop name=wireless_devices>
  <tmpl_unless name=supress_row>
    <tr <tmpl_if name=alert>bgcolor=red</tmpl_if>>
     <tmpl_if name="eatme">
       <tmpl_var name=drowid>   <tmpl_var name=srowid> <tmpl_var name=ah>  <tmpl_var name=na> <tmpl_var name=al><tmpl_var name=previous_time_in_cooked>
       <tmpl_var name=adjustment><tmpl_var name=alarm_low><tmpl_var name=alarm_high><tmpl_var name=trace>
       <tmpl_var name=ah>   <tmpl_var name=na>  <tmpl_var name=al> <tmpl_var name=default_can_change> <tmpl_var name=allow_loc> <tmpl_var name=external_override>
     </tmpl_if>
      <td align=left>
        <tmpl_if name=physical_location>
          <abbr  title="Address: <tmpl_var name=addr_high_hex>:<tmpl_var name=addr_low_hex>:<tmpl_var name=na_hex> Device type: <tmpl_var name=part_nbr> Net addr: <tmpl_var name=na> Parent addr: <tmpl_var name=parent_network_address>"><tmpl_var name=part_desc></abbr>
        </tmpl_if>
      </td>
      <td align=left>
         <tmpl_var name=physical_location>
      </td>
      <!-- <td align=center>
               <abbr  title="-dB level: <tmpl_var name=db_level>"><tmpl_var name=strength></abbr>
      </td>
      <td>
        <tmpl_var name=router>
      </td> -->
      <td align=center>
        <tmpl_var name=last_time_in_cooked>
      </td>
      <td align=left>
        <abbr  title="Port: <tmpl_var name=port>"><tmpl_var name=port_desc></abbr>

        <!-- <tmpl_var name=only_on> <tmpl_var name=port_type> <tmpl_var name=port_off><tmpl_var name=port_none>
        <tmpl_var name=port_on> <tmpl_var name=default_on_checked> <tmpl_var name=default_off_checked><tmpl_var name=default_none_checked>
       <tmpl_var name=override_none_checked> <tmpl_var name=override_none><tmpl_var name=display>
        <tmpl_var name=override_on_checked> <tmpl_var name=override_off_checked> <tmpl_var name=override_on> <tmpl_var name=override_off>  -->

      </td>

      <!--
      <td align=left>
          <tmpl_var name=sensor_desc> <tmpl_var name=port_name>
      </td>
      -->
      <td>
       <tmpl_var name=port_name>
      </td>
      <td>
       <tmpl_var name=value> <!--  <tmpl_var name=adjustable_device><tmpl_var name=invert_wemo> <tmpl_var name=invert_wemo_checked><tmpl_var name=wemo_device> <tmpl_var name=allow_wemo_checked><tmpl_var name=allow_wemo><tmpl_var name=current> <tmpl_var name=raw_value> -->
      </td>
      <!-- <td align=center>
        <abbr  title="<tmpl_var name=problem_date>"><tmpl_var name=problem_time></abbr>
      </td> -->
    </tr>
  </tmpl_unless>
</tmpl_loop>
</table>

EOF
return \$stuff;
}

sub form_action_cgi
{
    return '<body bgcolor=khaki><form  action=/cgi-bin/admin/aaadmin.pl method=POST>';
}

sub form_action_LAN
{
    return '<form  action="" method=post enctype="application/x-www-form-urlencoded">';
}

sub systems_info
{
my $stuff = <<EOF;
<html>
<title>SysInfo</title>
<tmpl_var name=form_action>
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<tmpl_var name=menu>
<div class="body">

<div><tmpl_var name=sysid></div>
<div>Your Version: <tmpl_var name=version>, Current version: <tmpl_var name=server_version></div>
<div>SQLite version: <tmpl_var name=sqlite></div>
<div>Restart reason: <tmpl_var name=restart_descr> (<tmpl_var name=restart_code>)</div>
<div>Process run time: <tmpl_var name=run_time></div>

<font color=red><tmpl_var name=msg></font><br>
<table>
        <tr class="dark">
         <th colspan=3>
          <font color=green>System Load</font>
         </th>
        </tr>
        <tr  class="dark">
         <th>
           <font color=green>Last Minute</font>
        </th>
        <th>
          <font color=green>Five Minutes</font>
        </th>
        <th>
          <font color=green>Fifteen Minutes</font>
        </th>
       </tr>
       <tr>
        <th align=center>
         <tmpl_var name=min1>%
        </th>
        <th align=center>
         <tmpl_var name=min5>%
        </th>
        <th align=center>
         <tmpl_var name=min15>%
        </th>
        </tr>
        </table>
        </td>
        </tr>
    </table>
<div><pre><tmpl_var name=text></pre></div>

</div>
</body>
</html>
EOF
return \$stuff;
}
#sub trace_list
#{
#my $stuff = <<EOF;
#<html>
#<tmpl_var name=form_action>
#<tmpl_loop name=hidden>
  #<input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
#</tmpl_loop>
#<center><h1>Alert Away Systems Information</h1>
#<tmpl_var name=menu>
#<div class="body">
#<table>

  #<tr>
    #<td valign=top style="width:140px">
    #<!-- <tmpl_var name=menux> -->
    #</td>
    #<td colspan=100% align=left>
      #<table border=1>
        #<tr>
        #<th> <input type=submit name="state" value="More">
             #<input type=submit name="state" value="Clear" onClick="return confirm('are you sure you want to clear our the trace log? if you want to stop it got to the configuration')">
        #</th>
        #<th colspan=100% align=left>
          #START AT: <input name="start_at" size=8 value="<tmpl_var name=start_at>">
          #SUB SYSTEM FILTER
          #<select name="subsystem_filter">
                    #<option value="<tmpl_var name=curr_ss_filter>"> <tmpl_var name=curr_ss_filter>
                    #<tmpl_loop name=sub_systems>
                      #<option value="<tmpl_var name=name>"> <tmpl_var name=name>
                    #</tmpl_loop>
                  #</select>
        #</th>
        #<tr>
          #<th>SEQUENCE
          #</th>
          #<th>SUB<br>SYSTEM
          #</th>
          #<th>MESSAGE
          #</th>
        #</tr>
        #<tmpl_loop name=items>
        #<tr>
          #<td>
            #<tmpl_var name=seq>
          #</td>
          #<td>
            #<tmpl_var name=name>
          #</td>
          #<td>
            #<tmpl_var name=msg>
          #</td>
        #</tr>
        #</tmpl_loop>
      #</table>
    #</td>
  #</tr>
#</table>
#<div>
#</font>
#</body>
#</html>
#EOF
#return \$stuff;
#}

sub simple_list
{
my $stuff = <<EOF;
<html>
<body bgcolor=tan>
<title>AlertAway&#64;External</title>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<table border=1>
  <tr>
    <th align=center colspan=100%>
       <font color=green size=+1><tmpl_var name=desc></font>
    </th>
  </tr>
  <tmpl_loop name=items>
  <tr>
    <th align=CENTER>
       <a href='<tmpl_var name=link>'><tmpl_var name=item></a>
    </th>
  </tr>
  </tmpl_loop>
</table>
</font>
</body>
</html>
EOF
return \$stuff;
}

sub contacts
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<title>AlertAway&#64;Home</title>
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<tmpl_var name=menu>
<div class="body"><div class=border>
    <table class=tbody>
      <tr>
        <td colspan=100% align=left>
          <font color=red><tmpl_var name=msg></font>
        </td>
      </tr>
      <tr class="dark">
        <th align=center colspan=100%>
          <font color=green size=+1>Who to contact</font>
        </th>
      </tr>
      <tr class="dark">
        <td align=left colspan=1>
          &nbsp;
        </td>
        <th>
          Contact name
        </th>
        <th>
          Email address
        </th>
        <th>
          TEXT<br>MESSAGE?
        </th>
      </tr>
      <tmpl_if name=msg>
        <tr>
         <th align=center colspan=100%><font color=red><tmpl_var name=msg></font></th>
        </tr>
      </tmpl_if>
      <tr>
        <td align=left colspan=1>
          <input type=submit name="state" value="Add contact">
        </td>
        <td>
          <input name="ADDCONTACT:contact" size=15 value="<tmpl_var name=addcontact>">
        </td>
        <td>
          <input name="ADDCONTACT:email" size=15 value="<tmpl_var name=addemail>">
        </td>
        <td align=center>
          <input type=checkbox name="ADDCONTACT:short" <tmpl_var name=addshort> value="checked" title="Check this when emailng to a phone as a text message, it will be less verbose and just the text">
        </td>
      </tr>
      <tmpl_loop name=contacts>
      <tr>
        <td align=left>
          <font size=+1>
            <b>
              <input type=submit name="state" value="Remove contact <tmpl_var name=rowid>">
            </b>
          <font>
        </td>
        <td>
          <tmpl_var name=contact>
        </td>
        <td>
          <tmpl_var name=email>
        </td>
        <td align=center>
          <b>
            <input type=checkbox disabled="disabled" <tmpl_var name=short>>
          </b>
        </td>
      </tr>
      </tmpl_loop>
    </table>
</div></div>
<pre>
<tmpl_var name=email_string>
<tmpl_var name=login_comments>
</pre>
<!-- <tmpl_var name=login_comments> -->
</html>
EOF
return \$stuff;
}

sub alerts
{
my $stuff = <<EOF;
<html>
<head>
<script>
function start_fixed_date() {
   document.getElementById("starthidefixed").style.display = '';
   document.getElementById("starthidedawn").style.display = 'none';
}
function start_dawn() {
   document.getElementById("starthidedawn").style.display = '';
   document.getElementById("starthidefixed").style.display = 'none';
}
function stop_fixed_date() {
   document.getElementById("stophidefixed").style.display = '';
   document.getElementById("stophidedawn").style.display = 'none';
}
function stop_dawn() {
   document.getElementById("stophidedawn").style.display = '';
   document.getElementById("stophidefixed").style.display = 'none';
}
</script>
</head>
<tmpl_var name=form_action>
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>

<tmpl_var name=menu>
<div class="body">
<div id="<tmpl_var name=alarms_here>" class=border>

            <table class="tbody">
              <tr>
                <th colspan=100% align=left>
                  <font color=red><tmpl_var name=msg></font>
                </th>
              </tr>
              <tr class="dark">
                <th colspan=100% align=left>
                  <input type=submit name="state" value="Map alarm">
                  &nbsp;&nbsp;
                  <input type=submit name="state" value="Test">
                  &nbsp;&nbsp;
                  <font size=+1 color=green>Map Sensors to Actions</font>
                </th>
              </tr>
              <tr class="dark">
                <th>
                  Select a sensor
                </th>
                <th>
                  Select<br>one or more<br>Actions
                </th>
              </tr>
              <tr>
                <td>
                  <select name="SENSORTOALARM:sensor" size=15>
                    <tmpl_loop name=sensors>
                      <option value="<tmpl_var name=ah>:<tmpl_var name=al>:<tmpl_var name=port>"
                      title="<tmpl_var name=devices_device_types_desc>:<tmpl_var name=port_types_desc>">
                       <tmpl_var name=desc>
                    </tmpl_loop>
                  </select>
                </td>
                <td>
                  <select name="SENSORTOALARM:alarm" size=15 multiple>
                    <tmpl_loop name=alerts>
                      <option value="<tmpl_var name=ah>:<tmpl_var name=al>:<tmpl_var name=port>:<tmpl_var name=logic>:<tmpl_var name=devices_rowid>"
                      title="<tmpl_var name=devices_device_types_desc>:<tmpl_var name=port_types_desc>">
                       <tmpl_var name=desc>
                      </option>
                       <abbr  title="Address: <tmpl_var name=addr_high_hex>:<tmpl_var name=addr_low_hex>:<tmpl_var name=na_hex> Device type: <tmpl_var name=part_nbr> Net addr: <tmpl_var name=na> Parent addr: <tmpl_var name=parent_network_address>"><tmpl_var name=part_desc></abbr>
                      </option>
                    </tmpl_loop>
                  </select>
                </td>
              </tr>
             </table>
                  <table class="tbody">
                    <tr class="dark">
                      <th colspan=100%>
                          Currently mapped
                      </th>
                    </tr>
                     <tr class="dark">
                        <th>
                        </th>
                        <th>
                          When Sensor
                        </th>
                        <th>
                        is
                        </th>
                        <th>
                          Then this
                        </th>
                        <th>
                         is
                        </th>
                        <th>

                          <span style="white-space: nowrap;" title=
"This can ether set the time in seconds a alert is activated,
like if a doorbell button is pushed the alarm should be short.
Or one of these special cases:
&quot;Follow&quot; - which will stay on until the sensor value clears.
&quot;Until Cleared&quot; - Which stays on even after a sensor changes,
    like a water sensor detecting a leak and controling a valve.
&quot;Clear&quot; - which is simply used to reset the above when problem has been corrected."
                            >Duration</span>
                        </th>
                        <th>
                        <span style="color:black;" title="This sets the porority for this alert. A higher priority will cause lower priority alerts to be disabled. This is usefull for example if a water leak detector wishes to turn off the water to a facility then the ON/OFF switch would be ignored.">Priority</span>
                        </th>
                        <th>

                          <span style="color:black;"Alerts get disabled when a higher Priority alert has gone off and caused the other alerts to be ignored. Just press the Enable button to clear .">Disabled?</span>

                        </th>
                      </tr>
                      <tmpl_loop name=mapped_alarms>
                      <tr>
                        <td>
                          <input type=submit name="state" value="Update Alert:<tmpl_var name=rowid>"><br>
                          <input type=submit name="state" value="Remove Alert:<tmpl_var name=rowid>">
                        </td>
                        <td>
                          <tmpl_var name=sensor_desc>
                        </td>
                        <td align=center>
                            <tmpl_if name=sensor_on_or_off>
                              <input type="radio" name="SENSORTOALARM:sensor_action:<tmpl_var name=rowid>" value="ON" <tmpl_var name=sensor_on_checked>>ON<br>
                              <input type="radio" name="SENSORTOALARM:sensor_action:<tmpl_var name=rowid>" value="OFF" <tmpl_var name=sensor_off_checked>>OFF
                            <tmpl_else>
                              ON <input name="SENSORTOALARM:sensor_action:<tmpl_var name=rowid>" size=10 value="ON" HIDDEN>
                            </tmpl_if>
                        </td>
                        <td>
                          <tmpl_var name=action_desc>
                        </td>
                        <td>
                            <input type="radio" name="SENSORTOALARM:action_action:<tmpl_var name=rowid>" value="ON" <tmpl_var name=action_on_checked>>ON<br>
                            <input type="radio" name="SENSORTOALARM:action_action:<tmpl_var name=rowid>" value="OFF" <tmpl_var name=action_off_checked>>OFF
                        </td>
                        <td>
                          <tmpl_if name=momentary>
                            <select name="SENSORTOALARM:duration:<tmpl_var name=rowid>" size=1>
                            <option value="<tmpl_var name=duration>"> <tmpl_var name=duration>
                            <optgroup label="Seconds">
                            <option value="1">1
                            <option value="2">2
                            <option value="5">5
                            <option value="10">10
                            <option value="20">20
                            <option value="30">30
                            <option value="60">60
                            <option value="Until Cleared">Until Cleared
                            <option value="Clear">Clear
                            </select>
                          <tmpl_else>
                              Follow <input name="SENSORTOALARM:duration:<tmpl_var name=rowid>" size=10 value="Follow" hidden>
                           </tmpl_if>
                        </td>
                        <td>
                           <select name="SENSORTOALARM:priority:<tmpl_var name=rowid>" size=1>
                            <option value="<tmpl_var name=priority>"> <tmpl_var name=priority>
                            <option value="1"> 1 Lowest
                            <option value="2"> 2
                            <option value="3"> 3
                            <option value="4"> 4
                            <option value="5"> 5 Default
                            <option value="6"> 6
                            <option value="7"> 7
                            <option value="8"> 8
                            <option value="9"> 9
                            <option value="10"> 10 Highest
                          </select>
                        </td>
                        <td>
                          <tmpl_if name=disabled>
                            <input type=submit name="state" value="Enable:<tmpl_var name=rowid>">
                          <tmpl_else>
                            Enabled
                          </tmpl_if>
                        </td>
                      </tr>
                      </tmpl_loop>
                    </table>
</div>
<hr>
<div id="<tmpl_var name=contacts_here>" class="border">
            <table class="tbody">
              <tr class="dark">
                <th colspan=100% align=left>
                  <input type=submit name="state" value="Map Contact">
                  &nbsp;&nbsp;&nbsp;&nbsp;
                  <font size=+1 color=green>Map Sensors to Contacts</font>
                </th>
              </tr>
              <tr class="dark">
                <th>
                  Select a Sensor
                </th>
                <th>
                  Select<br>one or more<br>Contacts
                </th>
              </tr>
              <tr>
                <td>
                  <select name=SENSORTOCONTACT:sensor size=15>
                    <tmpl_loop name=sensors>
                      <option value="<tmpl_var name=ah>:<tmpl_var name=al>:<tmpl_var name=port>"
                      title="<tmpl_var name=devices_device_types_desc>:<tmpl_var name=port_types_desc>">
                       <tmpl_var name=desc>
                    </tmpl_loop>
                  </select>
                </td>
                <td>
                  <select name=SENSORTOCONTACT:contact size=15 multiple>
                    <tmpl_loop name=contacts_name_only>
                      <option value="<tmpl_var name=contact>"> <tmpl_var name=contact>
                    </tmpl_loop>
                      <option value="UnMapSensor"> UNMAP SENSOR
                  </select>
                </td>
               </tr>
             </table>

            <table class="tbody">
                   <tr class="dark">
                    <th colspan=100%>
                      Currently mapped
                    </th>
                  </tr>
                  <tr class="dark">
                    <th>
                    </th>
                    <th>
                      Sensor
                    </th>
                    <th>
                      from
                    </th>
                    <th>
                      to
                    </th>
                    <th>
                      Contact
                    </th>
                    <!-- <th>
                      Frequency
                    </th> -->
                    <th>
                      Users state
                    </th>
                  </tr>
                  <tmpl_loop name=mapped_contacts>
                  <tr>
                    <td>
                     <input type=submit name="state" value="Update Contact:<tmpl_var name=rowid>"><br>
                     <input type=submit name="state" value="Remove Contact:<tmpl_var name=rowid>">
                    </td>
                    <td>
                      <tmpl_var name=sensor_desc>
                    </td>
                    <tmpl_if name=variable>
                        <td align=center>
                            <input type=number name="SENSORTOCONTACT:threshold_from:<tmpl_var name=rowid>" value="<tmpl_var name=threshold_from>" min="0" max="999">
                        </td>
                        <td align=center>
                            <input type=number name="SENSORTOCONTACT:threshold_to:<tmpl_var name=rowid>" value="<tmpl_var name=threshold_to>" min="0" max="999">
                        </td>
                    <tmpl_else>
                      <td align=center>
                               Any Change
                      </td>
                      <td></td>
                    </tmpl_if>

                    <td>
                      <tmpl_var name=contact>
                    </td>
                    <!-- <td>
                          <select name="SENSORTOCONTACT:freq:<tmpl_var name=rowid>" size=1>
                            <option value="<tmpl_var name=freq>"> <tmpl_var name=freq>
                            <option value="Once">Once
                            <option value="Hourly">Hourly
                            <option value="Daily">Daily
                          </select>
                    </td> -->
                    <td>
                      <tmpl_var name=state>
                    </td>
                   </tr>
                  </tmpl_loop>
                </table>
</div>
<hr>
<div id="<tmpl_var name=timers_here>" class="border">
            <table class="tbody">
              <tr>
                <th colspan=100% align=left>
                  <font color=red><tmpl_var name=timer_msg></font>
                </th>
              </tr>
              <tr class="dark">
                <th colspan=100% align=left>
                  <input type=submit name="state" value="Set timer">
                  &nbsp;&nbsp;&nbsp;&nbsp;<tmpl_var name=debug>
                  <font size=+1 color=green>Timed Alerts <tmpl_var name=time_now></font>
                </th>
              </tr>
              <tr class="dark">
                <th>
                  Select Alert
                </th>
                <th>
                  Set Time
                </th>
              </tr>
              <tr>
                <td>
                  <select name="TIMED:alert" size=15 multiple>
                    <tmpl_loop name=alerts>
                      <option value="<tmpl_var name=ah>:<tmpl_var name=al>:<tmpl_var name=port>:<tmpl_var name=logic>:<tmpl_var name=devices_rowid>"
                      title="<tmpl_var name=devices_device_types_desc>:<tmpl_var name=port_types_desc> <tmpl_var name=al>">
                      <tmpl_var name=desc>
                      </option>
                    </tmpl_loop>
                  </select>
                </td>
                <td>
                <input type="checkbox" name="TIMED:days" value="0" checked>Sun
                <input type="checkbox" name="TIMED:days" value="1" checked>Mon
                <input type="checkbox" name="TIMED:days" value="2" checked>Tue<br>
                <input type="checkbox" name="TIMED:days" value="3" checked>Wed
                <input type="checkbox" name="TIMED:days" value="4" checked>Thu
                <input type="checkbox" name="TIMED:days" value="5" checked>Fri<br>
                <input type="checkbox" name="TIMED:days" value="6" checked>Sat
                <table class=tbody>
                  <tr class="dark">
                    <th colspan=1>
                    Start Time
                    </th>
                    <th colspan=1>
                    Stop Time
                    </th>
                  </tr>
                  <tr class="dark">
                    <th colspan=1>
                    Fixed <input type=radio onClick="start_fixed_date();" name=TIMED:start value="Fixed" checked >
                    Sunrise <input type=radio onClick="start_dawn();" name=TIMED:start value="Sunrise">
                    Sunset <input type=radio onClick="start_dawn();" name=TIMED:start value="Sunset">
                    </th>
                    <th colspan=1>
                    Fixed <input type=radio onClick="stop_fixed_date();" name=TIMED:stop value="Fixed" checked >
                    Sunrise <input type=radio onClick="stop_dawn();" name=TIMED:stop value="Sunrise">
                    Sunset <input type=radio onClick="stop_dawn();" name=TIMED:stop value="Sunset">
                    </th>
                  </tr>
                  <tr>
                    <td>
                        <table id="starthidefixed">
                            <tr>
                            <th>
                                Hour(24):Minute
                            </th>
                            </tr>
                            <tr>
                            <td><input type=number name=TIMED:starthour min=1 max=24 value=6>
                            :
                            <input type=number name=TIMED:startminute min=0 max=59 value=30>
                            </td>
                            </tr>
                        </table>
                        <table id="starthidedawn"  style="display: none;">
                            <tr>
                            <th>
                                Offset Minutes (+-)
                            </th>
                            </tr>
                            <tr>
                            <td>
                                <input type=number name=TIMED:startoffset min=-2000 max=2000 value=0>
                            </td>
                            </tr>
                        </table>
                    </td>

                  <td>
                        <table id="stophidefixed">
                            <tr>
                            <th>
                                Hour(24):Minute
                            </th>
                            </tr>
                            <tr>
                            <td><input type=number name=TIMED:stophour min=1 max=24 value=6>
                            :
                            <input type=number name=TIMED:stopminute min=0 max=59 value=30>
                            </td>
                            </tr>
                        </table>
                        <table id="stophidedawn"  style="display: none;">
                            <tr>
                            <th>
                                Offset Minutes (+-)
                            </th>
                            </tr>
                            <tr>
                            <td>
                                <input type=number name=TIMED:stopoffset min=-2000 max=2000 value=0>
                            </td>
                            </tr>
                        </table>
                    </td>
                  </tr>
                  <tr class="dark">
                    <th colspan=2>
                    Action On or Off
                    </th>
                  </tr>
                  <tr>
                    <th colspan=2>
                       <input type="radio" name="TIMED:state" value="1" checked >ON

                       <input type="radio" name="TIMED:state" value="0">OFF
                    </th>
                  </tr>
                </table>
                </td>
              </tr>
            </table>
            <table class="tbody">
              <tr class="dark">
                <th colspan=100%>
                  CurrentTimers
                </th>
              </tr>
              <tr class="dark">
                <th>
                  &nbsp;
                </th>
                <th>
                  Alert
                </th>
                <th>
                  Days
                </th>
                <th>
                  Start
                </th>
                <th>
                  Stop
                </th>
                <th>
                  On/Off
                </th>
              </tr>
              <tmpl_loop name=timed_alerts>
              <tr>
                <td>
                <input type=submit name="state" value="Remove Timer:<tmpl_var name=rowid>">
                </td>
                <td>
                  <tmpl_var name=desc>
                </td>
                <td align=center>
                  <tmpl_var name=days>
                </td>
                <td align=center>
                  <abbr title="start info here"><tmpl_var name=start></abbr>
                </td>
                <td align=center>
                  <tmpl_var name=stop>
                </td>
                <td align=center>
                  <tmpl_var name=state>
                </td>
              </tr>
              </tmpl_loop>
            </table>
</div>
<tmpl_if name=have_cameras>
<hr>
<div id="<tmpl_var name=cameras_here>" class="border">
            <table  class="tbody">
              <tr class="dark">
                <th colspan=100% align=left>
                  <input type=submit name="state" value="Map Camera">
                  &nbsp;&nbsp;&nbsp;&nbsp;
                  <font size=+1 color=green>Map Sensors to Cameras</font>
                </th>
              </tr>
              <tr class="dark">
                <th colspan=2>
                  Select a Sensor
                </th>
                <th colspan=3>
                  Select<br>one or more<br>Cameras
                </th>
              </tr>
              <tr>
                <td colspan=2>
                  <select name=SENSORTOCAMERA:sensor size=15>
                    <tmpl_loop name=sensors>
                      <option value="<tmpl_var name=ah>:<tmpl_var name=al>:<tmpl_var name=port>"
                      title="<tmpl_var name=devices_device_types_desc>:<tmpl_var name=port_types_desc>">
                       <tmpl_var name=desc>
                    </tmpl_loop>
                  </select>
                </td>
                <td colspan=3>
                  <select name=SENSORTOCAMERA:camera size=15 multiple>
                    <tmpl_loop name=cameras_name_only>
                      <option value="<tmpl_var name=camera>"> <tmpl_var name=camera>
                    </tmpl_loop>
                      <option value="UnMapSensor"> UNMAP SENSOR
                  </select>
                </td>
              </tr>
              <tr class="dark">
                <th colspan=100%>
                  Currently mapped
                </th>
              </tr>
              <tr class="dark">
                <th>
                  &nbsp;
                </th>
                <th>
                  Sensor
                </th>
                <th>
                  Camera
                </th>
                <th>
                  Repeat
                </th>
                <th>
                  Delay (After first capture)
                </th>
              </tr>
              <tmpl_loop name=mapped_cameras>
              <tr>
                <td>
                <input type=submit name="state" value="Update Options:<tmpl_var name=rowid>">
                <td>
                  <tmpl_var name=sensor_desc>
                </td>
                <td>
                  <tmpl_var name=camera>
                </td>
                <td>
                  <input type=text name="<tmpl_var name=rowid>:repeat_count" value='<tmpl_var name=repeat_count>'>
                </td>
                <td>
                  <input type=text name="<tmpl_var name=rowid>:repeat_delay" value='<tmpl_var name=repeat_delay>'>
                </td>
              </tr>
              </tmpl_loop>
            </table>
    </div>
</tmpl_if>
</div>



<pre>
<tmpl_var name=email_string>
<tmpl_var name=login_comments>
</pre>
<!-- <tmpl_var name=login_comments> -->
</html>
EOF
return \$stuff;
}

sub configuration
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<tmpl_var name=menu>
<div class="body">
    <table class="tbody">
      <tr  class="dark">
        <th colspan=2 align=left>
          <input type=submit name="state" value="Update">&nbsp;&nbsp;&nbsp;&nbsp;
          <font size=+1 color=green>Configuration values</font>
          <tmpl_if name=display_reboot>
            &nbsp;&nbsp;<input type=submit name="state" value="Reboot" onClick="return confirm('are you sure?');">
            <!-- &nbsp;&nbsp;<input type=submit name="state" value="Trace on">
            &nbsp;&nbsp;<input type=submit name="state" value="Trace off"> -->
          </tmpl_if>
        </th>
      </tr>
      <tr>
      <font color=red><tmpl_var name=msg></font>
      </tr>
      <tr>
        <th>
            Identification
        </th>
        <td>
          <input name="CONFIG:ident" size=20 value="<tmpl_var name=currident>">
        </td>
      </tr>
      <tr>
        <th>
          Pass Phrase
        </th>
        <td>
          <input name="CONFIG:password" size=25 value="<tmpl_var name=password>">
        </td>
      </tr>
      <tr>
        <th>
            Problem reporting frequency
        </th>
        <td>
          <input name="CONFIG:freq" size=6 value="<tmpl_var name=currfreq>">&nbsp;Minutes
        </td>
      </tr>
      <tr>
        <th>
            WeMo base port number
        </th>
        <td>
          <input name="CONFIG:wemo" size=6 value="<tmpl_var name=currwemo>">
        </td>
      </tr>
      <tr>
        <th>
          Primary contact
        </th>
        <td>
          <select name=CONFIG:contact>
            <tmpl_if name=currprimary>
              <option value="<tmpl_var name=currprimary>"><tmpl_var name=currprimary>
            </tmpl_if>
            <tmpl_loop name=contacts>
              <option value="<tmpl_var name=email>"> <tmpl_var name=contact> -- <tmpl_var name=email>
            </tmpl_loop>
          </select>
        </td>
      </tr>
      <tr>
        <th>
          Connection Type
        </th>
        <td>
          <select name=CONFIG:contype title='If you change the IP address you will need to reboot'>
            <tmpl_if name=currcontype>
              <option value="<tmpl_var name=currcontype>"><tmpl_var name=currcontype>
            </tmpl_if>
            <option value="DHCP">DHCP
            <option value="STATIC IP">STATIC IP
          </select>
        </td>
      </tr>
      <tr>
        <th>
          External HTTP Server Port
        </th>
        <td>
          <input name="CONFIG:port" size=6 value="<tmpl_var name=currport>">
        </td>
      </tr>
      <tr>
        <th>
          Static IP address
        </th>
        <td>
          <input name="CONFIG:ip" size=16 value="<tmpl_var name=currip>">
          <br><tmpl_var name=curripmsg>
        </td>
      </tr>
      <tr>
        <th>
          Subnet Mask
        </th>
        <td>
          <input name="CONFIG:mask" size=16 value="<tmpl_var name=currmask>">
          <br><tmpl_var name=currmaskmsg>
        </td>
      </tr>
      <tr>
        <th>
          Gateway
        </th>
        <td colspan=3>
          <input name="CONFIG:gw" size=16 value="<tmpl_var name=currgw>">
          <br><tmpl_var name=currgwmsg>
        </td>
      </tr>
      <tr>
        <th>
          Domain Name Server 1
        </th>
        <td>
          <input name="CONFIG:dns1" size=16 value="<tmpl_var name=currdns1>">
          <br><tmpl_var name=currdns1msg>
        </td>
      </tr>
      <tr>
        <th>
          Domain Name Server 2
        </th>
        <td>
          <input name="CONFIG:dns2" size=16 value="<tmpl_var name=currdns2>">
          <br><tmpl_var name=currdns2msg>
        </td>
      </tr>
      <tr>
        <th>
          Metric Units
        </th>
        <td>
          <input type=checkbox name="CONFIG:metric_units" value=checked <tmpl_var name=currunits>>
        </td>
      </tr>
      <tr>
        <th>
          simpleNVR IP Address
        </th>
        <td>
          <input name="CONFIG:zmip" size=16 value="<tmpl_var name=dvrip>">
          <br><tmpl_var name=dvripmsg>
        </td>
      </tr>
      <tr>
        <th>
          simpleNVR Port
        </th>
        <td>
          <input name="CONFIG:zmport" size=8 value="<tmpl_var name=dvrport>">
          <br><tmpl_var name=dvrportmsg>
        </td>
      </tr>
      <tr>
        <th>
          simpleNVR user
        </th>
        <td>
          <input name="CONFIG:zmuser" size=8 value="<tmpl_var name=dvruser>">
          <br><tmpl_var name=dvrusermsg>
        </td>
      </tr>
      <tr>
        <th>
          simpleNVR Password
        </th>
        <td>
          <input name="CONFIG:zmpass" size=8 value="<tmpl_var name=dvrpass>">
          <br><tmpl_var name=dvrpassmsg>
        </td>
      </tr>
      <tr>
        <th>
          Coordinator communications<br>configuration<br>
          <input type=submit name="state" value="Get Coordinator">
          <input type=submit name="state" value="Set Coordinator" onClick="return confirm('are you sure?');">
         </th>
        <td>
          Pan ID 64 = <tmpl_var name=currpid64>
          Pan ID 16 = <tmpl_var name=currpid16>
          <br>
          operating channel=<tmpl_var name=curroperch>&nbsp
          stack_profile=<tmpl_var name=currstackpro>
        </td>
      </tr>

    </table>
<div>

<pre>
<tmpl_var name=email_string>
<tmpl_var name=login_comments>
</pre>
<!-- <tmpl_var name=login_comments> -->
</font>
</form>
</body>
</html>
EOF
return \$stuff;
}

sub extern
{
my $stuff = <<EOF;

<tmpl_var name=result>
EOF
return \$stuff;
}
sub location
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<tmpl_var name=menu>
<div class="body">
    <table class="tbody">
      <tr>
        <td colspan=100% align=left>
          <font color=red><tmpl_var name=msg></font>
       </td>
      </tr>
    <tr class="dark">
     <th>
      Date/Time
      </th>
    <th halign=center>
     Timezones
    </th>
    <th>
     Current Date and Time (24 Hour format)
    </th>
   <tr>
      <td halign=center>
        <input type=submit name="state" value="Set Timezone">
      </td>
    <td halign=center>
     <select name="timezone" id="timezone">
     <option value="<tmpl_var name=timezone>"><tmpl_var name=timezone>
     <tmpl_loop name=zones>
      <option value="<tmpl_var name=loc>"><tmpl_var name=loc></option>
     </tmpl_loop>
     </select>
    </td>
    <th halign=center>
        <tmpl_var name=day>-<tmpl_var name=month>-<tmpl_var name=year>
        &nbsp;
        <tmpl_var name=hour>:<tmpl_var name=minute>
    </th>
    </tr>
    <tr class="dark">
     <th>
      Geo Location
     </th>
    <th halign=center>
     Latitude
    </th>
    <th>
     Longitude
    </th>
   <tr>
      <td halign=center>
        <input type=submit name="state" value="Set Geo Location">
      </td>
    <th halign=center>
     <input type=number name="latitude", value=<tmpl_var name=latitude> min="-90" max="90" step="0.00001">
    </th>
    <th halign=center>
        <input type=number name="longitude", value=<tmpl_var name=longitude> min="-180" max="180" step="0.00001">
    </th>
    </tr>
    <tr>
     <th colspan=100%>
      <tmpl_var name=riseset>
     </th>
    </tr>
  </table>
<div>
</html>
EOF
return \$stuff;
}

sub motion_mask
{
my $stuff = <<EOF;
<!DOCTYPE html>
<html>
<head>
<style>
table {
    background: url(<tmpl_var name=jpeg>);
    background-size: <tmpl_var name=width>px <tmpl_var name=height>px;
    background-repeat: no-repeat;
    height: <tmpl_var name=height>px;
    width:  <tmpl_var name=width>px;
    border: 1px solid black;
    border-collapse: collapse;
}

td, tr { border: 1px solid black;}

</style>
</head>
<body>
<input type=hidden name="<tmpl_var name=camera_nbr>" value="<tmpl_var name=camera_name>">
<table>
  <tmpl_loop name=rows>
  <tr>
    <tmpl_loop name=columns>
    <td align=center><input type=checkbox name=cell_selected value='<tmpl_var name=cell_id>' <tmpl_var name=checked>></td>
    </tmpl_loop
  </tr>
  </tmpl_loop>
</table>

</body>
</html>
EOF
return \$stuff;
}

sub index_html
{
my $stuff = <<EOF;
<!DOCTYPE html>
<html>
<body>
<h1>Alertaway\@Home</h1>
<br>
<a href='/dvr'>DVR Viewer</a>
<br>
<!-- <a href='https://logout\@<tmpl_var name=ip_addr>'>Logout</a> -->
</body>
</html>
EOF
return \$stuff;
}


# test area
main() if not caller();
sub main {
    main_page();
}

1;
