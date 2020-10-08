
import numpy as np
# import matplotlib.pyplot as plt
from wlm_web import wlm_web
import os
import time

wm = wlm_web()
repeat_number = 3
data = np.zeros((4,repeat_number))

cmd = "start_sequence.bat"

for i in range(repeat_number):

    wave_lens = wm.get_data()
    laser_370 = round(wave_lens[1],6)
    laser_935 = round(wave_lens[3],6)

    data[0][i] = laser_370
    data[1][i] = laser_935

    os.system(cmd)
    time.sleep(2)
    count_data = np.load('data.npy')

    data[2][i] = count_data[0]
    data[3][i] = count_data[1]

# sort according the ascending order of the first row
# plt_data = data[:,np.lexsort(-data)]
# plt.plot(data[0][:],data[3][:])

# 对重复的波长进行合并，将计数取为二者的均值
laser_370 = np.unique(data[0][:])
lens_num = np.size(laser_370)
plt_data = np.zeros((2,lens_num))

for i in range(lens_num):
    temp = laser_370[i]
    index = data[0][:]==temp

    temp_data = data[0][:]
    plt_data[0][i] = temp_data[index].mean()

    temp_data2 = data[3][:]
    plt_data[1][i] = temp_data2[index].mean()

# 为了绘图方便对数据做一定整合。
xdata = 1000000*(plt_data[0,:] - 369.5270)
print(xdata)
print(plt_data[1,:])
"""
import matplotlib.pyplot as plt
plt.figure(1)
plt.title('Count-370')
plt.plot(xdata,plt_data[1,:])
#plt.plot(plt_data[0][:], plt_data[1][:])
plt.show()
"""