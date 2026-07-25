from aegis_os.planning.plan import Plan
from aegis_os.planning.task_decomposer import TaskDecomposer


class PlanningEngine:
    """
    Converts objectives into executable plans.
    """

    def __init__(self):

        self.decomposer = TaskDecomposer()


    def create_plan(self, goal):

        tasks = self.decomposer.decompose(
            goal
        )

        return Plan(
            goal,
            tasks
        )