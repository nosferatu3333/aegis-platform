from aegis_os.core.cognitive_runtime import CognitiveRuntime
from aegis_os.core.events import Event


class Kernel:
    """
    Aegis OS central cognitive layer.
    """

    def __init__(self):

        self.name = "Aegis Kernel"
        self.version = "0.3.0"
        self.state = "created"

        self.cognitive_runtime = CognitiveRuntime()

    def boot(self):

        self.state = "running"

        print(f"{self.name} v{self.version}")
        print("Kernel state:", self.state)
        print("Aegis OS online.")

        self.cognitive_runtime.start()

    def create_event(self, event_type, data=None):

        return Event(event_type, data)

    def process_goal(self, goal):

        return self.cognitive_runtime.process_goal(goal)
