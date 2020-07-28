
import os
import time

t1 = time.time()
os.system(r'timeout 1')
t2 = time.time()
print('time cost:%.2f' %(t2-t1))