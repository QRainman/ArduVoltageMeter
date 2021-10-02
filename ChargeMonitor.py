#!/usr/bin/python3

from serial import Serial
import requests
import traceback
import time
from BatteryMonitor import BatteryMonitor
from optparse import OptionParser


class ChargeMonitor(BatteryMonitor):
  def __init__(self, options, shuntResistance=1.433):
    super().__init__(options, shuntResistance=shuntResistance, voltMeterChannels=[0, 1, 4, 5])

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
  ChargeMonitor.getOptions(opt)
  opt.add_option('-m', '--i_min', dest='i_min', help='Current at which charging stops in mA', type='float', default=50.0)
  opt.add_option('-s', '--shunt', dest='shunt', help='Shunt resistance in Ohm', type='float', default=1.433)
  return opt.parse_args()


def main():
  options, args = getOptions()
  chargeMon = ChargeMonitor(options, options.shunt)
  chargeMon.start(batteryHighCutOff=options.u_max)
  #chargeMon.start(integratedCurrentLimit=0.8)
  chargeMon.integradetCurrent = 0
  run = True
  while run:
    chargeMon.readValues()
    print(chargeMon.rawValues)
    t, chargeSession, U_bat, I_bat, int_current, int_power = chargeMon.getCurrentState()
    sendData(options.battery_id, chargeSession, U_bat, I_bat, int_current, int_power, t)
    if (options.i_min / 1000) > I_bat > 0.005:
      chargeMon.stopCharge()
      print('Charging complete, capacity: %f' % int_current)
    time.sleep(5)


if __name__ == '__main__':
  main()


