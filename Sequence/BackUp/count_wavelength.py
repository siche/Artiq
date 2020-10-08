from wlm_web import wlm_web
import numpy as np
import os
import time
from toptica_laser import toptica_laser

laser1 = toptica_laser('192.168.1.61')
init_vol = laser1.get_voltage()
old_vol = init_vol - 0.005
wm = wlm_web()
repeat_number = 10
data = np.zeros((4, repeat_number))

cmd = "conda activate artiq-main && artiq_run sequence_only_cooling.py"


for i in range(repeat_number):
    
    wave_lens = wm.get_data()
    laser_370 = round(wave_lens[1], 6)
    laser_935 = round(wave_lens[3], 6)

    data[0][i] = laser_370
    data[1][i] = laser_935

    os.system(cmd)
    print("370 wavelength:%s" % laser_370)
    count_data = np.load('data.npy')

    data[2][i] = count_data[0]
    data[3][i] = count_data[1]
    # old_vol = laser1.get_voltage()
    new_vol = old_vol+0.001*i
    laser1.set_voltage(new_vol)
    time.sleep(0.1)
laser1.set_voltage(old_vol)
# sort according the ascending order of the first row
# plt_data = data[:,np.lexsort(-data)]
# plt.plot(data[0][:],data[3][:])

# 对重复的波长进行合并，将计数取为二者的均值
laser_370 = np.unique(data[0][:])
lens_num = np.size(laser_370)
plt_data = np.zeros((3, lens_num))

for i in range(lens_num):
    temp = laser_370[i]
    index = data[0][:] == temp

    temp_data = data[0][:]
    plt_data[0][i] = int(1000000*(temp_data[index].mean()-369.5260))

    temp_data2 = data[3][:]
    plt_data[1][i] = temp_data2[index].mean()

    # accuracy
    temp_data3 = data[2,:]
    plt_data[2][i] = temp_data3[index].mean()
# 为了绘图方便对数据做一定整合。
xdata = plt_data[0,:]
ydata = plt_data[1,:]
ydata2 = plt_data[2,:]
print(xdata)
print(ydata)

import matplotlib.pyplot as plt
fig = plt.figure(1)
# 绘制双轴图像
ax = fig.add_subplot(111)
plt.title('Count-370')
ax.plot(xdata, ydata)
ax.bar(xdata, ydata)
plt.grid(axis='y')
ax1 = ax.twinx()
ax1.plot(xdata, ydata2/10,color='C8')
"""
plt.bar(xdata,ydata,0.4)
plt.figure(2)
plt.plot(xdata, ydata2/10)
plt.bar(xdata,ydata2/10,0.2)
plt.grid(axis='y')
"""
plt.show()
