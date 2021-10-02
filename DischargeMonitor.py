#!/usr/bin/python3

import requests
import traceback
import time

from BatteryMonitor import BatteryMonitor
from serial import Serial
from optparse import OptionParser


class ChargeMonitor(BatteryMonitor):
  def __init__(self, options, shuntResistance=9.77):
    super().__init__(options, shuntResistance=shuntResistance, voltMeterChannels=[0, 1, 2, 3])

  def startDischarge(self):
    self.vm.enableRelay()

  def stopDischarge(self):
    self.vm.disableRelay()


class DischargeTest:
  def __init__(self):
    options, _ = DischargeTest.getOptions()
    self.chargeMon = ChargeMonitor(options, shuntResistance=options.shunt)
    self.batteryID = options.battery_id
    self.run = False
    pass

  def interruptHandler(self):
    pass

  def sendData(self, chargeSession, voltage, current, integratedCurrent, intPower, t):
    session = requests.session()
    session.trust_env = False

    lineString = "batdischarge,battery=%s,charge_session=%s,direction=discharge " % (self.batteryID, chargeSession)
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
      # pass
    except:
      print('Failed to submit data string %s' % lineString)
      print(traceback.format_exc())

  def start(self):
    self.chargeMon.start()
    self.run = True
    while self.run:
      self.chargeMon.readValues()
      print(self.chargeMon.rawValues)
      print(self.chargeMon.getRelayState())
      t, chargeSession, U_bat, I_bat, int_current, int_power = self.chargeMon.getCurrentState()
      self.sendData(chargeSession, U_bat, I_bat, int_current, int_power, t)
      if self.chargeMon.vm.relay == 0:
        print('Discharge finished. Capacity: %f mAh' % self.chargeMon.integradetCurrent * 1000)
      time.sleep(5)
    self.chargeMon.stopDischarge()
    self.chargeMon.vm.stop()

  @staticmethod
  def getOptions():
    opt = OptionParser()
    ChargeMonitor.getOptions(opt)
    opt.add_option('-s', '--shunt', dest='shunt', help='Shunt resistance in Ohm', type='float', default=9.77)
    return opt.parse_args()


if __name__ == '__main__':
  dm = DischargeTest()
  dm.start()
