#!/usr/bin/python3

from ArduVoltmeter import ArduVoltmeter
from serial import Serial

vm = ArduVoltmeter([0, 1, 4, 5], calibrationFile='calibration-all.json', port=Serial('/dev/ttyACM0', 9600))
vm.disableRelay()
