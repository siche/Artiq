
# test fit
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def fit_func(x,a,b,c):
    return a*np.sin(0.0116687*x+b)+c

# function fitting
data = np.load('microwave.npy')
popt,pcov = curve_fit(fit_func,data[0],data[1])
a=popt[0]
b=popt[1]
c=popt[2]
# d=popt[3]
print(a)
print(b)
print(c)
print('rabi frequency:%skHz' % (1000*b))
x_fit = np.arange(min(data[0]),max(data[0]),0.1)
y_fit = fit_func(x_fit,a,b,c)

plt.figure(1)
plt.scatter(data[0],data[1])
plt.plot(x_fit,y_fit,'r')
plt.show()