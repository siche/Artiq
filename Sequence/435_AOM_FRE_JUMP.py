import os, time

AOM_FRES = [200, 240]
flag = False
while True:
    AOM_FRE = AOM_FRES[flag]
    cmd = "python dds.py " + str(AOM_FRE)
    os.system(cmd)
    flag = not flag
    time.sleep(2)
