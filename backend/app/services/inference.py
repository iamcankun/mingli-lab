import re
from typing import Any


VARIABLE_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


class PromptRenderError(ValueError):
    pass


def render_prompt(template: str, variables: dict[str, Any]) -> str:
    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in variables:
            raise PromptRenderError(f"Unresolved prompt variable: {key}")
        return str(variables[key])

    return VARIABLE_RE.sub(replace, template)

