class CollaborationEngine:
    """
    Creates temporary agent teams
    for complex objectives.
    """

    def __init__(self):

        self.teams = []

        self._members = {}

        self._next_team_id = 1


    def create_team(
        self,
        objective,
        agents
    ):

        if not agents:

            raise ValueError(
                "A collaboration team requires at least one agent"
            )


        team_id = self._next_team_id

        self._next_team_id += 1


        team = {

            "team_id":
                team_id,

            "objective": objective,

            "agents": [
                agent.name
                for agent in agents
            ],

            "status":
                "created",

            "simulation":
                True

        }


        self._members[team_id] = tuple(
            agents
        )


        self.teams.append(
            team
        )


        return team


    def execute(
        self,
        team
    ):

        team_id = team.get(
            "team_id"
        )

        members = self._members.get(
            team_id
        )


        if members is None:

            raise ValueError(
                "Unknown collaboration team"
            )


        objective = team.get(
            "objective",
            "Unspecified objective"
        )

        results = []


        for agent in members:

            results.append(
                {

                    "agent":
                        agent.name,

                    "result":
                        agent.execute(
                            objective
                        )

                }
            )


        team["status"] = "completed"


        return {

            "team_id":
                team_id,

            "objective":
                objective,

            "status":
                "completed",

            "results":
                results,

            "simulation":
                True

        }


    def get_teams(self):

        return [
            team.copy()
            for team in self.teams
        ]
