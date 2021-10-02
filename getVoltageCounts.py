import json
from scipy import interpolate


with open('calibration.json') as calibfile:
  data = json.load(calibfile)

v_to_c = interpolate.interp1d(data['volts'], data['counts'])
c_to_v = interpolate.interp1d(data['counts'], data['volts'])

print(v_to_c(4.27))
print(v_to_c(2.95))