class Plan:
    """
    Represents an execution strategy.

    A plan contains a goal and a sequence
    of tasks required to achieve it.
    """

    def __init__(self, goal, tasks):
        self.goal = goal
        self.tasks = tasks
        self.status = "created"
        self.tasks_executed = False


    def activate(self):
        self.status = "active"


    def complete(self):
        self.status = "completed"
        self.tasks_executed = True


    def mark_assignment_observed(self):

        self.status = "partial"

        self.tasks_executed = False


    def __repr__(self):
        return (
            f"Plan(goal={self.goal}, "
            f"tasks={self.tasks}, "
            f"status={self.status})"
        )
