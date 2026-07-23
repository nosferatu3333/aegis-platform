class BaseAgent:
    """
    Fundamental cognitive unit in Aegis OS.

    Every specialized agent inherits from this class.
    """

    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.state = "initialized"
        self.memory = []

    def activate(self):
        self.state = "active"

        print(
            f"Agent {self.name} activated."
        )

    def process(self, task):
        """
        Executes an assigned task.

        To be extended by specialized agents.
        """

        result = {
            "agent": self.name,
            "task": task,
            "status": "completed"
        }

        self.memory.append(result)

        return result

    def remember(self, information):
        self.memory.append(information)