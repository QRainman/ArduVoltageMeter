from ArduVoltmeter import ArduVoltmeter
import serial
import json

voltMeter = ArduVoltmeter(channelList=[0], port=serial.Serial('COM4', 9600))

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
  cnt = voltMeter.readValuesWait()[1][0]
  print('Counts: %s' % cnt)
  counts.append(cnt)

for c, v in zip(counts, volts):
  print('%d: %f' % (c, v))

d = {'volts': volts, 'counts': counts}

print(json.dumps(d, indent=2, sort_keys=True))
voltMeter.stop()
