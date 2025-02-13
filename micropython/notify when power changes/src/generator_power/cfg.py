
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: 2025-02-12 21:27:43 
# MAKE YOUR CHANGES IN install.py
#
led_gpio = 3  # "D3" on D1-Mini proto card
#
# best to use firewalled router/wifi for IoT things
ssid="JEDguest"
wifi_password = "9098673852"
#
start_delay=10
number_of_seconds_to_wait=60
server = 'home-broker.local'
#
# a python list of one or more email addresses ["9095551212@tmomail.net", "you@gmail.com"]
send_messages_to = ["9097472800@tmomail.net", "jim@dodgen.us"]
# 
# gmail account to send emails through  
#
gmail_password = "xdom zveb qytq snms" # gmail generates this I can change it in the future
gmail_user = "notifygenerator@gmail.com"
# gen cost to run per hour https://generatorsupercenter.com/how-much-do-generators-cost-to-run/
cost_to_run = 1.88  # in any currency 
