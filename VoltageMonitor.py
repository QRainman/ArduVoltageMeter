import serial
import json
import datetime
import requests
import pytz as tz
import traceback


class VoltageDataLogger:
  def __init__(self, numChannels):
    self.integral = [0.0]*numChannels
    self.prevTime = 0
    self.numChannels = numChannels

  def convertData(self, data):
    return [float(x) / 1024.0 * 5.0 for x in data]

  def sendData(self, battery, data, time):
    session = requests.session()
    session.trust_env = False

    lineString = "batdischarge,battery=%s " % battery
    for i in range(self.numChannels):
      lineString += "V_%d=%f," % (i, data[i])
    for i in range(self.numChannels):
      lineString += "iV_%d=%f," % (i, self.integral[i])

    lineString = lineString[:-1]
    timestamp = time.timestamp()
    utc_time = int(timestamp) * 1000000000
    lineString += ' %d' % utc_time
    print(lineString)
  
    try:
      #response = session.post('http://192.168.178.220:8090/telegraf', lineString)
      #print(response)
      pass
    except:
      print('Failed to submit data string %s' % lineString)
      print(traceback.format_exc())

  def integrate(self, data, time):
    if self.prevTime == 0:
      self.prevTime = time
      return

    timeDiff = (time-self.prevTime).total_seconds()

    for i in range(self.numChannels):
      self.integral[i] = self.integral[i] + (float(data[i]) * float(timeDiff) / 3600.0)
    self.prevTime = time

def mainLoop():
  ser = serial.Serial('/dev/ttyACM0', 9600)

  vl = VoltageDataLogger(1)

  while True:
    x = ser.readline()
    now = datetime.datetime.now()
    x = x.decode().strip()
    vals = json.loads(x)
    data = vl.convertData(vals["volts"])
    vl.integrate(data, now)
    vl.sendData('101876', data, now)


if __name__ == '__main__':
  mainLoop()
