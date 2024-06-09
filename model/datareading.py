from datetime import datetime

from model.datatype import DataType


class DataReading:
    def __init__(self, raw_data):
        self.id = raw_data["id"]
        self.type = DataType(int(raw_data["type"]))
        self.value = raw_data["data"]
        dt = datetime.now()
        self.timestamp = dt.strftime('%Y-%m-%d %H:%M:%S %Z')

    def __repr__(self):
        return f"{{timestamp: {self.timestamp}, id: {self.id}, type: {self.type.name}, value: {self.value}}}"
