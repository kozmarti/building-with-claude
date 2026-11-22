"""The prompt under test.

The task: a "data-cleaning helper" that answers each request with exactly one
artifact - a Python function, a JSON object, or a regular expression - and
nothing else. Strict output makes it easy to grade with code as well as with
a model.

To iterate: add a new version below, point CURRENT_VERSION at it, re-run the
eval and compare scores.
"""

PROMPTS = {
    "v1": """Please solve the following task:

{task}
""",
    "v2": """You are a data-cleaning helper.

Solve the task below. Reply with ONLY the solution, in the format the task
asks for: a Python function, a JSON object, or a regular expression.
- No explanation, no markdown code fences, no surrounding text.
- Python must be valid and self-contained (standard library only).
- JSON must parse with json.loads.
- A regex must compile with Python's re module; reply with the bare pattern.

Task:
{task}
""",
}

CURRENT_VERSION = "v2"


def build_prompt(task: str, version: str = CURRENT_VERSION) -> str:
    return PROMPTS[version].format(task=task)
