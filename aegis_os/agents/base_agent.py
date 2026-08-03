class BaseAgent:
    """
    Base class for all Aegis agents.
    """

    def __init__(self, name, role):

        self.name = name

        self.role = role

        self.state = "initialized"

    def start(self):

        self.state = "active"

    def execute(self, task):

        raise NotImplementedError("Agent must implement execute method")

    def __repr__(self):

        return f"Agent(name={self.name}, role={self.role}, state={self.state})"
