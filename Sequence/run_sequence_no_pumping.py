import os
import numpy as np
import matplotlib.pyplot as plt
import time
cmd1='sequence_no_pumping.py'
cmd = 'conda activate artiq-main && artiq_run '+cmd1

os.system(cmd)

time.sleep(0.1)
data = np.load('microwave.npy')

plt.figure(1)
plt.bar(data[0],data[1],width=5)
plt.title('microwave time -- accuracy')

plt.figure(2)
plt.bar(data[0],data[2],width=5)
plt.title('microwave time -- count')

plt.show()