from datetime import datetime


class Event:
    """
    Represents an internal Aegis OS event.
    """

    def __init__(self, event_type, data=None):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"Event(type={self.event_type}, time={self.timestamp})"


class EventBus:
    """
    Internal communication system.

    Responsible for publishing and distributing events.
    """

    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)

        print(f"Event published: {event.event_type}")

    def history(self):
        return self.events
