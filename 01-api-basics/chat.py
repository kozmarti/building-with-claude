"""A minimal multi-turn chat in the terminal.

Shows the core idea behind conversations with the Claude API: the API is
stateless, so we keep the whole message history ourselves and send it with
every request.

Run:  python 01-api-basics/chat.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import chat  # noqa: E402

SYSTEM = "You are a friendly, concise assistant. Keep answers under 120 words."


def main() -> None:
    history: list[dict] = []
    print("Chat with Claude. Type 'quit' to exit.\n")
    while True:
        user_input = input("you > ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        reply = chat(history, system=SYSTEM, effort="low")
        history.append({"role": "assistant", "content": reply})
        print(f"\nclaude > {reply}\n")


if __name__ == "__main__":
    main()
