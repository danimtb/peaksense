
class Node:
    def __init__(self, id, name, streams):
        self.id = id
        self.name = name
        self.streams = streams

    def _check_id(self, data_reading):
        if self.id != data_reading.id:
            raise Exception("Different ids")

    def get_feed_name(self, data_reading):
        self._check_id(data_reading)
        return f"{self.name}.{self.name}-{data_reading.type.name.lower()}"

    def get_datalog_name(self, data_reading):
        self._check_id(data_reading)
        return f"{self.name}-{data_reading.type.name.lower()}"
