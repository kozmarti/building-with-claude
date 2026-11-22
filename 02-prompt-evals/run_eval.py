"""Steps 2-4 of the eval workflow: run the prompt, grade, report.

For every test case in dataset.json:
  1. fill in the prompt template and send it to Claude
  2. grade the output with the code grader and the model grader
  3. combine them into one score (average of the two, 1-10)

Prints a summary table and saves the full results to results/.

Run:  python 02-prompt-evals/run_eval.py
      python 02-prompt-evals/run_eval.py --version v1   # compare prompt versions
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from statistics import mean

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import MODEL, chat  # noqa: E402
from graders import grade_with_model, validate_format  # noqa: E402
from prompt import CURRENT_VERSION, PROMPTS, build_prompt  # noqa: E402

HERE = Path(__file__).parent


def run_case(case: dict, version: str) -> dict:
    output = chat([{"role": "user", "content": build_prompt(case["task"], version)}])
    code_score, code_note = validate_format(output, case["format"])
    model_grade = grade_with_model(case, output)
    return {
        "task": case["task"],
        "format": case["format"],
        "output": output,
        "code_score": code_score,
        "code_note": code_note,
        "model_score": model_grade.score,
        "model_reasoning": model_grade.reasoning,
        "score": (code_score + model_grade.score) / 2,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(HERE / "dataset.json"))
    parser.add_argument("--version", default=CURRENT_VERSION, choices=sorted(PROMPTS))
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        sys.exit(f"No dataset at {dataset_path}. Run generate_dataset.py first.")
    cases = json.loads(dataset_path.read_text())

    print(f"Running prompt {args.version} on {len(cases)} cases with {MODEL}...\n")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda c: run_case(c, args.version), cases))

    for i, r in enumerate(results, 1):
        print(f"{i:>2}. [{r['format']:<6}] score {r['score']:>4.1f}  "
              f"(code {r['code_score']:>2}, model {r['model_score']:>2})  {r['task'][:60]}")

    average = mean(r["score"] for r in results)
    print(f"\nAverage score for {args.version}: {average:.2f} / 10")

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = out_dir / f"{args.version}-{stamp}.json"
    out_file.write_text(json.dumps(
        {"prompt_version": args.version, "model": MODEL,
         "average_score": average, "results": results},
        indent=2,
    ) + "\n")
    print(f"Full results saved to {out_file.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
