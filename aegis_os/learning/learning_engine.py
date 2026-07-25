from aegis_os.learning.strategy_memory import StrategyMemory
from aegis_os.learning.pattern_detector import PatternDetector
from aegis_os.memory.memory_manager import MemoryManager


class LearningEngine:
    """
    Converts experiences into learning
    and stores knowledge persistently.
    """

    def __init__(
        self,
        memory_manager=None
    ):

        self.memory = StrategyMemory()

        self.detector = PatternDetector()

        self.memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager()
        )


    def learn(self, experience):

        patterns = self.detector.detect(
            [experience]
        )


        self.memory_manager.remember_experience(
            experience
        )


        self.memory_manager.save_state(
            {
                "last_observation":
                    experience,

                "candidate_patterns":
                    patterns,

                "cross_run_validation":
                    False,

                "promoted":
                    False
            }
        )


        return {

            "candidate_patterns":
                patterns,

            "pattern_count":
                len(
                    patterns
                ),

            "cross_run_validation":
                False,

            "promoted":
                False

        }
