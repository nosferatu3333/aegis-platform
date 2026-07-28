from aegis_os.core.events import EventBus


class Runtime:
    """
    Aegis OS execution environment.

    Responsible for managing the system lifecycle,
    runtime state and internal communication.
    """

    def __init__(self, kernel):
        self.kernel = kernel
        self.state = "initialized"
        self.event_bus = EventBus()

    def start(self):
        self.state = "running"

        print("Aegis Runtime started.")
        print("Runtime state:", self.state)

        self.event_bus.publish(self.kernel.create_event("SYSTEM_STARTED"))
