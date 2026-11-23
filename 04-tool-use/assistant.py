"""A training log assistant: a terminal chat where Claude can use tools.

This is the tool use loop written out by hand, so every step is visible:
  1. send the conversation plus the tool schemas
  2. if Claude replies with tool_use blocks, run those tools ourselves
  3. send the results back as tool_result blocks in a user message
  4. repeat until Claude answers without asking for a tool

Run:  python 04-tool-use/assistant.py
Try:  "I ran 10 km in 52 minutes this morning, felt strong. What was my pace?"
      "How much did I train this week?"
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import FALLBACK_BETA, MODEL, client  # noqa: E402
from tools import TOOL_SCHEMAS, run_tool  # noqa: E402

SYSTEM = """You are a friendly training log assistant for an amateur athlete.
Use the tools to log workouts, calculate paces and summarise training.
Never invent dates: get the current date with a tool when you need it.
Keep answers short."""

MAX_TOOL_ROUNDS = 10  # safety limit so a confused loop can't run forever


def ask_claude(messages: list):
    return client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        tools=TOOL_SCHEMAS,
        messages=messages,
        output_config={"effort": "low"},
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )


def run_turn(messages: list) -> str:
    """Run one user turn to completion, calling tools as needed. Returns Claude's text."""
    for _ in range(MAX_TOOL_ROUNDS):
        response = ask_claude(messages)

        # Always keep Claude's full reply (text, thinking and tool_use blocks) in
        # the history: the next request needs the tool_use blocks to match the results.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "refusal":
            return "(Claude declined this request.)"
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result, is_error = run_tool(block.name, block.input)
            print(f"  [tool] {block.name}({json.dumps(block.input)}) -> {result}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,  # links this result to Claude's request
                "content": result,
                "is_error": is_error,
            })

        # All results go back together, in one user message.
        messages.append({"role": "user", "content": tool_results})

    return "(Stopped: too many tool calls in one turn.)"


def main() -> None:
    messages: list = []
    print("Training log assistant. Type 'quit' to exit.\n")
    while True:
        user_input = input("you > ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue
        messages.append({"role": "user", "content": user_input})
        print(f"\nclaude > {run_turn(messages)}\n")


if __name__ == "__main__":
    main()
