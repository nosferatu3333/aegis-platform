from aegis_os.core.events import Event


class Kernel:
    """
    Aegis OS central cognitive layer.
    """

    def __init__(self):
        self.name = "Aegis Kernel"
        self.version = "0.1.0"
        self.state = "created"

    def boot(self):
        self.state = "running"

        print(f"{self.name} v{self.version}")
        print("Kernel state:", self.state)
        print("Aegis OS online.")

    def create_event(self, event_type, data=None):
        return Event(
            event_type,
            data
        )