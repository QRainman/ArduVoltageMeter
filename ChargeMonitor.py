from serial import Serial
import requests
import traceback
import time
from BatteryMonitor import BatteryMonitor


class ChargeMonitor(BatteryMonitor):
  def __init__(self):
    super().__init__(batteryLowCutOff=2.95, batteryHighCutOff=4.25, shuntResistance=1.433, voltMeterChannels=[0, 1, 4, 5],
                     calibrationFile='calibration.json', port=Serial('COM100', 9600))

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


def main():
  chargeMon = ChargeMonitor()
  chargeMon.start(batteryHighCutOff=4.3)
  #chargeMon.start(integratedCurrentLimit=0.8)
  chargeMon.integradetCurrent = 0.507
  run = True
  while run:
    chargeMon.readValues()
    print(chargeMon.rawValues)
    t, chargeSession, U_bat, I_bat, int_current, int_power = chargeMon.getCurrentState()
    sendData('I1804R49746', chargeSession, U_bat, I_bat, int_current, int_power, t)
    time.sleep(5)


if __name__ == '__main__':
  main()


