package html;
# Copyright 2011 by James E Dodgen Jr.  All rights reserved. 
use strict;
use Carp;

sub cgi_menu
{
  my $stuff = <<EOF;
    <table border=1 bgcolor=green>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=main">Home</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=configuration">Change Configuration</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=contacts">Contacts</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=alarms">Alarms</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=cameras">Cameras</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=date">Set date/Time</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl?admin_state=Edit:<tmpl_var name=pan_id>&method=trace">Diagnostic Output</a></th></tr>
      <tr><th align=left><a href="/cgi-bin/admin/aaadmin.pl">admin page</a></th></tr>
      <input type=hidden name=pan_id value=<tmpl_var name=pan_id>>
      <input type=hidden name=method value=<tmpl_var name=method>>
      <input type=hidden name=admin_state value="Edit:<tmpl_var name=pan_id>">
    </table>
EOF
  return \$stuff;
}


sub menu
{
  my $stuff = <<EOF;
    <table border=1 bgcolor=green>
      <tr><th align=left><a href="/">Home</a></th></tr>
      <tr><th align=left><a href="configuration">Change Configuration</a></th></tr>
      <tr><th align=left><a href="contacts">Contacts</a></th></tr>
      <tr><th align=left><a href="alarms">Alarms</a></th></tr>
      <tr><th align=left><a href="cameras">Cameras</a></th></tr>
      <tr><th align=left><a href="date">Set date/Time</a></th></tr>
      <tr><th align=left><a href="system">Systems Information</a></th></tr>
      <tr><th align=left><a href="trace">Diagnostic Output</a></th></tr>
    </table>
EOF
  return $stuff;
}

sub main_page 
{
my $stuff = <<EOF;
<html>
<title>AlertAway&#64;Home</title>
<tmpl_var name=form_action>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<center><h1>Alert Away</h1>
<table>  
  
  <tr>    
    <th colspan=1000 align=left>
    <tmpl_var name=sysid><br>
    <tmpl_if name=version>    
        Your Version = <tmpl_var name=version>, Current version = <tmpl_var name=server_version><br>
    </tmpl_if>
        Restart reason - <tmpl_var name=restart_descr> (<tmpl_var name=restart_code>)                   
    </th>
  </tr>
  
  <tr>
    <td valign=top>
     <tmpl_var name=menu>
    </td>
    <td colspan=100% align=center>      
      <table border=1>
        <tr>
          <th align=left colspan=1>
            <input type=submit name="state" value="Update">
          </th>
          <th colspan=11 align=center>
            <font color=green size=+1>DEVICE STATUS</font> Process run time <tmpl_var name=run_time>
          </th>
        </tr>
        <tr>
          <th>Remove</th>                    
          <th>Unit<br>Type</th>
          <th>Location</th>
          <th>Last</th> 
          <th>Prev</th>
          <th>Sensor<br>Type</th>
          <th>Where</th>
          <th>Adjustment</th>
          <th>Range<br>Low</th>
          <th>Range<br>High</th>
          <th>Current</th>
          <th><font color=red>Last<br>Event</font></th>
        </tr> 
        <tmpl_loop name=wireless_devices>
        <tr>    
          <td>
          <tmpl_if name=physical_location>
            <input type=submit name="state" value="Remove <tmpl_var name=drowid>" onClick="return confirm('are you sure you want to delete <tmpl_var name=physical_location> if it is still around it will return?')">
          </tmpl_if>
          </td>
        <!-- <tmpl_var name=addr_high>   <tmpl_var name=addr_low> -->          
          <td align=left>
            <tmpl_if name=physical_location>
              <abbr  title="Address: <tmpl_var name=addr_high_hex>:<tmpl_var name=addr_low_hex> Device type: <tmpl_var name=part_nbr>"><tmpl_var name=part_desc></abbr>
            </tmpl_if>             
          </td>
          <td align=left>
            <tmpl_if name=physical_location>
              <input size=12 value="<tmpl_var name=physical_location>" name="<tmpl_var name=drowid>:loc">                     
            </tmpl_if>
          </td>
          <td align=center>
            <tmpl_var name=last_time_in_cooked>
          </td>
          <td align=center>
            <tmpl_var name=previous_time_in_cooked>
          </td>     
          <td align=left>           
            <abbr  title="Port: <tmpl_var name=port>"><tmpl_var name=port_desc></abbr>
          </td>
          <td align=left>           
              <input size=8 value="<tmpl_var name=sensor_desc>" name="<tmpl_var name=srowid>:sensor_desc">                     
          </td>
          <td align=left>           
              <input size=8 value="<tmpl_var name=adjustment>" name="<tmpl_var name=srowid>:adj">                     
          </td>          
          <td align=left>           
              <input size=8 value="<tmpl_var name=alarm_low>" name="<tmpl_var name=srowid>:low">                     
          </td>
          <td align=left>           
              <input size=8 value="<tmpl_var name=alarm_high>" name="<tmpl_var name=srowid>:high">                     
          </td>
          <td>
           <tmpl_var name=value>
          </td>
          <td align=center>
            <abbr  title="<tmpl_var name=problem_date>"><font color=red><tmpl_var name=problem_time></font></abbr>
          </td>       
        </tr>
        </tmpl_loop>
      </table>
    </td>
  </tr>
</table>

<table border=1>
  <tr>
    <th>
        <input type=submit name="state" value="Clear log"> 
    </th>
    <th>
      Message Log
    </th>
  </tr>
  <tr>
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

sub emailed_status 
{
my $stuff = <<EOF;    
<table border=1>
<tr>                
  <th>Unit<br>Type</th>
  <th>Location</th>
  <th>Last<br>Sen</th> 
  <th>Sensor<br>Type</th>
  <th>Where</th>
  <th>Current</th>
  <th><font color=red>Last<br>Event</font></th>
</tr> 
<tmpl_loop name=wireless_devices>
	<tr>    
	<tmpl_if name="eatme">
	   <tmpl_var name=drowid>	<tmpl_var name=srowid> <tmpl_var name=addr_high>   <tmpl_var name=addr_low><tmpl_var name=previous_time_in_cooked>
       <tmpl_var name=adjustment><tmpl_var name=alarm_low><tmpl_var name=alarm_high>  
	   <tmpl_var name=addr_high>   <tmpl_var name=addr_low>
	 </tmpl_if>          
	  <td align=left>
		<tmpl_if name=physical_location>
		  <abbr  title="Address: <tmpl_var name=addr_high_hex>:<tmpl_var name=addr_low_hex> Device type: <tmpl_var name=part_nbr>"><tmpl_var name=part_desc></abbr>
		</tmpl_if>             
	  </td>
	  <td align=left>
		 <tmpl_var name=physical_location>                     
	  </td>
	  <td align=center>
		<tmpl_var name=last_time_in_cooked>
	  </td>  
	  <td align=left>           
		<abbr  title="Port: <tmpl_var name=port>"><tmpl_var name=port_desc></abbr>
	  </td>
	  <td align=left>           
		  <tmpl_var name=sensor_desc>                     
	  </td>         
	  <td>
	   <tmpl_var name=value>
	  </td>
	  <td align=center>
		<abbr  title="<tmpl_var name=problem_date>"><font color=red><tmpl_var name=problem_time></font></abbr>
	  </td>       
	</tr>
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
	return '<body bgcolor=tan><form  action="" method=post enctype="application/x-www-form-urlencoded">';
}

sub systems_info 
{
my $stuff = <<EOF;
<html>
<title>SysInfo</title>
<tmpl_var name=form_action>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<center><h1>Alert Away Systems Information</h1>
<table>   
  
  <tr>
    <td valign=top>
     <tmpl_var name=menu>
    </td>
    <td colspan=100% align=left>
     <pre>    
<tmpl_var name=sysid>
Your Version = <tmpl_var name=version>, Current version = <tmpl_var name=server_version>
Restart reason - <tmpl_var name=restart_descr> (<tmpl_var name=restart_code>) 
Process run time <tmpl_var name=run_time> 
                 
<tmpl_var name=text>
     </pre>
    </td>
  </tr>
</table> 
</font>
</body>
</html>
EOF
return \$stuff;
}
sub trace_list 
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<center><h1>Alert Away Systems Information</h1>
<table>   
  
  <tr>
    <td valign=top>
     <tmpl_var name=menu>
    </td>
    <td colspan=100% align=left>
      <table border=1>
        <tr>
        <th> <input type=submit name="state" value="More">
          
        </th>
        <th colspan=100% align=left>
          START AT: <input name="start_at" size=8 value="<tmpl_var name=start_at>">
          SUB SYSTEM FILTER 
          <select name="subsystem_filter"> 
                    <option value="<tmpl_var name=curr_ss_filter>"> <tmpl_var name=curr_ss_filter> 
                    <tmpl_loop name=sub_systems>
                      <option value="<tmpl_var name=name>"> <tmpl_var name=name>             
                    </tmpl_loop>
                  </select>
        </th>
        <tr>
          <th>SEQUENCE
          </th>
          <th>SUB<br>SYSTEM
          </th>
          <th>MESSAGE
          </th>
        </tr>   
        <tmpl_loop name=items>
        <tr>
          <td>
            <tmpl_var name=seq>
          </td>
          <td>
            <tmpl_var name=name>
          </td>
          <td>
            <tmpl_var name=msg>
          </td>
        </tr>          
        </tmpl_loop>
      </table>
    </td>
  </tr>
</table> 
</font>
</body>
</html>
EOF
return \$stuff;
}


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
<center><h1>Alert Away</h1>
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

sub cameras 
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<title>AlertAway&#64;Home</title>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<center><h1>Alert Away</h1>
<table>
  <tr>
    <td valign=top>
    <tmpl_var name=menu>
    </td>
    <td colspan=100% align=center>
      <table>
        <tr>
          <td colspan=100%>
            <table border=1>
              <tr>
              <th align=left colspan=1>
                <font size=+1>

                  </font>
                </th>
                <th align=center colspan=7>
                  <font color=green size=+1>Cameras</font>
                </th>
              </tr>
              <tr>
                <th>
                  &nbsp;
                </th>                         
                <th>
                  Camera name
                </th>
                <th>
                  Server
                </th>
                <th>
                  IP ADDR
                </th>
                <th>
                  Port
                </th>
                <th>
                  User
                </th>
                <th>
                  Password
                </th>
                <th>
                  Allow<br>External<br>Access?
                </th>
                <th>
                 Refresh Rate
                </th>
                <th>
                 Pre Reads
                </th><th>
                 Send<br>Raw<br>Image?
                </th>
              </tr>              
              <tmpl_loop name=cameras>
              <tr>
                <td align=left>
                  <tmpl_if name=camera_name>
                    <img height=120 width=160 src="/snapshot/<tmpl_var name=camera_name>">
                  </tmpl_if>
                </td>
                <td align=left>
                  <b>
                  <input type=submit name="state" value="Update">
                  <input type=text name="<tmpl_var name=rowid>:camera_name" value="<tmpl_var name=camera_name>">
                  <br>
                  <TMPL_UNLESS  name=readonly>
                    <input type=submit name="state" value="Delete <tmpl_var name=rowid>">
                  </TMPL_UNLESS>
                  </b>
                </td>
                <td align=left>
                  <input type=text readonly value="<tmpl_var name=server>">
                </td>
                <td align=left>
                  <input type=text <tmpl_var name=readonly> name="<tmpl_var name=rowid>:ip_addr" value="<tmpl_var name=ip_addr>">
                </td>
                <td align=left>
                  <input type=text <tmpl_var name=readonly> name="<tmpl_var name=rowid>:port" value="<tmpl_var name=port>">
                </td>
                <td align=left>
                  <input type=text <tmpl_var name=readonly> name="<tmpl_var name=rowid>:user" value="<tmpl_var name=user>">
                </td>
                <td align=left>
                  <input type=text <tmpl_var name=readonly> name="<tmpl_var name=rowid>:password" value="<tmpl_var name=password>">
                </td>
                <td align=center>
                  <b>
                    <input type=checkbox name="<tmpl_var name=rowid>:wan_access" value="checked" <tmpl_var name=wan_access>>
                  </b>
                </td>
                <td align=right>
                  <input type=text name="<tmpl_var name=rowid>:refresh_rate" value="<tmpl_var name=refresh_rate>">
                </td>
                <td align=right>
                  <input type=text name="<tmpl_var name=rowid>:pre_reads" value="<tmpl_var name=pre_reads>">
                </td>
                <td align=center>
                  <b>
                    <input type=checkbox name="<tmpl_var name=rowid>:raw"  value="checked" <tmpl_var name=raw>>
                  </b>
                </td>
              </tr>
              </tmpl_loop>
              <tr>
                <td align=left>
                   <input type=submit name="state" value="Add">
                </td>
                <td align=left>
                  <input type=text name="add_camera_name">
                </td>
                <td align=left>
                  <select name=add_server>
                    <option value="TRENDnet" selected> TRENDnet
                    <option value="Foscam" selected> Foscam
                  </select>
                </td>
                <td align=left>
                  &nbsp;
                </td>
                <td align=left>
                  &nbsp;
                </td>
                <td align=left>
                  &nbsp;
                </td>
                <td align=left>
                  &nbsp;
                </td>
                <td align=center>
                  &nbsp;
                </td>
                <td align=right>
                  &nbsp;
                </td>
                <td align=right>
                  &nbsp;
                </td>
                <td align=center>
                  &nbsp;
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table> 
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

sub contacts 
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<title>AlertAway&#64;Home</title>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<center><h1>Alert Away</h1>
<table>
  <tr>
    <td valign=top>
    <tmpl_var name=menu>
    </td>
    <td colspan=100% align=center>      
      <table>
        <tr>
          <td colspan=100%>
            <table border=1>
              <tr>
                <th align=center colspan=100%>
                  <font color=green size=+1>Who to contact</font>
                </th>
              </tr>
              <tr>
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
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table> 
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

sub alarms 
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<title>AlertAway&#64;Home</title>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<center><h1>Alert Away</h1>
<table>
  <tr>
    <td valign=top>
    <tmpl_var name=menu>
    </td>
    <td colspan=100% align=center>
      
      <table>
        <tr>
          <td valign=top> 
            <table border=1>
              <tr>
                <th colspan=100% align=left>
                  <input type=submit name="state" value="Map alarm">
                  &nbsp;&nbsp;
                  <input type=submit name="state" value="Test alarm">
                  &nbsp;&nbsp;   
                  <font size=+1 color=green>Map Sensors to Alarms</font>  
                </th>
              </tr>
              <tr>
                <th>
                  Select a sensor
                </th>
                <th>
                  Select<br>one or more<br>alarms
                </th>
              </tr>
              <tr>
                <td>
                  <select name="SENSORTOALARM:sensor" size=15>            
                    <tmpl_loop name=sensors>
                      <option value="<tmpl_var name=addr_high>:<tmpl_var name=addr_low>:<tmpl_var name=port>"> <tmpl_var name=desc>             
                    </tmpl_loop>
                  </select>
                </td>
                <td>
                  <select name="SENSORTOALARM:alarm" size=15 multiple>
                    <tmpl_loop name=alarms>
                      <option value="<tmpl_var name=addr_high>:<tmpl_var name=addr_low>:<tmpl_var name=port>"> <tmpl_var name=desc> 
                    </tmpl_loop>
                    <option value="UnMapSensor"> UNMAP SENSOR
                  </select>
                </td>
              </tr>
              <tr>
                 <td colspan=100%>
                  <table border=1>
                    <tr>
                      <th colspan=100%>
						  Currently mapped
					  </th>
				    </tr>
				     <tr>
						<th>
						</th>
						<th>
						  Sensor
						</th>
						<th>
						  Alarm
						</th>
						<th>
						  Duration
						</th>
					  </tr>
					  <tmpl_loop name=mapped_alarms>
					  <tr>
						<td>
						  <input type=submit name="state" value="Set Duration:<tmpl_var name=rowid>">
						</td>
						<td>
						  <tmpl_var name=sensor_desc>
						</td>
						<td>
						  <tmpl_var name=alarm_desc>
						</td> 
						<td>
						  <select name="SENSORTOALARM:duration:<tmpl_var name=rowid>" size=1>
							<option value="<tmpl_var name=duration>"> <tmpl_var name=duration>
							<option value="SHORT"> SHORT
							<option value="5"> 5 seconds
							<option value="10"> 10 second
							<option value="30"> 30 seconds
							<option value="60"> 1 minute
							<option value="DEFAULT"> DEFAULT 
						  </select>
						</td>           
					  </tr>
                      </tmpl_loop>
                    </table>
                 </td>
              </tr>
            </table>
          </td>
          <td valign=top>
            <table border=1>
              <tr>
                <th colspan=100% align=left>
                  <input type=submit name="state" value="Map Contact">
                  &nbsp;&nbsp;&nbsp;&nbsp;   
                  <font size=+1 color=green>Map Sensors to Contacts</font>  
                </th>
              </tr>
              <tr>
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
                      <option value="<tmpl_var name=addr_high>:<tmpl_var name=addr_low>:<tmpl_var name=port>"> <tmpl_var name=desc>             
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
              <tr>
                <th colspan=100%>
                  Currently mapped
                </th>
              </tr>
              <tr>               
                <th>
                  Sensor
                </th>
                <th>
                  Contact
                </th>               
              </tr>
              <tmpl_loop name=mapped_contacts>
              <tr>
               
                <td>
                  <tmpl_var name=sensor_desc>
                </td>
                <td>
                  <tmpl_var name=contact>
                </td>            
              </tr>
              </tmpl_loop>
            </table>
          </td>
        </tr>
        <tr>
          <td valign=top align=center colspan=2>
            <table border=1>
              <tr>
                <th colspan=100% align=left>
                  <input type=submit name="state" value="Map Camera">
                  &nbsp;&nbsp;&nbsp;&nbsp;   
                  <font size=+1 color=green>Map Sensors to Cameras</font>  
                </th>
              </tr>
              <tr>
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
                      <option value="<tmpl_var name=addr_high>:<tmpl_var name=addr_low>:<tmpl_var name=port>"> <tmpl_var name=desc>             
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
              <tr>
                <th colspan=100%>
                  Currently mapped
                </th>
              </tr>
              <tr>
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
          </td>
          <td>
          </td>
      </table>      
    </td>
  </tr>
</table> 


  

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

sub configuration 
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<title>AlertAway&#64;Home</title>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<center><h1>Alert Away</h1>
<table>  
  <tr>
    <td align=top>
    <tmpl_var name=menu>
    </td>
    <td align=center>
      
      <table>
        <tr>                    
          <td valign=top>
            <table border=1>
              <tr>
                <th colspan=100% align=left>
                  <input type=submit name="state" value="Update Config"  
                  onClick="return confirm('If you do actions that change the IP address you will need to reboot');">
                  &nbsp;&nbsp;&nbsp;&nbsp;   
                  <font size=+1 color=green>Configuration values</font>
                  <tmpl_if name=display_reboot>
                    <input type=submit name="state" value="Reboot" onClick="return confirm('are you sure?');">
                  </tmpl_if>
                </th>    
              </tr>
              <tr>
              <font color=red><tmpl_var name=msg></font>
              </tr>
              <tr>
                <th colspan=2>
                    Identification
                </th>
                <td colspan=3>
                  <input name="CONFIG:ident" size=20 value="<tmpl_var name=currident>">
                </td>
              </tr>
              <tr>
                <th colspan=2>
                    Problem reporting frequency
                </th>
                <td colspan=3>
                  <input name="CONFIG:freq" size=6 value="<tmpl_var name=currfreq>">&nbsp;Minutes
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Primary contact
                </th>
                <td colspan=3>
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
                <th colspan=2>
                  Connection Type
                </th>
                <td colspan=3>
                  <select name=CONFIG:contype>
                    <tmpl_if name=currcontype>
                      <option value="<tmpl_var name=currcontype>"><tmpl_var name=currcontype>
                    </tmpl_if>            
                    <option value="DHCP">DHCP
                    <option value="STATIC IP">STATIC IP                    
                  </select>
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  External HTTP Server Port
                </th>
                <td colspan=3>
                  <input name="CONFIG:port" size=6 value="<tmpl_var name=currport>">                 
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Static IP address
                </th>
                <td colspan=3>
                  <input name="CONFIG:ip" size=16 value="<tmpl_var name=currip>"> 
                  <br><tmpl_var name=curripmsg>                
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Subnet Mask
                </th>
                <td colspan=3>
                  <input name="CONFIG:mask" size=16 value="<tmpl_var name=currmask>">
                  <br><tmpl_var name=currmaskmsg>                 
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Gateway
                </th>
                <td colspan=3>
                  <input name="CONFIG:gw" size=16 value="<tmpl_var name=currgw>"> 
                  <br><tmpl_var name=currgwmsg>                
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Domain Name Server 1
                </th>
                <td colspan=3>
                  <input name="CONFIG:dns1" size=16 value="<tmpl_var name=currdns1>">
                  <br><tmpl_var name=currdns1msg>                 
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Domain Name Server 2
                </th>
                <td colspan=3>
                  <input name="CONFIG:dns2" size=16 value="<tmpl_var name=currdns2>">
                  <br><tmpl_var name=currdns2msg>                 
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Metric Units
                </th>
                <td colspan=3>
                  <input type=checkbox name="CONFIG:metric_units" value=checked <tmpl_var name=currunits>>                 
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Trace
                </th>
                <td colspan=3>
                  <select name=CONFIG:trace onchange="return confirm('Trace change takes effect next restart')">                   
                    <option value="<tmpl_var name=currtrace>"><tmpl_var name=currtrace> (0=OFF, 1=ON)         
                    <option value="0">0=OFF
                    <option value="1">1=ON                                  
                  </select>                
                </td>
              </tr>
              <tr>
                <th colspan=2>
                  Print Trace
                </th>
                <td colspan=3>
                  <select name=CONFIG:printtrace onchange="return confirm('Causes trace output to also be printed to the console')">                   
                    <option value="<tmpl_var name=currprinttrace>"><tmpl_var name=currprinttrace> (0=OFF, 1=ON (prints to console))         
                    <option value="0">0=OFF
                    <option value="1">1=ON                                  
                  </select>                
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>      
    </td>
  </tr>
</table>

  

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

sub date 
{
my $stuff = <<EOF;
<html>
<tmpl_var name=form_action>
<title>AlertAway&#64;Home</title>
<font size=2 face="geneva, helvetica, sans serif">
<tmpl_loop name=hidden>
  <input type=hidden name="<tmpl_var name=name>" value="<tmpl_var name=value>">
</tmpl_loop>
<center><h1>Alert Away</h1>
<table>  
  <tr>  
  <td align=top>
    <tmpl_var name=menu>
  </td>
  <td align=top>
    <table border=1>
    <tr>  
    <td>
     &nbsp;
    </td>
    <th>
     DATE DAY-MONTH-YEAR
    </th>
    <th>
     TIME HH:MM (24 Hr format)
    <th>
  <tr>
      
      <td>
        <input type=submit name="state" value="Set Date/Time"> 
      </td>
      <td>
        <select name=day>            
        <option value="<tmpl_var name=day>"><tmpl_var name=day>                                      
        <option value="1">1
        <option value="2">2
        <option value="3">3
        <option value="4">4
        <option value="5">5
        <option value="6">6
        <option value="7">7
        <option value="8">8
        <option value="9">9
        <option value="10">10
        <option value="11">11
        <option value="12">12
        <option value="13">13
        <option value="14">14
        <option value="15">15
        <option value="16">16
        <option value="17">17
        <option value="18">18
        <option value="19">19
        <option value="20">20
        <option value="21">21
        <option value="22">22
        <option value="23">23
        <option value="24">24
        <option value="25">25
        <option value="26">26
        <option value="27">27
        <option value="28">28
        <option value="29">29
        <option value="30">30
        <option value="31">31                
        </select>
      -    
        <select name=month>            
        <option value="<tmpl_var name=month>"><tmpl_var name=month>                              
        <option value="Jan">Jan
        <option value="Feb">Feb
        <option value="Mar">Mar
        <option value="Apr">Apr
        <option value="May">May
        <option value="Jun">Jun
        <option value="Jul">Jul
        <option value="Aug">Aug
        <option value="Sep">Sep
        <option value="Nov">Nov
        <option value="Dec">Dec
        </select>
        -
        <select name=year>            
        <option value="<tmpl_var name=year>"><tmpl_var name=year>                              
        <option value="2011">2011
        <option value="2012">2012
        <option value="2013">2013
        <option value="2014">2014
        <option value="2015">2015
        </select>
      </td>
      <td>
        <select name=hour>            
        <option value="<tmpl_var name=hour>"><tmpl_var name=hour> 
        <option value="0">0                             
        <option value="1">1
        <option value="2">2
        <option value="3">3
        <option value="4">4
        <option value="5">5
        <option value="6">6
        <option value="7">7
        <option value="8">8
        <option value="9">9
        <option value="10">10
        <option value="11">11
        <option value="12">12
        <option value="13">13
        <option value="14">14
        <option value="15">15
        <option value="16">16
        <option value="17">17
        <option value="18">18
        <option value="19">19
        <option value="20">20
        <option value="21">21
        <option value="22">22
        <option value="23">23
        <option value="24">24
        </select>
        <select name=minute>            
        <option value="<tmpl_var name=minute>"><tmpl_var name=minute>
        <option value="0">00 
        <option value="1">01                             
        <option value="1">01
        <option value="2">02
        <option value="3">03
        <option value="4">04
        <option value="5">05
        <option value="6">06
        <option value="7">07
        <option value="8">08
        <option value="9">09
        <option value="10">10
        <option value="11">11
        <option value="12">12
        <option value="13">13
        <option value="14">14
        <option value="15">15
        <option value="16">16
        <option value="17">17
        <option value="18">18
        <option value="19">19
        <option value="20">20
        <option value="21">21                             
        <option value="21">21
        <option value="22">22
        <option value="23">23
        <option value="24">24
        <option value="25">25
        <option value="26">6
        <option value="27">27
        <option value="28">28
        <option value="29">29
        <option value="30">30                           
        <option value="31">31
        <option value="32">32
        <option value="33">33
        <option value="34">34
        <option value="35">35
        <option value="36">36
        <option value="37">37
        <option value="38">38
        <option value="39">39
        <option value="40">40                           
        <option value="41">41
        <option value="42">42
        <option value="43">43
        <option value="44">44
        <option value="45">45
        <option value="46">46
        <option value="47">47
        <option value="48">48
        <option value="49">49
        <option value="50">50                         
        <option value="51">51
        <option value="52">52
        <option value="53">53
        <option value="54">54
        <option value="55">55
        <option value="56">56
        <option value="57">57
        <option value="58">58
        <option value="59">59
        </select>
      </td>    
    </tr>
    <tr>
      <td colspan=2 halign=left>
       Time Zone:&nbsp
       

    <select name="timezone" id="timezone">
    <option value="<tmpl_var name=timezone>"><tmpl_var name=timezone>
    <option value="America/Atka">(GMT-10:00) America/Atka (Hawaii-Aleutian Standard Time)</option>
    <option value="America/Anchorage">(GMT-9:00) America/Anchorage (Alaska Standard Time)</option>
    <option value="America/Juneau">(GMT-9:00) America/Juneau (Alaska Standard Time)</option>
    <option value="America/Nome">(GMT-9:00) America/Nome (Alaska Standard Time)</option>
    <option value="America/Yakutat">(GMT-9:00) America/Yakutat (Alaska Standard Time)</option>
    <option value="America/Dawson">(GMT-8:00) America/Dawson (Pacific Standard Time)</option>
    <option value="America/Ensenada">(GMT-8:00) America/Ensenada (Pacific Standard Time)</option>
    <option value="America/Los_Angeles">(GMT-8:00) America/Los_Angeles (Pacific Standard Time)</option>
    <option value="America/Tijuana">(GMT-8:00) America/Tijuana (Pacific Standard Time)</option>
    <option value="America/Vancouver">(GMT-8:00) America/Vancouver (Pacific Standard Time)</option>
    <option value="America/Whitehorse">(GMT-8:00) America/Whitehorse (Pacific Standard Time)</option>
    <option value="Canada/Pacific">(GMT-8:00) Canada/Pacific (Pacific Standard Time)</option>
    <option value="Canada/Yukon">(GMT-8:00) Canada/Yukon (Pacific Standard Time)</option>
    <option value="Mexico/BajaNorte">(GMT-8:00) Mexico/BajaNorte (Pacific Standard Time)</option>
    <option value="America/Boise">(GMT-7:00) America/Boise (Mountain Standard Time)</option>
    <option value="America/Cambridge_Bay">(GMT-7:00) America/Cambridge_Bay (Mountain Standard Time)</option>
    <option value="America/Chihuahua">(GMT-7:00) America/Chihuahua (Mountain Standard Time)</option>
    <option value="America/Dawson_Creek">(GMT-7:00) America/Dawson_Creek (Mountain Standard Time)</option>
    <option value="America/Denver">(GMT-7:00) America/Denver (Mountain Standard Time)</option>
    <option value="America/Edmonton">(GMT-7:00) America/Edmonton (Mountain Standard Time)</option>
    <option value="America/Hermosillo">(GMT-7:00) America/Hermosillo (Mountain Standard Time)</option>
    <option value="America/Inuvik">(GMT-7:00) America/Inuvik (Mountain Standard Time)</option>
    <option value="America/Mazatlan">(GMT-7:00) America/Mazatlan (Mountain Standard Time)</option>
    <option value="America/Phoenix">(GMT-7:00) America/Phoenix (Mountain Standard Time)</option>
    <option value="America/Shiprock">(GMT-7:00) America/Shiprock (Mountain Standard Time)</option>
    <option value="America/Yellowknife">(GMT-7:00) America/Yellowknife (Mountain Standard Time)</option>
    <option value="Canada/Mountain">(GMT-7:00) Canada/Mountain (Mountain Standard Time)</option>
    <option value="Mexico/BajaSur">(GMT-7:00) Mexico/BajaSur (Mountain Standard Time)</option>
    <option value="America/Belize">(GMT-6:00) America/Belize (Central Standard Time)</option>
    <option value="America/Cancun">(GMT-6:00) America/Cancun (Central Standard Time)</option>
    <option value="America/Chicago">(GMT-6:00) America/Chicago (Central Standard Time)</option>
    <option value="America/Costa_Rica">(GMT-6:00) America/Costa_Rica (Central Standard Time)</option>
    <option value="America/El_Salvador">(GMT-6:00) America/El_Salvador (Central Standard Time)</option>
    <option value="America/Guatemala">(GMT-6:00) America/Guatemala (Central Standard Time)</option>
    <option value="America/Knox_IN">(GMT-6:00) America/Knox_IN (Central Standard Time)</option>
    <option value="America/Managua">(GMT-6:00) America/Managua (Central Standard Time)</option>
    <option value="America/Menominee">(GMT-6:00) America/Menominee (Central Standard Time)</option>
    <option value="America/Merida">(GMT-6:00) America/Merida (Central Standard Time)</option>
    <option value="America/Mexico_City">(GMT-6:00) America/Mexico_City (Central Standard Time)</option>
    <option value="America/Monterrey">(GMT-6:00) America/Monterrey (Central Standard Time)</option>
    <option value="America/Rainy_River">(GMT-6:00) America/Rainy_River (Central Standard Time)</option>
    <option value="America/Rankin_Inlet">(GMT-6:00) America/Rankin_Inlet (Central Standard Time)</option>
    <option value="America/Regina">(GMT-6:00) America/Regina (Central Standard Time)</option>
    <option value="America/Swift_Current">(GMT-6:00) America/Swift_Current (Central Standard Time)</option>
    <option value="America/Tegucigalpa">(GMT-6:00) America/Tegucigalpa (Central Standard Time)</option>
    <option value="America/Winnipeg">(GMT-6:00) America/Winnipeg (Central Standard Time)</option>
    <option value="Canada/Central">(GMT-6:00) Canada/Central (Central Standard Time)</option>
    <option value="Canada/East-Saskatchewan">(GMT-6:00) Canada/East-Saskatchewan (Central Standard Time)</option>
    <option value="Canada/Saskatchewan">(GMT-6:00) Canada/Saskatchewan (Central Standard Time)</option>
    <option value="Chile/EasterIsland">(GMT-6:00) Chile/EasterIsland (Easter Is. Time)</option>
    <option value="Mexico/General">(GMT-6:00) Mexico/General (Central Standard Time)</option>
    <option value="America/Atikokan">(GMT-5:00) America/Atikokan (Eastern Standard Time)</option>
    <option value="America/Bogota">(GMT-5:00) America/Bogota (Colombia Time)</option>
    <option value="America/Cayman">(GMT-5:00) America/Cayman (Eastern Standard Time)</option>
    <option value="America/Coral_Harbour">(GMT-5:00) America/Coral_Harbour (Eastern Standard Time)</option>
    <option value="America/Detroit">(GMT-5:00) America/Detroit (Eastern Standard Time)</option>
    <option value="America/Fort_Wayne">(GMT-5:00) America/Fort_Wayne (Eastern Standard Time)</option>
    <option value="America/Grand_Turk">(GMT-5:00) America/Grand_Turk (Eastern Standard Time)</option>
    <option value="America/Guayaquil">(GMT-5:00) America/Guayaquil (Ecuador Time)</option>
    <option value="America/Havana">(GMT-5:00) America/Havana (Cuba Standard Time)</option>
    <option value="America/Indianapolis">(GMT-5:00) America/Indianapolis (Eastern Standard Time)</option>
    <option value="America/Iqaluit">(GMT-5:00) America/Iqaluit (Eastern Standard Time)</option>
    <option value="America/Jamaica">(GMT-5:00) America/Jamaica (Eastern Standard Time)</option>
    <option value="America/Lima">(GMT-5:00) America/Lima (Peru Time)</option>
    <option value="America/Louisville">(GMT-5:00) America/Louisville (Eastern Standard Time)</option>
    <option value="America/Montreal">(GMT-5:00) America/Montreal (Eastern Standard Time)</option>
    <option value="America/Nassau">(GMT-5:00) America/Nassau (Eastern Standard Time)</option>
    <option value="America/New_York">(GMT-5:00) America/New_York (Eastern Standard Time)</option>
    <option value="America/Nipigon">(GMT-5:00) America/Nipigon (Eastern Standard Time)</option>
    <option value="America/Panama">(GMT-5:00) America/Panama (Eastern Standard Time)</option>
    <option value="America/Pangnirtung">(GMT-5:00) America/Pangnirtung (Eastern Standard Time)</option>
    <option value="America/Port-au-Prince">(GMT-5:00) America/Port-au-Prince (Eastern Standard Time)</option>
    <option value="America/Resolute">(GMT-5:00) America/Resolute (Eastern Standard Time)</option>
    <option value="America/Thunder_Bay">(GMT-5:00) America/Thunder_Bay (Eastern Standard Time)</option>
    <option value="America/Toronto">(GMT-5:00) America/Toronto (Eastern Standard Time)</option>
    <option value="Canada/Eastern">(GMT-5:00) Canada/Eastern (Eastern Standard Time)</option>
    <option value="America/Caracas">(GMT-4:-30) America/Caracas (Venezuela Time)</option>
    <option value="America/Anguilla">(GMT-4:00) America/Anguilla (Atlantic Standard Time)</option>
    <option value="America/Antigua">(GMT-4:00) America/Antigua (Atlantic Standard Time)</option>
    <option value="America/Aruba">(GMT-4:00) America/Aruba (Atlantic Standard Time)</option>
    <option value="America/Asuncion">(GMT-4:00) America/Asuncion (Paraguay Time)</option>
    <option value="America/Barbados">(GMT-4:00) America/Barbados (Atlantic Standard Time)</option>
    <option value="America/Blanc-Sablon">(GMT-4:00) America/Blanc-Sablon (Atlantic Standard Time)</option>
    <option value="America/Boa_Vista">(GMT-4:00) America/Boa_Vista (Amazon Time)</option>
    <option value="America/Campo_Grande">(GMT-4:00) America/Campo_Grande (Amazon Time)</option>
    <option value="America/Cuiaba">(GMT-4:00) America/Cuiaba (Amazon Time)</option>
    <option value="America/Curacao">(GMT-4:00) America/Curacao (Atlantic Standard Time)</option>
    <option value="America/Dominica">(GMT-4:00) America/Dominica (Atlantic Standard Time)</option>
    <option value="America/Eirunepe">(GMT-4:00) America/Eirunepe (Amazon Time)</option>
    <option value="America/Glace_Bay">(GMT-4:00) America/Glace_Bay (Atlantic Standard Time)</option>
    <option value="America/Goose_Bay">(GMT-4:00) America/Goose_Bay (Atlantic Standard Time)</option>
    <option value="America/Grenada">(GMT-4:00) America/Grenada (Atlantic Standard Time)</option>
    <option value="America/Guadeloupe">(GMT-4:00) America/Guadeloupe (Atlantic Standard Time)</option>
    <option value="America/Guyana">(GMT-4:00) America/Guyana (Guyana Time)</option>
    <option value="America/Halifax">(GMT-4:00) America/Halifax (Atlantic Standard Time)</option>
    <option value="America/La_Paz">(GMT-4:00) America/La_Paz (Bolivia Time)</option>
    <option value="America/Manaus">(GMT-4:00) America/Manaus (Amazon Time)</option>
    <option value="America/Marigot">(GMT-4:00) America/Marigot (Atlantic Standard Time)</option>
    <option value="America/Martinique">(GMT-4:00) America/Martinique (Atlantic Standard Time)</option>
    <option value="America/Moncton">(GMT-4:00) America/Moncton (Atlantic Standard Time)</option>
    <option value="America/Montserrat">(GMT-4:00) America/Montserrat (Atlantic Standard Time)</option>
    <option value="America/Port_of_Spain">(GMT-4:00) America/Port_of_Spain (Atlantic Standard Time)</option>
    <option value="America/Porto_Acre">(GMT-4:00) America/Porto_Acre (Amazon Time)</option>
    <option value="America/Porto_Velho">(GMT-4:00) America/Porto_Velho (Amazon Time)</option>
    <option value="America/Puerto_Rico">(GMT-4:00) America/Puerto_Rico (Atlantic Standard Time)</option>
    <option value="America/Rio_Branco">(GMT-4:00) America/Rio_Branco (Amazon Time)</option>
    <option value="America/Santiago">(GMT-4:00) America/Santiago (Chile Time)</option>
    <option value="America/Santo_Domingo">(GMT-4:00) America/Santo_Domingo (Atlantic Standard Time)</option>
    <option value="America/St_Barthelemy">(GMT-4:00) America/St_Barthelemy (Atlantic Standard Time)</option>
    <option value="America/St_Kitts">(GMT-4:00) America/St_Kitts (Atlantic Standard Time)</option>
    <option value="America/St_Lucia">(GMT-4:00) America/St_Lucia (Atlantic Standard Time)</option>
    <option value="America/St_Thomas">(GMT-4:00) America/St_Thomas (Atlantic Standard Time)</option>
    <option value="America/St_Vincent">(GMT-4:00) America/St_Vincent (Atlantic Standard Time)</option>
    <option value="America/Thule">(GMT-4:00) America/Thule (Atlantic Standard Time)</option>
    <option value="America/Tortola">(GMT-4:00) America/Tortola (Atlantic Standard Time)</option>
    <option value="America/Virgin">(GMT-4:00) America/Virgin (Atlantic Standard Time)</option>
    <option value="Antarctica/Palmer">(GMT-4:00) Antarctica/Palmer (Chile Time)</option>
    <option value="Atlantic/Bermuda">(GMT-4:00) Atlantic/Bermuda (Atlantic Standard Time)</option>
    <option value="Atlantic/Stanley">(GMT-4:00) Atlantic/Stanley (Falkland Is. Time)</option>
    <option value="Brazil/Acre">(GMT-4:00) Brazil/Acre (Amazon Time)</option>
    <option value="Brazil/West">(GMT-4:00) Brazil/West (Amazon Time)</option>
    <option value="Canada/Atlantic">(GMT-4:00) Canada/Atlantic (Atlantic Standard Time)</option>
    <option value="Chile/Continental">(GMT-4:00) Chile/Continental (Chile Time)</option>
    <option value="America/St_Johns">(GMT-3:-30) America/St_Johns (Newfoundland Standard Time)</option>
    <option value="Canada/Newfoundland">(GMT-3:-30) Canada/Newfoundland (Newfoundland Standard Time)</option>
    <option value="America/Araguaina">(GMT-3:00) America/Araguaina (Brasilia Time)</option>
    <option value="America/Bahia">(GMT-3:00) America/Bahia (Brasilia Time)</option>
    <option value="America/Belem">(GMT-3:00) America/Belem (Brasilia Time)</option>
    <option value="America/Buenos_Aires">(GMT-3:00) America/Buenos_Aires (Argentine Time)</option>
    <option value="America/Catamarca">(GMT-3:00) America/Catamarca (Argentine Time)</option>
    <option value="America/Cayenne">(GMT-3:00) America/Cayenne (French Guiana Time)</option>
    <option value="America/Cordoba">(GMT-3:00) America/Cordoba (Argentine Time)</option>
    <option value="America/Fortaleza">(GMT-3:00) America/Fortaleza (Brasilia Time)</option>
    <option value="America/Godthab">(GMT-3:00) America/Godthab (Western Greenland Time)</option>
    <option value="America/Jujuy">(GMT-3:00) America/Jujuy (Argentine Time)</option>
    <option value="America/Maceio">(GMT-3:00) America/Maceio (Brasilia Time)</option>
    <option value="America/Mendoza">(GMT-3:00) America/Mendoza (Argentine Time)</option>
    <option value="America/Miquelon">(GMT-3:00) America/Miquelon (Pierre & Miquelon Standard Time)</option>
    <option value="America/Montevideo">(GMT-3:00) America/Montevideo (Uruguay Time)</option>
    <option value="America/Paramaribo">(GMT-3:00) America/Paramaribo (Suriname Time)</option>
    <option value="America/Recife">(GMT-3:00) America/Recife (Brasilia Time)</option>
    <option value="America/Rosario">(GMT-3:00) America/Rosario (Argentine Time)</option>
    <option value="America/Santarem">(GMT-3:00) America/Santarem (Brasilia Time)</option>
    <option value="America/Sao_Paulo">(GMT-3:00) America/Sao_Paulo (Brasilia Time)</option>
    <option value="Antarctica/Rothera">(GMT-3:00) Antarctica/Rothera (Rothera Time)</option>
    <option value="Brazil/East">(GMT-3:00) Brazil/East (Brasilia Time)</option>
    <option value="America/Noronha">(GMT-2:00) America/Noronha (Fernando de Noronha Time)</option>
    <option value="Atlantic/South_Georgia">(GMT-2:00) Atlantic/South_Georgia (South Georgia Standard Time)</option>
    <option value="Brazil/DeNoronha">(GMT-2:00) Brazil/DeNoronha (Fernando de Noronha Time)</option>
    <option value="America/Scoresbysund">(GMT-1:00) America/Scoresbysund (Eastern Greenland Time)</option>
    <option value="Atlantic/Azores">(GMT-1:00) Atlantic/Azores (Azores Time)</option>
    <option value="Atlantic/Cape_Verde">(GMT-1:00) Atlantic/Cape_Verde (Cape Verde Time)</option>
    <option value="Africa/Abidjan">(GMT+0:00) Africa/Abidjan (Greenwich Mean Time)</option>
    <option value="Africa/Accra">(GMT+0:00) Africa/Accra (Ghana Mean Time)</option>
    <option value="Africa/Bamako">(GMT+0:00) Africa/Bamako (Greenwich Mean Time)</option>
    <option value="Africa/Banjul">(GMT+0:00) Africa/Banjul (Greenwich Mean Time)</option>
    <option value="Africa/Bissau">(GMT+0:00) Africa/Bissau (Greenwich Mean Time)</option>
    <option value="Africa/Casablanca">(GMT+0:00) Africa/Casablanca (Western European Time)</option>
    <option value="Africa/Conakry">(GMT+0:00) Africa/Conakry (Greenwich Mean Time)</option>
    <option value="Africa/Dakar">(GMT+0:00) Africa/Dakar (Greenwich Mean Time)</option>
    <option value="Africa/El_Aaiun">(GMT+0:00) Africa/El_Aaiun (Western European Time)</option>
    <option value="Africa/Freetown">(GMT+0:00) Africa/Freetown (Greenwich Mean Time)</option>
    <option value="Africa/Lome">(GMT+0:00) Africa/Lome (Greenwich Mean Time)</option>
    <option value="Africa/Monrovia">(GMT+0:00) Africa/Monrovia (Greenwich Mean Time)</option>
    <option value="Africa/Nouakchott">(GMT+0:00) Africa/Nouakchott (Greenwich Mean Time)</option>
    <option value="Africa/Ouagadougou">(GMT+0:00) Africa/Ouagadougou (Greenwich Mean Time)</option>
    <option value="Africa/Sao_Tome">(GMT+0:00) Africa/Sao_Tome (Greenwich Mean Time)</option>
    <option value="Africa/Timbuktu">(GMT+0:00) Africa/Timbuktu (Greenwich Mean Time)</option>
    <option value="America/Danmarkshavn">(GMT+0:00) America/Danmarkshavn (Greenwich Mean Time)</option>
    <option value="Atlantic/Canary">(GMT+0:00) Atlantic/Canary (Western European Time)</option>
    <option value="Atlantic/Faeroe">(GMT+0:00) Atlantic/Faeroe (Western European Time)</option>
    <option value="Atlantic/Faroe">(GMT+0:00) Atlantic/Faroe (Western European Time)</option>
    <option value="Atlantic/Madeira">(GMT+0:00) Atlantic/Madeira (Western European Time)</option>
    <option value="Atlantic/Reykjavik">(GMT+0:00) Atlantic/Reykjavik (Greenwich Mean Time)</option>
    <option value="Atlantic/St_Helena">(GMT+0:00) Atlantic/St_Helena (Greenwich Mean Time)</option>
    <option value="Europe/Belfast">(GMT+0:00) Europe/Belfast (Greenwich Mean Time)</option>
    <option value="Europe/Dublin">(GMT+0:00) Europe/Dublin (Greenwich Mean Time)</option>
    <option value="Europe/Guernsey">(GMT+0:00) Europe/Guernsey (Greenwich Mean Time)</option>
    <option value="Europe/Isle_of_Man">(GMT+0:00) Europe/Isle_of_Man (Greenwich Mean Time)</option>
    <option value="Europe/Jersey">(GMT+0:00) Europe/Jersey (Greenwich Mean Time)</option>
    <option value="Europe/Lisbon">(GMT+0:00) Europe/Lisbon (Western European Time)</option>
    <option value="Europe/London">(GMT+0:00) Europe/London (Greenwich Mean Time)</option>
    <option value="Africa/Algiers">(GMT+1:00) Africa/Algiers (Central European Time)</option>
    <option value="Africa/Bangui">(GMT+1:00) Africa/Bangui (Western African Time)</option>
    <option value="Africa/Brazzaville">(GMT+1:00) Africa/Brazzaville (Western African Time)</option>
    <option value="Africa/Ceuta">(GMT+1:00) Africa/Ceuta (Central European Time)</option>
    <option value="Africa/Douala">(GMT+1:00) Africa/Douala (Western African Time)</option>
    <option value="Africa/Kinshasa">(GMT+1:00) Africa/Kinshasa (Western African Time)</option>
    <option value="Africa/Lagos">(GMT+1:00) Africa/Lagos (Western African Time)</option>
    <option value="Africa/Libreville">(GMT+1:00) Africa/Libreville (Western African Time)</option>
    <option value="Africa/Luanda">(GMT+1:00) Africa/Luanda (Western African Time)</option>
    <option value="Africa/Malabo">(GMT+1:00) Africa/Malabo (Western African Time)</option>
    <option value="Africa/Ndjamena">(GMT+1:00) Africa/Ndjamena (Western African Time)</option>
    <option value="Africa/Niamey">(GMT+1:00) Africa/Niamey (Western African Time)</option>
    <option value="Africa/Porto-Novo">(GMT+1:00) Africa/Porto-Novo (Western African Time)</option>
    <option value="Africa/Tunis">(GMT+1:00) Africa/Tunis (Central European Time)</option>
    <option value="Africa/Windhoek">(GMT+1:00) Africa/Windhoek (Western African Time)</option>
    <option value="Arctic/Longyearbyen">(GMT+1:00) Arctic/Longyearbyen (Central European Time)</option>
    <option value="Atlantic/Jan_Mayen">(GMT+1:00) Atlantic/Jan_Mayen (Central European Time)</option>
    <option value="Europe/Amsterdam">(GMT+1:00) Europe/Amsterdam (Central European Time)</option>
    <option value="Europe/Andorra">(GMT+1:00) Europe/Andorra (Central European Time)</option>
    <option value="Europe/Belgrade">(GMT+1:00) Europe/Belgrade (Central European Time)</option>
    <option value="Europe/Berlin">(GMT+1:00) Europe/Berlin (Central European Time)</option>
    <option value="Europe/Bratislava">(GMT+1:00) Europe/Bratislava (Central European Time)</option>
    <option value="Europe/Brussels">(GMT+1:00) Europe/Brussels (Central European Time)</option>
    <option value="Europe/Budapest">(GMT+1:00) Europe/Budapest (Central European Time)</option>
    <option value="Europe/Copenhagen">(GMT+1:00) Europe/Copenhagen (Central European Time)</option>
    <option value="Europe/Gibraltar">(GMT+1:00) Europe/Gibraltar (Central European Time)</option>
    <option value="Europe/Ljubljana">(GMT+1:00) Europe/Ljubljana (Central European Time)</option>
    <option value="Europe/Luxembourg">(GMT+1:00) Europe/Luxembourg (Central European Time)</option>
    <option value="Europe/Madrid">(GMT+1:00) Europe/Madrid (Central European Time)</option>
    <option value="Europe/Malta">(GMT+1:00) Europe/Malta (Central European Time)</option>
    <option value="Europe/Monaco">(GMT+1:00) Europe/Monaco (Central European Time)</option>
    <option value="Europe/Oslo">(GMT+1:00) Europe/Oslo (Central European Time)</option>
    <option value="Europe/Paris">(GMT+1:00) Europe/Paris (Central European Time)</option>
    <option value="Europe/Podgorica">(GMT+1:00) Europe/Podgorica (Central European Time)</option>
    <option value="Europe/Prague">(GMT+1:00) Europe/Prague (Central European Time)</option>
    <option value="Europe/Rome">(GMT+1:00) Europe/Rome (Central European Time)</option>
    <option value="Europe/San_Marino">(GMT+1:00) Europe/San_Marino (Central European Time)</option>
    <option value="Europe/Sarajevo">(GMT+1:00) Europe/Sarajevo (Central European Time)</option>
    <option value="Europe/Skopje">(GMT+1:00) Europe/Skopje (Central European Time)</option>
    <option value="Europe/Stockholm">(GMT+1:00) Europe/Stockholm (Central European Time)</option>
    <option value="Europe/Tirane">(GMT+1:00) Europe/Tirane (Central European Time)</option>
    <option value="Europe/Vaduz">(GMT+1:00) Europe/Vaduz (Central European Time)</option>
    <option value="Europe/Vatican">(GMT+1:00) Europe/Vatican (Central European Time)</option>
    <option value="Europe/Vienna">(GMT+1:00) Europe/Vienna (Central European Time)</option>
    <option value="Europe/Warsaw">(GMT+1:00) Europe/Warsaw (Central European Time)</option>
    <option value="Europe/Zagreb">(GMT+1:00) Europe/Zagreb (Central European Time)</option>
    <option value="Europe/Zurich">(GMT+1:00) Europe/Zurich (Central European Time)</option>
    <option value="Africa/Blantyre">(GMT+2:00) Africa/Blantyre (Central African Time)</option>
    <option value="Africa/Bujumbura">(GMT+2:00) Africa/Bujumbura (Central African Time)</option>
    <option value="Africa/Cairo">(GMT+2:00) Africa/Cairo (Eastern European Time)</option>
    <option value="Africa/Gaborone">(GMT+2:00) Africa/Gaborone (Central African Time)</option>
    <option value="Africa/Harare">(GMT+2:00) Africa/Harare (Central African Time)</option>
    <option value="Africa/Johannesburg">(GMT+2:00) Africa/Johannesburg (South Africa Standard Time)</option>
    <option value="Africa/Kigali">(GMT+2:00) Africa/Kigali (Central African Time)</option>
    <option value="Africa/Lubumbashi">(GMT+2:00) Africa/Lubumbashi (Central African Time)</option>
    <option value="Africa/Lusaka">(GMT+2:00) Africa/Lusaka (Central African Time)</option>
    <option value="Africa/Maputo">(GMT+2:00) Africa/Maputo (Central African Time)</option>
    <option value="Africa/Maseru">(GMT+2:00) Africa/Maseru (South Africa Standard Time)</option>
    <option value="Africa/Mbabane">(GMT+2:00) Africa/Mbabane (South Africa Standard Time)</option>
    <option value="Africa/Tripoli">(GMT+2:00) Africa/Tripoli (Eastern European Time)</option>
    <option value="Asia/Amman">(GMT+2:00) Asia/Amman (Eastern European Time)</option>
    <option value="Asia/Beirut">(GMT+2:00) Asia/Beirut (Eastern European Time)</option>
    <option value="Asia/Damascus">(GMT+2:00) Asia/Damascus (Eastern European Time)</option>
    <option value="Asia/Gaza">(GMT+2:00) Asia/Gaza (Eastern European Time)</option>
    <option value="Asia/Istanbul">(GMT+2:00) Asia/Istanbul (Eastern European Time)</option>
    <option value="Asia/Jerusalem">(GMT+2:00) Asia/Jerusalem (Israel Standard Time)</option>
    <option value="Asia/Nicosia">(GMT+2:00) Asia/Nicosia (Eastern European Time)</option>
    <option value="Asia/Tel_Aviv">(GMT+2:00) Asia/Tel_Aviv (Israel Standard Time)</option>
    <option value="Europe/Athens">(GMT+2:00) Europe/Athens (Eastern European Time)</option>
    <option value="Europe/Bucharest">(GMT+2:00) Europe/Bucharest (Eastern European Time)</option>
    <option value="Europe/Chisinau">(GMT+2:00) Europe/Chisinau (Eastern European Time)</option>
    <option value="Europe/Helsinki">(GMT+2:00) Europe/Helsinki (Eastern European Time)</option>
    <option value="Europe/Istanbul">(GMT+2:00) Europe/Istanbul (Eastern European Time)</option>
    <option value="Europe/Kaliningrad">(GMT+2:00) Europe/Kaliningrad (Eastern European Time)</option>
    <option value="Europe/Kiev">(GMT+2:00) Europe/Kiev (Eastern European Time)</option>
    <option value="Europe/Mariehamn">(GMT+2:00) Europe/Mariehamn (Eastern European Time)</option>
    <option value="Europe/Minsk">(GMT+2:00) Europe/Minsk (Eastern European Time)</option>
    <option value="Europe/Nicosia">(GMT+2:00) Europe/Nicosia (Eastern European Time)</option>
    <option value="Europe/Riga">(GMT+2:00) Europe/Riga (Eastern European Time)</option>
    <option value="Europe/Simferopol">(GMT+2:00) Europe/Simferopol (Eastern European Time)</option>
    <option value="Europe/Sofia">(GMT+2:00) Europe/Sofia (Eastern European Time)</option>
    <option value="Europe/Tallinn">(GMT+2:00) Europe/Tallinn (Eastern European Time)</option>
    <option value="Europe/Tiraspol">(GMT+2:00) Europe/Tiraspol (Eastern European Time)</option>
    <option value="Europe/Uzhgorod">(GMT+2:00) Europe/Uzhgorod (Eastern European Time)</option>
    <option value="Europe/Vilnius">(GMT+2:00) Europe/Vilnius (Eastern European Time)</option>
    <option value="Europe/Zaporozhye">(GMT+2:00) Europe/Zaporozhye (Eastern European Time)</option>
    <option value="Africa/Addis_Ababa">(GMT+3:00) Africa/Addis_Ababa (Eastern African Time)</option>
    <option value="Africa/Asmara">(GMT+3:00) Africa/Asmara (Eastern African Time)</option>
    <option value="Africa/Asmera">(GMT+3:00) Africa/Asmera (Eastern African Time)</option>
    <option value="Africa/Dar_es_Salaam">(GMT+3:00) Africa/Dar_es_Salaam (Eastern African Time)</option>
    <option value="Africa/Djibouti">(GMT+3:00) Africa/Djibouti (Eastern African Time)</option>
    <option value="Africa/Kampala">(GMT+3:00) Africa/Kampala (Eastern African Time)</option>
    <option value="Africa/Khartoum">(GMT+3:00) Africa/Khartoum (Eastern African Time)</option>
    <option value="Africa/Mogadishu">(GMT+3:00) Africa/Mogadishu (Eastern African Time)</option>
    <option value="Africa/Nairobi">(GMT+3:00) Africa/Nairobi (Eastern African Time)</option>
    <option value="Antarctica/Syowa">(GMT+3:00) Antarctica/Syowa (Syowa Time)</option>
    <option value="Asia/Aden">(GMT+3:00) Asia/Aden (Arabia Standard Time)</option>
    <option value="Asia/Baghdad">(GMT+3:00) Asia/Baghdad (Arabia Standard Time)</option>
    <option value="Asia/Bahrain">(GMT+3:00) Asia/Bahrain (Arabia Standard Time)</option>
    <option value="Asia/Kuwait">(GMT+3:00) Asia/Kuwait (Arabia Standard Time)</option>
    <option value="Asia/Qatar">(GMT+3:00) Asia/Qatar (Arabia Standard Time)</option>
    <option value="Europe/Moscow">(GMT+3:00) Europe/Moscow (Moscow Standard Time)</option>
    <option value="Europe/Volgograd">(GMT+3:00) Europe/Volgograd (Volgograd Time)</option>
    <option value="Indian/Antananarivo">(GMT+3:00) Indian/Antananarivo (Eastern African Time)</option>
    <option value="Indian/Comoro">(GMT+3:00) Indian/Comoro (Eastern African Time)</option>
    <option value="Indian/Mayotte">(GMT+3:00) Indian/Mayotte (Eastern African Time)</option>
    <option value="Asia/Tehran">(GMT+3:30) Asia/Tehran (Iran Standard Time)</option>
    <option value="Asia/Baku">(GMT+4:00) Asia/Baku (Azerbaijan Time)</option>
    <option value="Asia/Dubai">(GMT+4:00) Asia/Dubai (Gulf Standard Time)</option>
    <option value="Asia/Muscat">(GMT+4:00) Asia/Muscat (Gulf Standard Time)</option>
    <option value="Asia/Tbilisi">(GMT+4:00) Asia/Tbilisi (Georgia Time)</option>
    <option value="Asia/Yerevan">(GMT+4:00) Asia/Yerevan (Armenia Time)</option>
    <option value="Europe/Samara">(GMT+4:00) Europe/Samara (Samara Time)</option>
    <option value="Indian/Mahe">(GMT+4:00) Indian/Mahe (Seychelles Time)</option>
    <option value="Indian/Mauritius">(GMT+4:00) Indian/Mauritius (Mauritius Time)</option>
    <option value="Indian/Reunion">(GMT+4:00) Indian/Reunion (Reunion Time)</option>
    <option value="Asia/Kabul">(GMT+4:30) Asia/Kabul (Afghanistan Time)</option>
    <option value="Asia/Aqtau">(GMT+5:00) Asia/Aqtau (Aqtau Time)</option>
    <option value="Asia/Aqtobe">(GMT+5:00) Asia/Aqtobe (Aqtobe Time)</option>
    <option value="Asia/Ashgabat">(GMT+5:00) Asia/Ashgabat (Turkmenistan Time)</option>
    <option value="Asia/Ashkhabad">(GMT+5:00) Asia/Ashkhabad (Turkmenistan Time)</option>
    <option value="Asia/Dushanbe">(GMT+5:00) Asia/Dushanbe (Tajikistan Time)</option>
    <option value="Asia/Karachi">(GMT+5:00) Asia/Karachi (Pakistan Time)</option>
    <option value="Asia/Oral">(GMT+5:00) Asia/Oral (Oral Time)</option>
    <option value="Asia/Samarkand">(GMT+5:00) Asia/Samarkand (Uzbekistan Time)</option>
    <option value="Asia/Tashkent">(GMT+5:00) Asia/Tashkent (Uzbekistan Time)</option>
    <option value="Asia/Yekaterinburg">(GMT+5:00) Asia/Yekaterinburg (Yekaterinburg Time)</option>
    <option value="Indian/Kerguelen">(GMT+5:00) Indian/Kerguelen (French Southern & Antarctic Lands Time)</option>
    <option value="Indian/Maldives">(GMT+5:00) Indian/Maldives (Maldives Time)</option>
    <option value="Asia/Calcutta">(GMT+5:30) Asia/Calcutta (India Standard Time)</option>
    <option value="Asia/Colombo">(GMT+5:30) Asia/Colombo (India Standard Time)</option>
    <option value="Asia/Kolkata">(GMT+5:30) Asia/Kolkata (India Standard Time)</option>
    <option value="Asia/Katmandu">(GMT+5:45) Asia/Katmandu (Nepal Time)</option>
    <option value="Antarctica/Mawson">(GMT+6:00) Antarctica/Mawson (Mawson Time)</option>
    <option value="Antarctica/Vostok">(GMT+6:00) Antarctica/Vostok (Vostok Time)</option>
    <option value="Asia/Almaty">(GMT+6:00) Asia/Almaty (Alma-Ata Time)</option>
    <option value="Asia/Bishkek">(GMT+6:00) Asia/Bishkek (Kirgizstan Time)</option>
    <option value="Asia/Dacca">(GMT+6:00) Asia/Dacca (Bangladesh Time)</option>
    <option value="Asia/Dhaka">(GMT+6:00) Asia/Dhaka (Bangladesh Time)</option>
    <option value="Asia/Novosibirsk">(GMT+6:00) Asia/Novosibirsk (Novosibirsk Time)</option>
    <option value="Asia/Omsk">(GMT+6:00) Asia/Omsk (Omsk Time)</option>
    <option value="Asia/Qyzylorda">(GMT+6:00) Asia/Qyzylorda (Qyzylorda Time)</option>
    <option value="Asia/Thimbu">(GMT+6:00) Asia/Thimbu (Bhutan Time)</option>
    <option value="Asia/Thimphu">(GMT+6:00) Asia/Thimphu (Bhutan Time)</option>
    <option value="Indian/Chagos">(GMT+6:00) Indian/Chagos (Indian Ocean Territory Time)</option>
    <option value="Asia/Rangoon">(GMT+6:30) Asia/Rangoon (Myanmar Time)</option>
    <option value="Indian/Cocos">(GMT+6:30) Indian/Cocos (Cocos Islands Time)</option>
    <option value="Antarctica/Davis">(GMT+7:00) Antarctica/Davis (Davis Time)</option>
    <option value="Asia/Bangkok">(GMT+7:00) Asia/Bangkok (Indochina Time)</option>
    <option value="Asia/Ho_Chi_Minh">(GMT+7:00) Asia/Ho_Chi_Minh (Indochina Time)</option>
    <option value="Asia/Hovd">(GMT+7:00) Asia/Hovd (Hovd Time)</option>
    <option value="Asia/Jakarta">(GMT+7:00) Asia/Jakarta (West Indonesia Time)</option>
    <option value="Asia/Krasnoyarsk">(GMT+7:00) Asia/Krasnoyarsk (Krasnoyarsk Time)</option>
    <option value="Asia/Phnom_Penh">(GMT+7:00) Asia/Phnom_Penh (Indochina Time)</option>
    <option value="Asia/Pontianak">(GMT+7:00) Asia/Pontianak (West Indonesia Time)</option>
    <option value="Asia/Saigon">(GMT+7:00) Asia/Saigon (Indochina Time)</option>
    <option value="Asia/Vientiane">(GMT+7:00) Asia/Vientiane (Indochina Time)</option>
    <option value="Indian/Christmas">(GMT+7:00) Indian/Christmas (Christmas Island Time)</option>
    <option value="Antarctica/Casey">(GMT+8:00) Antarctica/Casey (Western Standard Time (Australia))</option>
    <option value="Asia/Brunei">(GMT+8:00) Asia/Brunei (Brunei Time)</option>
    <option value="Asia/Choibalsan">(GMT+8:00) Asia/Choibalsan (Choibalsan Time)</option>
    <option value="Asia/Chongqing">(GMT+8:00) Asia/Chongqing (China Standard Time)</option>
    <option value="Asia/Chungking">(GMT+8:00) Asia/Chungking (China Standard Time)</option>
    <option value="Asia/Harbin">(GMT+8:00) Asia/Harbin (China Standard Time)</option>
    <option value="Asia/Hong_Kong">(GMT+8:00) Asia/Hong_Kong (Hong Kong Time)</option>
    <option value="Asia/Irkutsk">(GMT+8:00) Asia/Irkutsk (Irkutsk Time)</option>
    <option value="Asia/Kashgar">(GMT+8:00) Asia/Kashgar (China Standard Time)</option>
    <option value="Asia/Kuala_Lumpur">(GMT+8:00) Asia/Kuala_Lumpur (Malaysia Time)</option>
    <option value="Asia/Kuching">(GMT+8:00) Asia/Kuching (Malaysia Time)</option>
    <option value="Asia/Macao">(GMT+8:00) Asia/Macao (China Standard Time)</option>
    <option value="Asia/Macau">(GMT+8:00) Asia/Macau (China Standard Time)</option>
    <option value="Asia/Makassar">(GMT+8:00) Asia/Makassar (Central Indonesia Time)</option>
    <option value="Asia/Manila">(GMT+8:00) Asia/Manila (Philippines Time)</option>
    <option value="Asia/Shanghai">(GMT+8:00) Asia/Shanghai (China Standard Time)</option>
    <option value="Asia/Singapore">(GMT+8:00) Asia/Singapore (Singapore Time)</option>
    <option value="Asia/Taipei">(GMT+8:00) Asia/Taipei (China Standard Time)</option>
    <option value="Asia/Ujung_Pandang">(GMT+8:00) Asia/Ujung_Pandang (Central Indonesia Time)</option>
    <option value="Asia/Ulaanbaatar">(GMT+8:00) Asia/Ulaanbaatar (Ulaanbaatar Time)</option>
    <option value="Asia/Ulan_Bator">(GMT+8:00) Asia/Ulan_Bator (Ulaanbaatar Time)</option>
    <option value="Asia/Urumqi">(GMT+8:00) Asia/Urumqi (China Standard Time)</option>
    <option value="Australia/Perth">(GMT+8:00) Australia/Perth (Western Standard Time (Australia))</option>
    <option value="Australia/West">(GMT+8:00) Australia/West (Western Standard Time (Australia))</option>
    <option value="Australia/Eucla">(GMT+8:45) Australia/Eucla (Central Western Standard Time (Australia))</option>
    <option value="Asia/Dili">(GMT+9:00) Asia/Dili (Timor-Leste Time)</option>
    <option value="Asia/Jayapura">(GMT+9:00) Asia/Jayapura (East Indonesia Time)</option>
    <option value="Asia/Pyongyang">(GMT+9:00) Asia/Pyongyang (Korea Standard Time)</option>
    <option value="Asia/Seoul">(GMT+9:00) Asia/Seoul (Korea Standard Time)</option>
    <option value="Asia/Tokyo">(GMT+9:00) Asia/Tokyo (Japan Standard Time)</option>
    <option value="Asia/Yakutsk">(GMT+9:00) Asia/Yakutsk (Yakutsk Time)</option>
    <option value="Australia/Adelaide">(GMT+9:30) Australia/Adelaide (Central Standard Time (South Australia))</option>
    <option value="Australia/Broken_Hill">(GMT+9:30) Australia/Broken_Hill (Central Standard Time (South Australia/New South Wales))</option>
    <option value="Australia/Darwin">(GMT+9:30) Australia/Darwin (Central Standard Time (Northern Territory))</option>
    <option value="Australia/North">(GMT+9:30) Australia/North (Central Standard Time (Northern Territory))</option>
    <option value="Australia/South">(GMT+9:30) Australia/South (Central Standard Time (South Australia))</option>
    <option value="Australia/Yancowinna">(GMT+9:30) Australia/Yancowinna (Central Standard Time (South Australia/New South Wales))</option>
    <option value="Antarctica/DumontDUrville">(GMT+10:00) Antarctica/DumontDUrville (Dumont-d'Urville Time)</option>
    <option value="Asia/Sakhalin">(GMT+10:00) Asia/Sakhalin (Sakhalin Time)</option>
    <option value="Asia/Vladivostok">(GMT+10:00) Asia/Vladivostok (Vladivostok Time)</option>
    <option value="Australia/ACT">(GMT+10:00) Australia/ACT (Eastern Standard Time (New South Wales))</option>
    <option value="Australia/Brisbane">(GMT+10:00) Australia/Brisbane (Eastern Standard Time (Queensland))</option>
    <option value="Australia/Canberra">(GMT+10:00) Australia/Canberra (Eastern Standard Time (New South Wales))</option>
    <option value="Australia/Currie">(GMT+10:00) Australia/Currie (Eastern Standard Time (New South Wales))</option>
    <option value="Australia/Hobart">(GMT+10:00) Australia/Hobart (Eastern Standard Time (Tasmania))</option>
    <option value="Australia/Lindeman">(GMT+10:00) Australia/Lindeman (Eastern Standard Time (Queensland))</option>
    <option value="Australia/Melbourne">(GMT+10:00) Australia/Melbourne (Eastern Standard Time (Victoria))</option>
    <option value="Australia/NSW">(GMT+10:00) Australia/NSW (Eastern Standard Time (New South Wales))</option>
    <option value="Australia/Queensland">(GMT+10:00) Australia/Queensland (Eastern Standard Time (Queensland))</option>
    <option value="Australia/Sydney">(GMT+10:00) Australia/Sydney (Eastern Standard Time (New South Wales))</option>
    <option value="Australia/Tasmania">(GMT+10:00) Australia/Tasmania (Eastern Standard Time (Tasmania))</option>
    <option value="Australia/Victoria">(GMT+10:00) Australia/Victoria (Eastern Standard Time (Victoria))</option>
    <option value="Australia/LHI">(GMT+10:30) Australia/LHI (Lord Howe Standard Time)</option>
    <option value="Australia/Lord_Howe">(GMT+10:30) Australia/Lord_Howe (Lord Howe Standard Time)</option>
    <option value="Asia/Magadan">(GMT+11:00) Asia/Magadan (Magadan Time)</option>
    <option value="Antarctica/McMurdo">(GMT+12:00) Antarctica/McMurdo (New Zealand Standard Time)</option>
    <option value="Antarctica/South_Pole">(GMT+12:00) Antarctica/South_Pole (New Zealand Standard Time)</option>
    <option value="Asia/Anadyr">(GMT+12:00) Asia/Anadyr (Anadyr Time)</option>
    <option value="Asia/Kamchatka">(GMT+12:00) Asia/Kamchatka (Petropavlovsk-Kamchatski Time)</option>
    </select>
      </td>
    </tr>
  </table>
  <td>
  </tr>
</table>
</font>
</form>
</body>
</html>
EOF
return \$stuff;
}

1;
