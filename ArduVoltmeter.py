import json
import logging
import datetime
import threading
import copy
import serial
import time
from scipy import interpolate

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class ArduVoltmeter:
  def __init__(self, channelList=[0], calibrationFile=None, port=None):
    self.channelList = channelList
    self.calibrationFile = calibrationFile
    if self.calibrationFile is not None:
      self.calibrationFunction = self.readCalibrationFile()
    else:
      self.calibrationFunction = self.dumbConvert

    self.port = port
    self.values = None
    self.run = False
    self.runThread = None
    self.updateLock = threading.Lock()
    self.readyLock = threading.Condition()
    self.ready = False
    self.relay = 0

  def readCalibrationFile(self):
    with open(self.calibrationFile) as inputFile:
      calibData = json.load(inputFile)
      cnts = calibData['counts']
      volts = calibData['volts']
      return interpolate.interp1d(cnts, volts)

    log.error('Could not load calibration file: %s' % self.calibrationFile)

  def start(self):
    self.run = True
    self.runThread = threading.Thread(target=self.mainThread)
    self.runThread.start()

  def stop(self):
    self.disableRelay()
    self.run = False
    self.runThread.join()

  def convertData(self, values):
    return self.calibrationFunction(values)

  def dumbConvert(self, values):
    #return [float(x) / 1024.0 * 5.0 for x in values]
    return copy.deepcopy(values)

  def mainThread(self):
    while self.run:
      log.debug('Main Thread acquiring lock')
      self.readyLock.acquire()
      self._readValues()
      if self.values is not None:
        self.ready = True
        self.readyLock.notify_all()
      log.debug('Main Thread releasing lock')
      self.readyLock.release()
      time.sleep(0.5) #Give some time for other threads to pick up data

  def _readValues(self):
    x = self.port.readline()
    now = datetime.datetime.now()
    x = x.decode().strip()
    try:
      vals = json.loads(x)
      with self.updateLock:
        self.values = now, self.convertData(vals['volts'])
        self.relay = vals['relay']
    except:
      log.error('Problem when decoding serial data')

  def waitReady(self):
    while not self.ready:
      log.debug('WaitReady Acquire lock')
      self.readyLock.acquire()
      log.debug('WaitReady Wait lock')
      self.readyLock.wait()
      log.debug('WaitReady Release lock')
      self.readyLock.release()
      log.debug('WaitReady Done')

  def readValues(self):
    res = []
    with self.updateLock:
      for channel in self.channelList:
        res.append(self.values[1][channel])

  def readValuesWait(self):
    res = []
    self.readyLock.acquire()
    self.readyLock.wait()
    with self.updateLock:
      for channel in self.channelList:
        res.append(self.values[1][channel])
    self.readyLock.release()

    return self.values[0], res

  def enableRelay(self):
    self.port.write(b'e')

  def disableRelay(self):
    self.port.write(b'o')
    self.port.write(b'o')
    self.port.write(b'o')
    self.port.write(b'o')
    self.port.write(b'o')


if __name__ == '__main__':
  log.info('Starting')
  vMeter = ArduVoltmeter(channelList=[0, 1, 2, 3, 4, 5], calibrationFile='calibration-all.json', port=serial.Serial('COM4', 9600))
  vMeter.start()
  vMeter.waitReady()
  log.info('Meter Ready')

  vMeter.enableRelay()
  for i in range(0,10):
    print(vMeter.readValuesWait())
    #time.sleep(5)
  vMeter.disableRelay()
  vMeter.stop()
