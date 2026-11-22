"""Evaluate a meal plan prompt version on every athlete in dataset.json.

A meal plan can't be checked with code (there is no "valid" or "invalid"
plan), so this eval uses a model grader only. Claude scores each plan 1-10
against general criteria for any good plan plus the extra criteria of that
athlete.

Run:  python 03-prompt-engineering/run_eval.py --version v1
      python 03-prompt-engineering/run_eval.py --all      # every version, then a summary
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import List

from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import MODEL, chat, structured  # noqa: E402
from prompts import PROMPTS, athlete_text, build_prompt  # noqa: E402

HERE = Path(__file__).parent

GENERAL_CRITERIA = """- States a daily calorie target and a protein / carbs / fat breakdown in grams
- The numbers are realistic for the athlete's body weight, sport and goal
- Lists every meal and snack with a time, foods and portion sizes
- Meal timing fits the athlete's training and goal
- Fully respects the dietary restrictions
- Practical, easy-to-follow foods"""


class Grade(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    reasoning: str
    score: int  # 1-10


GRADER_PROMPT = """You are a sports nutritionist grading a one-day meal plan
written by an AI assistant.

<athlete>
{athlete}
</athlete>

<criteria>
{general}
{extra}
</criteria>

<meal_plan>
{plan}
</meal_plan>

Grade the meal plan strictly against every criterion. A plan that includes a
food the athlete must avoid scores 3 or lower. List the key strengths and
weaknesses, explain your reasoning, then give a score from 1 (unusable) to
10 (excellent, meets every criterion)."""


def grade(case: dict, plan: str) -> Grade:
    prompt = GRADER_PROMPT.format(
        athlete=athlete_text(case["athlete"]),
        general=GENERAL_CRITERIA,
        extra=f"- {case['extra_criteria']}",
        plan=plan,
    )
    result = structured(prompt, Grade, effort="low")
    result.score = max(1, min(10, result.score))
    return result


def run_case(case: dict, version: str) -> dict:
    plan = chat([{"role": "user", "content": build_prompt(case["athlete"], version)}])
    result = grade(case, plan)
    return {
        "athlete": case["athlete"],
        "plan": plan,
        "score": result.score,
        "strengths": result.strengths,
        "weaknesses": result.weaknesses,
        "reasoning": result.reasoning,
    }


def run_version(cases: list, version: str, workers: int) -> float:
    print(f"Running prompt {version} on {len(cases)} athletes with {MODEL}...")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda c: run_case(c, version), cases))

    for i, r in enumerate(results, 1):
        a = r["athlete"]
        print(f"  {i}. score {r['score']:>2}  {a['sport']} ({a['dietary_restrictions']})")
    average = mean(r["score"] for r in results)
    print(f"  Average for {version}: {average:.2f} / 10\n")

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = out_dir / f"{version}-{stamp}.json"
    out_file.write_text(json.dumps(
        {"prompt_version": version, "model": MODEL,
         "average_score": average, "results": results},
        indent=2,
    ) + "\n")
    return average


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--version", choices=sorted(PROMPTS))
    group.add_argument("--all", action="store_true", help="run every prompt version")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    cases = json.loads((HERE / "dataset.json").read_text())
    versions = sorted(PROMPTS) if args.all else [args.version]
    averages = {v: run_version(cases, v, args.workers) for v in versions}

    if len(averages) > 1:
        print("Summary")
        for v, avg in averages.items():
            print(f"  {v}: {avg:.2f} / 10")
    print(f"Full results saved in {(HERE / 'results').relative_to(HERE.parent)}/")


if __name__ == "__main__":
    main()
