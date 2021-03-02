import serial

ttyname = '/dev/ttyACM0'

# baudrate = 9600  # measured with sudo stty -F /dev/ttyACM0
with serial.Serial(ttyname) as ser:
    # line = ser.readline()
    # print(line)
    byte = ser.read()
    print(byte)
