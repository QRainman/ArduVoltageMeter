from ArduVoltmeter import ArduVoltmeter
from serial import Serial
import datetime


class BatteryMonitor:
  def __init__(self, options, shuntResistance=9.77, voltMeterChannels=[0, 1, 2, 3]):
    self.batteryLowCutOff = options.u_min
    self.batteryHighCutOff = options.u_max
    self.integratedCurrentLimit = 0
    self.integratedPower = 0

    self.shuntResistance = shuntResistance
    self.integradetCurrent = options.i_start
    self.batVoltage = 0.0
    self.bat_channel_1 = 0
    self.bat_channel_2 = 1
    self.current_channel_1 = 2
    self.current_channel_2 = 3

    self.vm = ArduVoltmeter(voltMeterChannels, options.calib_file, Serial(options.port, options.baud_rate))
    self.vm.start()
    self.vm.waitReady()

    self.prevTime = 0
    self.rawValues = None
    self.chargeSession = int(datetime.datetime.now().timestamp())

  def checkLimits(self):
    _tmp, v_bat = self.getBatVoltage()
    if v_bat <= self.batteryLowCutOff or v_bat >= self.batteryHighCutOff or \
        (0.0 < self.integratedCurrentLimit < self.integradetCurrent):
      self.vm.disableRelay()

  def start(self, batteryLowCutOff=3.0, batteryHighCutOff=4.2, integratedCurrentLimit=0.0):
    self.batteryLowCutOff = batteryLowCutOff
    self.batteryHighCutOff = batteryHighCutOff
    self.integratedCurrentLimit = integratedCurrentLimit

  def getCurrent(self):
    vDiff = self.rawValues[self.current_channel_2] - self.rawValues[self.current_channel_1]
    current = vDiff / self.shuntResistance
    print(current)
    return current

  def _integrateCurrent(self, t):
    if self.prevTime == 0:
      self.prevTime = t
      return

    current = self.getCurrent()
    _tmp, voltage = self.getBatVoltage()
    timeDiff = (t-self.prevTime).total_seconds()

    self.integradetCurrent += (current * float(timeDiff) / 3600.0)
    self.integratedPower += current * voltage * float(timeDiff) / 3600.0

  def readValues(self):
    updateTime, values = self.vm.readValuesWait()
    self.rawValues = values
    self._integrateCurrent(updateTime)
    _blah, self.batVoltage = self.getBatVoltage()
    self.prevTime = updateTime
    self.checkLimits()

  def getBatVoltage(self):
    return self.prevTime, self.rawValues[self.bat_channel_2] - self.rawValues[self.bat_channel_1]

  def getIntegratedCurrent(self):
    return self.prevTime, self.integradetCurrent

  def getCurrentState(self):
    return self.prevTime, self.chargeSession, self.batVoltage, self.getCurrent(), self.integradetCurrent, self.integratedPower

  def getRelayState(self):
    return self.vm.relay

  def stop(self):
    return self.vm.stop()

  @staticmethod
  def getOptions(opt):
    opt.add_option('-b', '--battery_id', dest='battery_id', help='Battery Serial Number', type='string', default='Unknown')
    opt.add_option('-U', '--u_max', dest='u_max', help='Max Voltage safety cutoff in V', type='float', default=4.25)
    opt.add_option('-L', '--u_min', dest='u_min', help='Minimum Voltage cutoff in V', type='float', default=0.0)
    opt.add_option('-i', '--i_start', dest='i_start', help='Integrated Current start value in Ah', type='float', default=0.0)
    opt.add_option('-p', '--port', dest='port', help='Serial port name', type='string', default='/dev/ttyACM0')
    opt.add_option('-r', '--baud', dest='baud_rate', help='Serial port baud rate', type='int', default=9600)
    opt.add_option('-c', '--calib', dest='calib_file', help='Path to calibration file', type='string', default='calibration-all.json')
    return opt


