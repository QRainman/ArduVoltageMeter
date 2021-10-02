#!/usr/bin/python3

from serial import Serial
import requests
import traceback
import time
from BatteryMonitor import BatteryMonitor
from optparse import OptionParser


class ChargeMonitor(BatteryMonitor):
  def __init__(self, batteryLowCutoff, batteryHighCutOff, calibrationFile, port):
    super().__init__(batteryLowCutOff=batteryLowCutoff, batteryHighCutOff=batteryHighCutOff, shuntResistance=1.433,
                     voltMeterChannels=[0, 1, 4, 5], calibrationFile=calibrationFile, port=port)

  def startCharge(self):
    self.vm.enableRelay()

  def stopCharge(self):
    self.vm.disableRelay()


def sendData(battery, chargeSession, voltage, current, integratedCurrent, intPower, t):
  session = requests.session()
  session.trust_env = False

  lineString = "batdischarge,battery=%s,charge_session=%s,direction=charge " % (battery, chargeSession)
  lineString += "U_bat=%f," % voltage
  lineString += "I_bat=%f," % current
  lineString += "E_int=%f," % intPower
  lineString += "I_int=%f" % integratedCurrent

  timestamp = t.timestamp()
  utc_time = int(timestamp) * 1000000000
  lineString += ' %d' % utc_time
  print(lineString)

  try:
    response = session.post('http://192.168.178.220:8090/telegraf', lineString)
    print(response)
  except:
    print('Failed to submit data string %s' % lineString)
    print(traceback.format_exc())


def getOptions():
  opt = OptionParser()
  opt.add_option('-b', '--battery_id', target='battery_id', help='Battery Serial Number', type='string', default='Unknown')
  opt.add_option('-m', '--i_min', target='i_min', help='Current at which charging stops in mA', type='float', default=50.0)
  opt.add_option('-U', '--u_max', target='u_max', help='Max Voltage safety cutoff in V', type='float', default=4.3)
  opt.add_option('-L', '--u_min', target='u_min', help='Minimum Voltage cutoff in V', type='float', default=0.0)
  opt.add_option('-i', '--i_start', target='i_start', help='Integrated Current start value in Ah', type='float', default=0.0)
  opt.add_option('-p', '--port', target='port', help='Serial port name', type='string', default='/dev/ttyACM0')
  opt.add_option('-r', '--baud', target='baud_rate', help='Serial port baud rate', type='int', default=9600)
  opt.add_option('-c', '--calib', target='calib_file', help='Path to calibration file', type='string', default='calibration-all.json')
  return opt.parse_args()


def main():
  options, args = getOptions()
  chargeMon = ChargeMonitor(options.u_min, options.u_max, options.calib_file, Serial('options.port', options.baud_rate))
  chargeMon.start(batteryHighCutOff=options.u_max)
  #chargeMon.start(integratedCurrentLimit=0.8)
  chargeMon.integradetCurrent = 0
  run = True
  while run:
    chargeMon.readValues()
    print(chargeMon.rawValues)
    t, chargeSession, U_bat, I_bat, int_current, int_power = chargeMon.getCurrentState()
    sendData(options.battery_id, chargeSession, U_bat, I_bat, int_current, int_power, t)
    if I_bat < (options.i_min * 1000):
      chargeMon.stopCharge()
      print('Charging complete, capacity: %f' % int_current)
    time.sleep(5)


if __name__ == '__main__':
  main()


