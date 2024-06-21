html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <link rel="shortcut icon" type="image/x-icon" href="/favicon.ico">
  <!--<meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>APP</title> -->
</head>
<body>
  <h1>Hot Water Controller</h1>
  <h2>{{version}}</h2>
  <h3>
  <form action="/status">
    <a href="http://{{ipaddr}}:9000" target="_blank">Realtime status</a>
  </form>
  </h3>

  <form action="/runit">
  <input type="submit" value="Run pump cycle">
  </form>
  <form action="/testing">
    <input type="submit" value="Make children flash">
    </form>
  
  <form action="/action"  method="post">
  <input type="submit" value="Update all Values"><br>     
  <b>Flow Cycle Values</b><br> 
  <label for="cycles_to_run">cycles_to_run_after_pump_on_before_checking_flow:</label><br>
  <input type="number" id="cycles_to_run" name="cycles_to_run"value="{{cycles_to_run}}" min="1" max="99"><br>
  
  <label for="max_pump">max_pump_on_seconds:</label><br>
  <input type="number" id="max_pump" name="max_pump"value="{{max_pump}}" maxlength="4" min="1" max="999"><br>
  
  <label for="pulse_collection">pulse_collection_milliseconds 1000ms = 1 second:</label><br>
  <input type="number" id="pulse_collection" name="pulse_collection"value="{{pulse_collection}}" min="1" max="9999"><br>
  <b>Pump only runs between these values<br>Min is where the heater is off, Max is when faucit is on<b></b>
  <label for="min_pulses">min_pulses_to_turn_off:</label><br>
  <input type="number" id="min_pulses" name="min_pulses"value="{{min_pulses}}" min="1" max="99"><br>
  
  <label for="max_pulses">max_pulses_to_turn_off:</label><br>
  <input type="number" id="max_pulses" name="max_pulses"value="{{max_pulses}}" min="1" max="99"><br>

  <label for="pulses_per_ltr ">Pulses per liter:</label><br>
  <input type="number" id="pulses_per_ltr" name="pulses_per_ltr"value="{{pulses_per_ltr}}" min="1" max="9999"><br>

  <label for="minimum_number_of_children ">minimum number of children:</label><br>
  <input type="number" id="minimum_number_of_children" name="minimum_number_of_children"value="{{minimum_number_of_children}}" min="0" max="99"><br>
  
  <!--
  <h3>Faucet Trigger Values</h3>
  <b>Faucet needs to  be left open between these values</b><br><b>to trigger a pump cycle</b><br>
  <label for="trigger_min">trigger_on_to_off_milliseconds_min:</label><br>
  <input type="number" id="trigger_min" name="trigger_min"value="{{trigger_min}}" min="1" max="9999"><br>
  
  <label for="trigger_max">trigger_on_to_off_milliseconds_max:</label><br>
  <input type="number" id="trigger_max" name="trigger_max"value="{{trigger_max}}" min="1" max="9999"><br>
  -->
  <!-- 
  <h3>Other Items</h3>
  <label for="aa">do_we_send_to_AlertAway:</label><br>
  <input type="checkbox" id="aa" name="aa" {{aa}}><br>
  -->
  <input type="submit" value="Update all Values">
  </form>
  
  <form action="/defaults">
  <input type="submit" value="Set to defaults">
  </form>
  <form action="/reboot">
  <input type="submit" value="reboot">
  </form> 
  
</body>
</html>
"""
