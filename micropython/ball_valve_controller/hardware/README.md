# development version with the following parts:

# controller
These are all [D1 MINI](https://www.wemos.cc/en/latest/d1/d1_mini.html) form factor, using ESP32 for the processor
[ESP32-S2 mini](https://www.wemos.cc/en/latest/s2/s2_mini.html) microcontroller  
2 [relay shields](https://www.wemos.cc/en/latest/d1_mini_shield/relay.html)  
[triple base](https://www.wemos.cc/en/latest/d1_mini_shield/tripler_base.html) 
my valve wants 12v so [DC power hat](https://www.wemos.cc/en/latest/d1_mini_shield/dc_power.html)
Quite a few different sources like amazon, temu, aliexpress to name a few  

# Motor valve
I using a "five wire" valve [CR05](CR05_wiring.png) and that spec is what the system is written for.
It is not difficult to change to support the simpler valves  

# wiring:
ES32-S2 pins to "D1 Mini" pins and the valve wire color:  
open_relay_pin  = 35   D1  Yellow  
close_relay_pin = 33   D2  Black  
feed back pins  
full_open_pin   = 16    D3   Green  
full_closed_pin = 18    D4   red  

Relays tend to be hard wired to D1-Mini D1 line  
So a trace cut and a jumper on the LAST triple slot.
Much easier than changing a relay. 








  

