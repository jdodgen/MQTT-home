# monitoring serial port
# MIT licence copyright 2025 Jim Dodgen
#
import serial
import time
port = '/dev/ttyACM1'
baud = 115200
while True:
    try:
        device = serial.Serial(port, baud)  # Open serial port
    except KeyboardInterrupt:
        device.close()
        exit()
    except:
        print(port+" not found")
        time.sleep(2)
    else:
        while True:
            try:
                line = device.readline().decode('utf-8').strip()
                if line:
                    print(line)
            except KeyboardInterrupt:
                device.close()
                exit()
            except:
                break


