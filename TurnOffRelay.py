from ArduVoltmeter import ArduVoltmeter
from serial import Serial

vm = ArduVoltmeter([0, 1, 4, 5], calibrationFile='calibration.json', port=Serial('COM4', 9600))
vm.disableRelay()
