from dataclasses import dataclass

@dataclass(frozen=True)
class EntropyPolicy:
    base_temperature: float = 0.0
    step: float = 0.05
    max_temperature: float = 0.3
    max_retries: int = 6

    def temperature_for_attempt(self, attempt: int) -> float:
        t = self.base_temperature + attempt * self.step
        return min(t, self.max_temperature)
