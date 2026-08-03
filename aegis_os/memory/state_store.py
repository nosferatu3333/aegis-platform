import json
import os


class StateStore:
    """
    Persistent storage for Aegis cognitive state.
    """

    def __init__(self, path="aegis_state.json"):

        self.path = path

    def save(self, state):

        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=4)

    def load(self):

        if not os.path.exists(self.path):
            return {}

        with open(self.path, encoding="utf-8") as file:
            return json.load(file)
