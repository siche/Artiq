
import matplotlib.pyplot as plt  
from image_processing import *

img = window_capture2()
plt.figure()
plt.subplot(121)
plt.imshow(img)

img2 = window_capture()
plt.subplot(122)    
plt.imshow(img)
plt.show()