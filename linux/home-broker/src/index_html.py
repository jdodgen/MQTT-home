# you may wonder why this is not just a file.
# the reason is that this loads faster and does not require a slow sd card Access
# each time HTTP is accessed.

html = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <!--<meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>APP</title> -->
  <style>
    body {
      background-color: #d5f4e6;     
    }
    table.leftright{
      border: 2px solid orange;
      border-collapse: collapse;   
    }
    th.leftright{
      text-align: center;
    }
    td.leftright{
      text-align: center;
    }
    table.center{
      border: 2px solid orange;
      border-collapse: collapse;
    }
    th.center{
      border: 2px solid orange;
      border-collapse: collapse;
      text-align: center;
    }
    td.center{
      border: 2px solid orange;
      border-collapse: collapse;
      text-align: center;
    }

    table td,tr{
      border: 2px solid blue;
      border-collapse: collapse; 
    } 
    
  </style>
</head>

<body>
  <table style="border: none;">
    <tr style="border: none;">
        <td style="border: none;"><h1  style="font-size: 40px;">home-broker:&nbsp&nbsp</h1></td>

        <td style="border: none;"><h2>Device and WeMo/fauxmo Management</h2></td>
    </tr>
  </table>
  <table>
    <tr>
      <th  style="text-align: left;">
        <a href="http://home-broker.local:8080/">
          <h2>Maintain zigbee2mqtt Devices</h2>
        </a>
        <h3 style="color: red" ;>{{error_message}}</h3>
      </th>
    </tr>
    {% if do_update_IP %}
    <tr>
      <td>
        <form action="/update_manIP" method="post">
          <h2>Update Feature</h2>
          <table class="leftright">
            <tr>
              <th>
                <button type="submit" name=action value="Update/{{man_ip[0]}}">Update</button>
                <!--&nbsp;<br>
                <button type="submit" name=action value="Delete/{{man_ip[0]}}">Delete</button>
                -->
              </th>
              <th>
                <h1>"{{man_ip[1]}}","{{man_ip[2]}}"</h1>
              </th>
            </tr>
            <tr>
              <th>
                Feature Type
              </th>
              <td>
                <select name="type">
                  <option value="{{man_ip[3]}}">{{man_ip[3]}}</option>
                  <option value="binary">Binary</option>
                  <option value="numeric">Numeric</option>
                </select>
              </td>
            </tr>
            <tr>
              <th>
                Access
              </th>
              <td>
                <select name="access">
                  <option value="{{man_ip[7]}}">{{man_ip[7]}}</option>
                  <option value="sub">sub</option>
                  <option value="pub">pub</option>
                </select>
              </td>
            </tr>
            <tr>
              <th>
                MQTT topic
              </th>
              <td>
                <input type="text" size="30" name="topic" value="{{man_ip[4]}}">
              </td>
            </tr>
            <tr>
              <th>
                Payload On/other value
              </th>
              <td>
                <input type="text" size="30" name="on" value="{{man_ip[5]}}">
              </td>
            </tr>
            <tr>
              <th>
                Payload Off value
              </th>
              <td>
                <input type="text" size="30" name="off" value="{{man_ip[6]}}">
              </td>
            </tr>
          </table>
        </form>
      </td>
    </tr>
    {% endif %}
    <tr>
      <td>
        <form action="/create_wemo" method="post">
          <h2>WeMo to Device mapping</h2>
          <table class="leftright">
            <tr>
              <th>
                <button type="submit" name=action value="create_wemo">Create WeMo</button><br>
                <button type="submit" name=action value="restart">Restart FauxMo Process</button><br>
                <button type="submit" name=action value="display">Display future FauxMo config</button>
              </th>
              <th>
                <label for="wemo_name">WeMo Name:</label>
                <input type="text" id="wemo_name" name="wemo_name"><br>
                <label for="wemo_port">WeMo Port:</label>
                <input type="text" id="wemo_port" name="wemo_port" value="Optional"><br>
              </th>
              <th>
                Device:
              </th>
              <th>
                <select id="wemo_device" name="wemo_device" size="5">
                  {% for b in get_devices_for_wemo %}
                  <option value="{{b[0]}}">
                 "{{b[1]}}"({{b[2]}})
                  Property({{b[3]}})Desc[{{b[4]}}]
                  topic[[{{b[5]}}]
                  payloads[{{b[6]}}]&nbsp[{{b[7]}}] </option>
                  {% endfor %}
                </select>
              </th>
            </tr>
          </table>
        </form>
      </td>
    </tr>

    <tr>
      <td>
        <form action="/modify_wemo" method="post">
          <table class="center">
            <tr>
              <th rowspan="2">
                Mapped WeMo
              </th>
              <th colspan="2">
                WeMo
              </th>
              <th colspan="100%">
                MQTT
              </th>
            </tr>
            <tr>
              <th>
                Name
              </th>
              <th>
                port
              </th>
              <th>
                Friendly Name
              </th>
              <th>
                Description
              </th>
              <th>
                feature
              </th>
              <th>
                on payload
              </th>
              <th>
                off payload
              </th>
            </tr>
            {% for d in all_wemo %}
            <tr>
              <td>
                <button type="submit" name=action value="delete_wemo/{{d[0]}}">Delete</button>
              </td>
              <td>{{d[1]}}</td>
              <td>{{d[2]}}</td>
              <td>{{d[3]}}</td>
              <td>{{d[4]}}</td>
              <td>{{d[5]}}</td>
              <td>{{d[6]}}</td>
              <td>{{d[7]}}</td>
            </tr>
            {% endfor %}
          </table>
        </form>
      </td>
    </tr>
    <tr>
      <td>
        <form action=" /create_IP_device" method="post">
          <h2>Manual Creation of IP Devices</h2>
          <table class="leftright">
            <tr>
              <td><button type="submit" name=action value="create_wifi">Create IP Device</button>
              <th><label for="IP_name">Device Name:</label>
                <input type="text" id="IP_name" name="IP_name"><br>
              </th>
              <th><label for="IP_description">Description:</label>
                <input type="text" id="IP_description" name="IP_description"><br>
              </th>
            </tr>
          </table>
        </form>
      </td>
    </tr>
    <tr>
      <td>
        <form action="/create_IP_feature" method="post">
          <table class="leftright">
            <tr>
              <td><button type="submit" name=action value="create_IP_feature">Create IP Device feature</button>
              <th><label for="wifi_access">Device Name:</label>
              <td>
                <select name="device_ieee_address" size="4">
                  {% for b in manual_device_names %}
                  <option value="{{b[0]}}">{{b[1]}}&nbsp[{{b[2]}}] </option>
                  {% endfor %}
                </select>
              </td>
              </th>
              <th><label for="property">property:</label>
                <input type="text" id="property" name="property"><br>
              </th>
            </tr>
          </table>
        </form>
      </td>
    </tr>
    
    </td>
    </tr>
    <tr>
      <td>
        <form action="/all_devices" method="post">
          <h2>All  Things</h2>
          <table class="center">
            <tr>
              <th>
                Friendly name
              </th>
              <th>
                Description
              </th>
              <th>
                last<br>date
              </th>
              <th>
                Property
              </th>
              <th>
                Feature<br>Description
              </th>
              <th>
                Type
              </th>
              <th>
                Access
              </th>
              <th>
                MQTT Topic
              </th>
              <th>
                MQTT payload<br>True/other
              </th>
              <th>
                MQTT payload<br>False
              </th>
            </tr>
            <tr>
              <th colspan="100%"  style="text-align: left;">Manual entered IP devices</th>
            </tr>
            {% for d in manIP_devices %}
            <tr>
              <th align="center">
                {% if d[1] %}
                {{d[1]}} 
                <button type="submit" name=action value="delete/{{d[1]}}">
                    Delete
                </button>
                {% endif %}
              </th>
              <td>{{d[2]}}</td>
              <td>{{d[3]}}</td>
              <th>{{d[4]}}
                <button type="submit" name=action value="manIP/{{d[0]}}">Modify
                  values
                </button>
              </th>
              <td>{{d[5]}}</td>
              <td>{{d[6]}}</td>
              <td>{{d[7]}}</td>
              <td>{{d[8]}}</td>
              <td>{{d[9]}}<br>{% if d[11] %} <button type="submit" name=action value="send/1/{{d[0]}}">Send</button>{%
                endif %}</td>
              <td>{{d[10]}}<br>{% if d[11] %} <button type="submit" name=action value="send/0/{{d[0]}}">Send</button>
                {%endif %}</td>
            </tr>
            {% endfor %}
            <tr>
              <th colspan="100%"  style="text-align: left;">Auto discovered IP devices
              <button type="submit" name=action value="iprefresh"> refresh auto IP devices</th>
            </tr>
            {% for d in autoIP_devices %}
            <tr>
              <th>
                {{d[1]}}
                {% if d[1] %}
                <button type="submit" name=action value="delete/{{d[1]}}">
                  Delete
                </button>
                {% endif %}
              </th>
              <td>{{d[2]}}</td>
              <td>{{d[3]}}</td>
              <th>{{d[4]}}</th>
              <td>{{d[5]}}</td>
              <td>{{d[6]}}</td>
              <td>{{d[7]}}</td>
              <td>{{d[8]}}</td>
              <td>{{d[9]}}<br>{% if d[11] %} <button type="submit" name=action value="send/1/{{d[0]}}">Send</button>{%
                endif %}</td>
              <td>{{d[10]}}<br>{% if d[11] %} <button type="submit" name=action value="send/0/{{d[0]}}">Send</button>{%
                endif %}</td>
            </tr>
            {% endfor %}
            <tr>
              <th colspan="100%"  style="text-align: left;">ZigBee devices
                <button type="submit" name=action value="zbrefresh">Refresh ZigBee2MQTT devices</button>
              </th>
            </tr>
            {% for d in zigbee_devices %}
            <tr>
              <th>{{d[1]}}</th>
              <td>{{d[2]}}</td>
              <td>{{d[3]}}</td>
              <th>{{d[4]}}</th>
              <td>{{d[5]}}</td>
              <td>{{d[6]}}</td>
              <td>{{d[7]}}</td>
              <td>{{d[8]}}</td>
              <td>{{d[9]}}<br>{% if d[11] %} <button type="submit" name=action value="send/1/{{d[0]}}">Send</button>{%
                endif %}</td>
              <td>{{d[10]}}<br>{% if d[11] %} <button type="submit" name=action value="send/0/{{d[0]}}">Send</button>{%
                endif %}</td>
            </tr>
            {% endfor %}
          </table>
        </form>
      </td>
    </tr>
  </table>
</body>

</html>
'''

if __name__ == "__main__":
    import os
    import webbrowser

    path = os.path.abspath('sample.html')
    print(path)
    url = 'file://' + path

    with open(path, 'w') as f:
      f.write(html)
    webbrowser.open(url)