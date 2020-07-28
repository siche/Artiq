
# save data file

import pandas as pd
import numpy as np
import time

def save_file(data,pro_name=''):
    time_now = time.strftime("%Y-%m-%d-%H-%M")
    xlsx_name = 'data\\'+ pro_name + '-' + time_now + '.xlsx'
    pd_data = pd.DataFrame(data)
       
    writer = pd.ExcelWriter(xlsx_name)
    pd_data.to_excel(writer, 'sheet1', float_format='%.5f')
    writer.save()
    writer.close()
