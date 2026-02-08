from dataclasses import dataclass, field
from typing import Dict

@dataclass
class FileEntropyState:
    base_temperature: float = 0.0
    step: float = 0.05
    max_temperature: float = 0.3
    attempts: Dict[str, int] = field(default_factory=dict)

    def temperature_for(self, path: str) -> float:
        attempt = self.attempts.get(path, 0)
        t = self.base_temperature + attempt * self.step
        return min(t, self.max_temperature)

    def record_failure(self, path: str) -> None:
        self.attempts[path] = self.attempts.get(path, 0) + 1
