"""Step 3 of the eval workflow: grade each output.

Two kinds of grader, combined into one score per test case:

- Code grader: cheap and deterministic. Checks the output is valid in the
  format the task asked for (Python parses, JSON loads, regex compiles).
- Model grader: Claude reviews the output against the case's criteria and
  gives a 1-10 score with its reasoning.
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import List

from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import structured  # noqa: E402


# --- Code grader -------------------------------------------------------------

def _strip_fences(text: str) -> str:
    """Return the text without surrounding markdown fences (used for checking only)."""
    match = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", text.strip(), re.DOTALL)
    return match.group(1) if match else text.strip()


def validate_format(output: str, fmt: str) -> tuple[int, str]:
    """Return (score 0 or 10, note). Fenced output is penalised but still checked."""
    had_fences = _strip_fences(output) != output.strip()
    body = _strip_fences(output)
    try:
        if fmt == "python":
            ast.parse(body)
        elif fmt == "json":
            json.loads(body)
        elif fmt == "regex":
            re.compile(body)
        else:
            return 0, f"unknown format {fmt!r}"
    except (SyntaxError, ValueError, re.error) as exc:
        return 0, f"invalid {fmt}: {exc}"
    if had_fences:
        return 5, f"valid {fmt}, but wrapped in markdown fences"
    return 10, f"valid {fmt}"


# --- Model grader ------------------------------------------------------------

class ModelGrade(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    reasoning: str
    score: int  # 1-10


GRADER_PROMPT = """You are grading an AI assistant's answer to a data-cleaning task.

<task>
{task}
</task>

<required_format>{fmt}</required_format>

<solution_criteria>
{criteria}
</solution_criteria>

<answer>
{output}
</answer>

Judge the answer strictly against the criteria and the required format.
List key strengths and weaknesses, explain your reasoning, then give a score
from 1 (fails the task) to 10 (fully correct, nothing extra). Answers that add
explanation or text outside the required format should lose points."""


def grade_with_model(case: dict, output: str) -> ModelGrade:
    prompt = GRADER_PROMPT.format(
        task=case["task"],
        fmt=case["format"],
        criteria=case["solution_criteria"],
        output=output,
    )
    grade = structured(prompt, ModelGrade, effort="low")
    grade.score = max(1, min(10, grade.score))
    return grade
