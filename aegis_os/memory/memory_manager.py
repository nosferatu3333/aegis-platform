from aegis_os.memory.experience_repository import ExperienceRepository
from aegis_os.memory.state_store import StateStore


class MemoryManager:
    """
    Coordinates Aegis persistent memory systems.
    """

    def __init__(self, state_path="aegis_state.json"):

        self.state_store = StateStore(state_path)

        self.experience_repository = ExperienceRepository()

    def save_state(self, state):

        self.state_store.save(state)

    def load_state(self):

        return self.state_store.load()

    def remember_experience(self, experience):

        self.experience_repository.add(experience)

    def get_experiences(self):

        return self.experience_repository.all()
