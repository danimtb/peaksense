import aiofiles
import aiohttp
import os
from abc import abstractmethod


class Streams:

    def __init__(self, configuration):
        self.streams = {}
        for stream_id in ["csv", "adafruit", "homeassistant"]:
            self.streams[stream_id] = Stream.create(stream_id, configuration.get(stream_id))

    def get(self, stream_id):
        return self.streams.get(stream_id)


class Stream:

    @staticmethod
    def create(id, config):
        if id == "adafruit":
            return AdafruitStream(config)
        elif id == "csv":
            return CsvStream(config)
        elif id == "homeassistant":
            return HomeassistantStream(config)
        else:
            raise Exception(f"Stream type {id} does not exist")

    @staticmethod
    def _check_id(node, data_reading):
        if node.id != data_reading.id:
            raise Exception("Different ids")

    @abstractmethod
    async def save_data(self, node, data_reading):
        raise NotImplementedError()


class AdafruitStream(Stream):
    id = "adafruit"
    url = "https://io.adafruit.com/api/v2/"

    def __init__(self, config):
        self.username = config.get("username")
        self.key = config.get("key")

    def get_feed_name(self, node, data_reading):
        self._check_id(node, data_reading)
        return f"{node.name}.{node.name}-{data_reading.type.name.lower()}"

    async def save_data(self, node, data_reading):
        async with aiohttp.ClientSession() as session:
            print("update feed")
            feed_name = self.get_feed_name(node, data_reading)
            feed_url = f"{self.url}/{self.username}/feeds/{feed_name}/data"
            async with session.post(feed_url, json={"value": data_reading.value},
                                    headers={"X-AIO-Key": self.key}) as resp:
                await resp.text()


class CsvStream(Stream):
    id = "csv"

    def __init__(self, config):
        self.folder = os.path.join(os.getcwd(), config.get("folder"))

    def get_datalog_name(self, node, data_reading):
        self._check_id(node, data_reading)
        return f"{node.name}-{data_reading.type.name.lower()}"

    async def save_data(self, node, data_reading):
        datalog_name = self.get_datalog_name(node, data_reading)
        datalog_filepath = os.path.join(self.folder, f"{datalog_name}.csv")
        print(f"save data to {datalog_filepath}")
        row = f"{data_reading.timestamp},{data_reading.value}\n"
        open_mode = "a" if os.path.exists(datalog_filepath) else "w"

        async with aiofiles.open(datalog_filepath, open_mode, newline='', encoding='UTF8') as f:
            print("save to csv")
            if open_mode == "w":  # Write header
                await f.write("timestamp,{}\n".format(data_reading.type.name.lower()))
            await f.write(row)


class HomeassistantStream(Stream):
    id = "homeassistant"

    def __init__(self, config):
        # https://your-home-assistant:8123/api/webhook/some_hook_id
        self.url = f"{config.get('url')}/api/webhook"

    def get_webhook_id(self, node, data_reading):
        self._check_id(node, data_reading)
        return f"{node.name}-{data_reading.type.name.lower()}"

    async def save_data(self, node, data_reading):
        # curl -X POST -d 'key=value&key2=value2' https://your-home-assistant:8123/api/webhook/some_hook_id
        async with aiohttp.ClientSession() as session:
            print("update home assistant")
            webhook_id = self.get_webhook_id(node, data_reading)
            webhook_url = f"{self.url}/{webhook_id}"
            data = {data_reading.type.name.lower(): data_reading.value}
            async with session.post(webhook_url, data=data) as resp:
                await resp.text()
