import os
import numpy as np
import matplotlib.pyplot as plt
import time
import pandas as pd

cmd1='microwave_frequency_scan.py'
cmd = 'conda activate artiq-main && artiq_run '+cmd1

os.system(cmd)

time.sleep(0.1)
data = np.load('microwave.npy')
pd_data = pd.DataFrame(data)
writer = pd.ExcelWriter('A.xlsx')		# 写入Excel文件
data.to_excel(writer, 'page_1', float_format='%.5f')		# ‘page_1’是写入excel的sheet名
writer.save()
writer.close()

plt.figure(1)
plt.bar(data[0],data[1],width=0.0005)
plt.title('microwave frequenc -- accuracy')

plt.figure(2)
plt.bar(data[0],data[2],width=0.0005)
plt.title('microwave frequenc -- count')

plt.show()