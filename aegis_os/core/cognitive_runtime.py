from aegis_os.cognition.orchestrator import CognitiveOrchestrator


class CognitiveRuntime:
    """
    Connects the Aegis runtime
    with the cognitive architecture.
    """

    def __init__(self):

        self.orchestrator = CognitiveOrchestrator()

        self.state = "initialized"


    def start(self):

        self.state = "running"

        print(
            "Cognitive Runtime started."
        )


    def process_goal(self, goal):

        if self.state != "running":

            raise RuntimeError(
                "Cognitive Runtime is not running"
            )


        print(
            f"Cognitive goal received: {goal}"
        )


        result = self.orchestrator.process(
            goal
        )


        print(
            "Cognitive cycle completed."
        )


        return result