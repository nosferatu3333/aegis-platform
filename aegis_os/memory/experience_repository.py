class ExperienceRepository:
    """
    Stores cognitive experiences.
    """

    def __init__(self):

        self.experiences = []

    def add(self, experience):

        self.experiences.append(experience)

    def all(self):

        return self.experiences
