import csv
import json
import os
import signal
from datetime import datetime
from enum import Enum

import aiofiles
import aiohttp
import asyncio
import yaml
import serial_asyncio


class DataType(Enum):
    STATUS = 0  # Status
    TEMPERATURE = 1  # Temperature
    TEMPERATURE2 = 2  # Temperature #2
    HUMIDITY = 3  # Relative Humidity
    PRESSURE = 4  # Atmospheric Pressure
    LIGHT = 5  # Light (lux)
    VOLTAGE = 16  # Voltage
    LATITUDE = 21  # GPS Latitude
    LONGITUDE = 22  # GPS Longitude
    ALTITUDE = 23  # GPS Altitude
    HDOP = 24  # GPS HDOP
    SPEED = 999  # GPS Speed
    SPEED_LATITUDE_LONGITUDE_ALTITUDE_HDOP = 1000  # GPS Latitude, Longitude, Altitude, HDOP


class DataReading:
    def __init__(self, raw_data):
        self.id = raw_data["id"]
        self.type = DataType(int(raw_data["type"]))
        self.value = raw_data["data"]
        dt = datetime.now()
        self.timestamp = dt.strftime('%Y-%m-%d %H:%M:%S %Z')

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


async def save_data(session, nodes, data_reading, username, key):
    node = get_node_for_id(nodes, data_reading.id)
    datalog_name = node.get_datalog_name(data_reading)
    datalog_filepath = os.path.join(os.getcwd(), f"{datalog_name}.csv")
    row = [data_reading.timestamp, data_reading.value]
    open_mode = "a" if os.path.exists(datalog_filepath) else "w"

    async with aiofiles.open(datalog_filepath, open_mode, newline='', encoding='UTF8') as f:
        writer = csv.writer(await f.__anext__())
        if open_mode == "w":  # Write header
            writer.writerow(["timestamp", data_reading.type.name.lower()])
        
        feed_name = node.get_feed_name(data_reading)
        feed_url = f"https://io.adafruit.com/api/v2/{username}/feeds/{feed_name}/data"
        async with session.post(feed_url, json={"value": data_reading.value}, headers={"X-AIO-Key": key}) as resp:
            await resp.text()

        writer.writerow(row)


def get_node_for_id(nodes, id):
    for node in nodes:
        if node.id == id:
            return node
    return None


def sigint_handler(signum, frame):
    global loop
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


async def read_serial_data(loop, serial_port, serial_baud_rate, nodes, username, key):
    reader, _ = await serial_asyncio.open_serial_connection(url=serial_port, baudrate=serial_baud_rate)
    async with aiohttp.ClientSession() as session:
        while loop:
            try:
                line = await reader.readline()
                line = line.decode('utf-8').rstrip()
                print(line)
                if not line.startswith("["):
                    continue
                datas = json.loads(line)
                for data in datas:
                    dr = DataReading(data)
                    print(dr)
                    await save_data(session, nodes, dr, username, key)
                print("")
            except Exception as e:
                print(f"Error: {e}")


loop = True

if __name__ == '__main__':
    print("Initializing PeakSense...")

    signal.signal(signal.SIGTERM, sigint_handler)
    config = get_configuration()
    print(f"Configuration:\n\n{config}")
    nodes = config_nodes(config)
    print(f"Nodes: {nodes}")
    serial_port = config["serial"]["port"]
    serial_baud_rate = config["serial"]["baud_rate"]
    username = config["adafruit"]["username"]
    key = config["adafruit"]["key"]

    try:
        asyncio.run(read_serial_data(loop, serial_port, serial_baud_rate, nodes, username, key))
    except KeyboardInterrupt:
        print("Closing PeakSense...")
