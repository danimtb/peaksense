import csv
import json
import os
import signal
import yaml
from datetime import datetime
from enum import Enum

from Adafruit_IO import Client
import serial


class DataType(Enum):
    STATUS =         0  # Status
    TEMPERATURE =           1  # Temperature
    TEMPERATURE2 =          2  # Temperature #2
    HUMIDITY =       3  # Relative Humidity
    PRESSURE =       4  # Atmospheric Pressure
    LIGHT =          5  # Light (lux)
#define SOIL_T          6  // Soil Moisture
#define SOIL2_T         7  // Soil Moisture #2
#define SOILR_T         8 // Soil Resistance
#define SOILR2_T        9 // Soil Resistance #2
#define OXYGEN_T        10 // Oxygen
#define CO2_T           11 // Carbon Dioxide
#define WINDSPD_T       12 // Wind Speed
#define WINDHDG_T       13 // Wind Direction
#define RAINFALL_T      14 // Rainfall
#define MOTION_T        15 // Motion
    VOLTAGE =        16  # Voltage
#define VOLTAGE2_T      17 // Voltage #2
#define CURRENT_T       18 // Current
#define CURRENT2_T      19 // Current #2
#define IT_T            20 // Iterations
    LATITUDE =      21 # GPS Latitude
    LONGITUDE =     22 # GPS Longitude
    ALTITUDE =      23 # GPS Altitude
    HDOP =          24 # GPS HDOP
    SPEED =         999 # GPS Speed
    SPEED_LATITUDE_LONGITUDE_ALTITUDE_HDOP =               1000 # GPS Latitude, Longitude, Altitude, HDOP
#define LEVEL_T         25 // Fluid Level
#define UV_T            26 // UV
#define PM1_T           27 // 1 Particles
#define PM2_5_T         28 // 2.5 Particles
#define PM10_T          29 // 10 Particles
#define POWER_T         30 // Power
#define POWER2_T        31 // Power #2
#define ENERGY_T        32 // Energy
#define ENERGY2_T       33 // Energy #2


class DataReading:
    id = None
    type = None
    value = None
    timestamp = None

    def __init__(self, raw_data):
        self.id = raw_data["id"]
        self.type = DataType(int(data["type"]))
        self.value = data["data"]
        dt = datetime.now()
        self.timestamp = datetime.timestamp(dt)

    def __repr__(self):
        return f"{{timestamp: {self.timestamp}, id: {self.id}, type: {self.type.name}, value: {self.value}}}"


class Node:

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def _check_id(self, data_reading):
        if self.id != data_reading.id:
            raise Exception("Different ids")

    def get_feed_name(self, data_reading):
        self._check_id(data_reading)
        return f"{self.name}.{self.name}-{data_reading.type.name.lower()}"

    def get_datalog_name(self, data_reading):
        self._check_id(data_reading)
        return f"{self.name}-{data_reading.type.name.lower()}"


def save_data(nodes, data_reading, username, key):
    node = get_node_for_id(nodes, data_reading.id)
    datalog_name = node.get_datalog_name(data_reading)
    aio = Client('danimtb', 'aio_vgWw33FaK8te7s2oHfuTk6OOmu9W')
    datalog_filepath = os.path.join(os.getcwd(), f"{datalog_name}.csv")
    row = [data_reading.timestamp, data_reading.value]
    open_mode = "a" if os.path.exists(datalog_filepath) else "w"
    with open(datalog_filepath, open_mode, newline='', encoding='UTF8') as f:
        writer = csv.writer(f)
        if open_mode == "w":  # Write header
            writer.writerow(["timestamp", data_reading.type.name.lower()])
        feed = aio.feeds(node.get_feed_name(data_reading))
        aio.send_data(feed.key, data_reading.value)

        writer.writerow(row)
        f.close()


def get_node_for_id(nodes, id):
    for node in nodes:
        if node.id == id:
            return node
    return None

def sigint_handler(signum, frame):
    loop = False

def get_configuration():
    config_path = os.path.join(os.getcwd(), "configuration.yml")
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def config_nodes(config):
    nodes = []
    for n in config["nodes"]:
        nodes.append(Node(n["id"], n["name"]))
    return nodes

loop = True


if __name__ == '__main__':
    print("Intializing PeakSense...")

    signal.signal(signal.SIGTERM, sigint_handler)
    config = get_configuration()
    print(f"Configuration:\n\n{config}")
    nodes = config_nodes(config)
    print(f"Nodes: ${nodes}")
    serial_port = config["serial"]["port"]
    serial_baud_rate = config["serial"]["baud_rate"]
    username = config["adafruit"]["username"]
    key = config["adafruit"]["key"]

    with serial.Serial() as ser:
        ser.baudrate = serial_baud_rate
        ser.port = serial_port
        ser.open()
        while ser.is_open and loop:
            try:
                line = str(ser.readline().decode('utf-8')).rstrip()
                print(line)
                if not line.startswith("["):
                    continue
                #input()
                datas = json.loads(line)
                for data in datas:
                    dr = DataReading(data)
                    print(dr)
                    save_data(nodes, dr, username, key)
                print("")
            except Exception as e:
                print(f"Error: {e}")
        ser.close()
    print("Closing PeakSense...")
