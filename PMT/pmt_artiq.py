from subprocess import Popen, PIPE, STDOUT
import numpy as np
import matplotlib.pyplot as plt

POINTS = 100

data = [None] * POINTS
time = np.arange(POINTS)*0.1
time_now = 0.0

plt.ion()
fig, = plt.plot(time, data)
ax = plt.gca()
plt.xlabel('Time(s)')
plt.ylabel('Photon Count')

if __name__ == '__main__':

    shell_cmd = ['cmd','run_get_data']
    data_len = 0
    rank = 0
    # cmd = shlex.split(shell_cmd)
    p = Popen(shell_cmd, stdout=PIPE, bufsize=1, shell=False)

    mean_count = 0
    num = 0
    for line in iter(p.stdout.readline, 'b'):
        count = 0

        try:
            count = np.float(line)
        except:
            pass

        if num < 10:
            num = num + 1
            mean_count = mean_count + count
            continue
       
       # get data
        mean_count = mean_count/10
        data = data[1:] + [mean_count]

        # reset data
        num = 0
        mean_count = 0
       
       # update figure 
        ax.relim()
        ax.autoscale_view(True, True, True)
        fig.set_ydata(data)
        plt.draw()
        plt.pause(1e-17)
    p.stdout.close()
    p.wait()
