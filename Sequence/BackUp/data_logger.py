
# influx-db data logger
from influxdb import InfluxDBClient
db_client = InfluxDBClient('192.168.1.13',8086,database='mingming')

def data_logger(data):
    db_client.write_points(data)