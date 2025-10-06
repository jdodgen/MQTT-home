import serial
port = '/dev/ttyACM0'
ser = serial.Serial(port, 115200)  # Open serial port
while True:
    line = ser.readline().decode('utf-8').strip()
    if line:
        print(line)
ser.close() 
