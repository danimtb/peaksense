import json
import os
import signal

import asyncio
import serial_asyncio


from config.configuration import Configuration
from model.datareading import DataReading
from streams.streams import Streams


def sigint_handler(signum, frame):
    global loop
    loop = False


async def update_node_streams(configuration, streams):
    while True:
        if data_reading_buffer:
            data_reading = data_reading_buffer.pop(0)
            node = configuration.get_node_for_id(data_reading.id)
            for stream_id in node.streams:
                stream = streams.get(stream_id)
                stream.save_data(node, data_reading)
        await asyncio.sleep(1)  # Adjust the sleep duration as needed


async def read_from_serial(serial_port, serial_baud_rate):
    reader, _ = await serial_asyncio.open_serial_connection(url=serial_port, baudrate=serial_baud_rate)
    while True:
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
                data_reading_buffer.append(dr)
            print("")
        except Exception as e:
            print(f"Error: {e}")
        except asyncio.CancelledError:
            break


loop = True
data_reading_buffer = []


async def main():
    print("Initializing PeakSense...")
    signal.signal(signal.SIGTERM, sigint_handler)
    configuration = Configuration(os.getcwd())
    print(f"Configuration:\n\n{configuration.config}")
    nodes = configuration.get_nodes()
    print(f"Nodes: {nodes}")
    serial_port = configuration.get("serial")["port"]
    serial_baud_rate = configuration.get("serial")["baud_rate"]
    print(f"Serial connection:\n\t- Port: {serial_port}\n\t- Baud rate: {serial_baud_rate}")
    streams = Streams(configuration)

    tasks = [
        asyncio.create_task(read_from_serial(serial_port, serial_baud_rate)),
        asyncio.create_task(update_node_streams(configuration, streams))
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted")
