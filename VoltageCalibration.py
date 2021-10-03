#!/usr/bin/python3

from ArduVoltmeter import ArduVoltmeter
import serial
import json
from optparse import OptionParser

opt = OptionParser()
opt.add_option('-p', '--port', dest='port', help='Serial port name', default='/dev/ttyACM0')
opt.add_option('-b', '--baud', dest='baud', help='Serial port baud rate', default=9600, type='int')
opt.add_option('-o', '--output', dest='output_file', help='Output file where json calibration will be stored', default='calibration-all.json', type='string')
options, args = opt.parse_args()

voltMeter = ArduVoltmeter(calibrationFile=None, channelList=[0, 1, 2, 3, 4, 5], port=serial.Serial(options.port, options.baud))

voltMeter.start()
voltMeter.waitReady()

volts = []
counts = []

cont = True
while cont:
  print('Voltage Reading or "e" for end: ')
  inp = input()
  if inp == 'e':
    break

  volts.append(float(inp))
  cnt = voltMeter.readValuesWait()[1]
  print('Counts: %s' % cnt)
  counts.append(cnt)

for c, v in zip(counts, volts):
  print('%s: %f' % (c, v))

d = {'volts': volts, 'counts': counts}

print(json.dumps(d, indent=2, sort_keys=True))
with open(options.output_file, 'w') as outfile:
  outfile.write(json.dumps(d, indent=2, sort_keys=True))

voltMeter.stop()
