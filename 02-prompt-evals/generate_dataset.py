"""Step 1 of the eval workflow: build a test dataset.

Uses Claude to write realistic test cases, each with the expected output
format and the criteria a good answer must meet. Saves them to dataset.json
so every eval run uses the same inputs.

Run:  python 02-prompt-evals/generate_dataset.py --count 6
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import structured  # noqa: E402

HERE = Path(__file__).parent


class TestCase(BaseModel):
    task: str
    format: Literal["python", "json", "regex"]
    solution_criteria: str


class Dataset(BaseModel):
    cases: List[TestCase]


GENERATOR_PROMPT = """Write {count} test cases for evaluating a data-cleaning assistant.

Each case is a short, realistic task a data analyst might ask for, solvable
with ONE of: a Python function, a JSON object, or a regular expression.
Spread the cases across all three formats.

For each case give:
- task: the request, which says which format it wants
- format: "python", "json" or "regex"
- solution_criteria: 2-4 concrete things a correct answer must do

Keep each task solvable in under 30 lines. Vary the difficulty."""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=6)
    parser.add_argument("--out", default=str(HERE / "dataset.json"))
    args = parser.parse_args()

    dataset = structured(GENERATOR_PROMPT.format(count=args.count), Dataset)
    cases = [case.model_dump() for case in dataset.cases]

    Path(args.out).write_text(json.dumps(cases, indent=2) + "\n")
    print(f"Saved {len(cases)} test cases to {args.out}")


if __name__ == "__main__":
    main()
