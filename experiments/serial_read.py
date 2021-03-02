import serial

ttyname = '/dev/ttyACM0'

with serial.Serial(ttyname) as ser:
    line = ser.readline()
    print(line)
