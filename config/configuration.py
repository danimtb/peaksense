import os
import yaml

from model.node import Node


class Configuration:

    def __init__(self, base_path):
        self.nodes = None
        self.path = os.path.join(os.getcwd(), "configuration.yml")
        with open(self.path, 'r') as file:
            self.config = yaml.safe_load(file)

    def get(self, key):
        return self.config.get(key)

    def get_nodes(self):
        if not self.nodes:
            nodes = []
            for n in self.config["nodes"]:
                streams = n["streams"] if "streams" in n.keys() else []
                nodes.append(Node(n["id"], n["name"], streams))
        return self.nodes

    def get_node_for_id(self, id):
        for node in self.nodes:
            if node.id == id:
                return node
        return None
