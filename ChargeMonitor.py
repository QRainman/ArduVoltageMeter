#!/usr/bin/python3

from serial import Serial
import requests
import traceback
import time
from BatteryMonitor import BatteryMonitor
from optparse import OptionParser
from threading import Thread


class ChargeMonitor(BatteryMonitor):
  def __init__(self, options, shuntResistance=1.408):
    super().__init__(options, shuntResistance=shuntResistance, voltMeterChannels=[0, 1, 5, 4])

  def startCharge(self):
    self.vm.enableRelay()

  def stopCharge(self):
    self.vm.disableRelay()


class ChargeTest:
  def __init__(self):
    options, _ = ChargeTest.getOptions()
    self.chargeMon = ChargeMonitor(options, shuntResistance=options.shunt)
    self.batteryID = options.battery_id
    self.run = True
    self.runThread = None
    self.cutOffCurrent = options.i_min

  def sendData(self, chargeSession, voltage, current, integratedCurrent, intPower, t):
    session = requests.session()
    session.trust_env = False

    lineString = "batdischarge,battery=%s,charge_session=%s,direction=charge " % (self.batteryID, chargeSession)
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

  @staticmethod
  def getOptions():
    opt = OptionParser()
    ChargeMonitor.getOptions(opt)
    opt.add_option('-m', '--i_min', dest='i_min', help='Current at which charging stops in mA', type='float', default=50.0)
    opt.add_option('-s', '--shunt', dest='shunt', help='Shunt resistance in Ohm', type='float', default=1.408)
    return opt.parse_args()

  def start(self):
    if self.runThread is not None:
      print('Run thread already exists. Aborting start')
      return

    print('Creating monitoring thread')
    self.runThread = Thread(target=self.run_a)
    self.runThread.start()
    print('Monitoring thread started')

  def run_a(self):
    print('Starting discharge monitor')
    self.chargeMon.start()
    doneCount = 0
    while self.run:
      self.chargeMon.readValues()
      print(self.chargeMon.rawValues)
      t, chargeSession, U_bat, I_bat, int_current, int_power = self.chargeMon.getCurrentState()
      self.sendData(chargeSession, U_bat, I_bat, int_current, int_power, t)
      if (self.cutOffCurrent / 1000) > I_bat:
        doneCount += 1
        if doneCount >= 5:
          self.chargeMon.stopCharge()
          print('Charging complete, capacity: %f' % int_current)
      else:
        doneCount = 0
      time.sleep(5)

  def stop(self):
    self.run = False
    self.runThread.join()
    self.runThread = None


if __name__ == '__main__':
  cm = ChargeTest()
  cm.start()
  while True:
    res = input('press s to start discharge, x to stop discharge, e to end: ')
    if res == 's':
      cm.chargeMon.startCharge()
    elif res == 'x':
      cm.chargeMon.stopCharge()
    elif res == 'e':
      cm.stop()
      break
    else:
      print('Unknown command')


