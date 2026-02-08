from pydantic import BaseModel
from typing import get_origin, get_args, List
import inspect

def walk_schema(model: type[BaseModel], indent: int = 0) -> list[str]:
    lines = []
    pad = "  " * indent

    for name, field in model.model_fields.items():
        tp = field.annotation

        if inspect.isclass(tp) and issubclass(tp, BaseModel):
            lines.append(f"{pad}{name}:")
            lines.extend(walk_schema(tp, indent + 1))

        elif get_origin(tp) in (list, List):
            sub = get_args(tp)[0]
            lines.append(f"{pad}{name}:")
            lines.append(f"{pad}  -")
            if inspect.isclass(sub) and issubclass(sub, BaseModel):
                lines.extend(walk_schema(sub, indent + 2))
            else:
                lines.append(f"{pad}    <value>")

        else:
            lines.append(f"{pad}{name}: <value>")

    return lines
