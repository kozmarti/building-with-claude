"""See what temperature does: same prompt, several runs, two temperatures.

An LLM writes text one token at a time. For each next token it has a
probability for every possible option. Temperature reshapes those
probabilities before one is picked:
  - 0   -> almost always the single most likely token, so runs look the same
  - 1   -> the model's normal distribution, so less likely tokens get
           picked more often and runs differ more

NOTE: temperature is a legacy setting. Newer Claude models (Claude 4.7 and
later, including claude-opus-5-5 used elsewhere in this repo) reject it with
a 400 error, and the 2026-10-21 API version removes it for every model. This
demo therefore uses claude-haiku-4-5, an older model that still accepts it.

Run:  python 01-api-basics/temperature.py
      python 01-api-basics/temperature.py --runs 5 --prompt "Name a new ice cream flavour."
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import client  # noqa: E402

DEMO_MODEL = "claude-haiku-4-5"  # one of the last models that still accepts temperature
DEFAULT_PROMPT = "Invent a name for a coffee shop. Reply with the name only."


def generate(prompt: str, temperature: float) -> str:
    response = client.messages.create(
        model=DEMO_MODEL,
        max_tokens=50,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--runs", type=int, default=4)
    args = parser.parse_args()

    print(f"Prompt: {args.prompt}\nModel:  {DEMO_MODEL}\n")
    for temperature in (0.0, 1.0):
        outputs = [generate(args.prompt, temperature) for _ in range(args.runs)]
        print(f"temperature = {temperature}  ({len(set(outputs))} different answers "
              f"in {args.runs} runs)")
        for text in outputs:
            print(f"  - {text}")
        print()


if __name__ == "__main__":
    main()
