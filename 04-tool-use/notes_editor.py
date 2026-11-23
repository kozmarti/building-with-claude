"""A training notes editor: Claude creates and edits real markdown files.

This uses Anthropic's text editor tool. Its name and input format are set by
Anthropic, so there's no schema to write: we only declare it in the request.
Claude still never touches the disk itself. It sends commands (view, create,
str_replace, insert) and this script carries them out.

Every file operation is locked to the notes/ folder next to this script.
Paths come from the model, so they are checked before anything is opened.

Run:  python 04-tool-use/notes_editor.py
Try:  "Create a 4-week plan for a 10 km race in plan.md"
      "In plan.md, change week 3's long run to 12 km"
      (Example prompts. Use your own goals.)
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import FALLBACK_BETA, MODEL, client  # noqa: E402

NOTES_DIR = (Path(__file__).parent / "notes").resolve()
TEXT_EDITOR = {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}

SYSTEM = """You help an amateur athlete write and update training notes.
Files live in a notes folder; use plain relative paths like "plan.md".
View a file before editing it. Keep edits small and targeted.
Keep chat answers short: the notes are in the files."""

MAX_TOOL_ROUNDS = 15


class EditorError(Exception):
    """Bad command or path; the message is sent back to Claude as an error."""


# --- Path safety --------------------------------------------------------------

def safe_path(raw: str) -> Path:
    """Turn a model-supplied path into a real path inside NOTES_DIR, or refuse."""
    if not raw:
        raise EditorError("path is required")
    relative = raw.lstrip("/")
    if relative.startswith("notes/"):
        relative = relative[len("notes/"):]
    # resolve() follows "..", symlinks and the like, so the check below sees the real target.
    path = (NOTES_DIR / relative).resolve()
    if path != NOTES_DIR and not path.is_relative_to(NOTES_DIR):
        raise EditorError(f"{raw!r} is outside the notes folder")
    return path


def _show(path: Path) -> str:
    return path.relative_to(NOTES_DIR).as_posix() or "."


# --- The four commands --------------------------------------------------------

def view(path: Path, view_range=None) -> str:
    if path.is_dir():
        files = sorted(p.relative_to(NOTES_DIR).as_posix() for p in path.rglob("*") if p.is_file())
        return "\n".join(files) if files else "(the notes folder is empty)"
    if not path.exists():
        raise EditorError(f"{_show(path)} does not exist")
    lines = path.read_text().splitlines()
    start, end = 1, len(lines)
    if view_range:
        start = view_range[0]
        end = len(lines) if view_range[1] == -1 else view_range[1]
    return "\n".join(f"{n}: {lines[n - 1]}" for n in range(max(start, 1), min(end, len(lines)) + 1))


def create(path: Path, file_text: str) -> str:
    if path.exists():
        path.with_name(path.name + ".bak").write_text(path.read_text())  # keep the old version
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(file_text)
    return f"Saved {_show(path)}"


def str_replace(path: Path, old_str: str, new_str: str) -> str:
    if not path.is_file():
        raise EditorError(f"{_show(path)} does not exist")
    text = path.read_text()
    count = text.count(old_str)
    if count != 1:
        raise EditorError(f"old_str must match exactly once, it matched {count} times")
    path.write_text(text.replace(old_str, new_str))
    return f"Edited {_show(path)}"


def insert(path: Path, insert_line: int, insert_text: str) -> str:
    if not path.is_file():
        raise EditorError(f"{_show(path)} does not exist")
    lines = path.read_text().splitlines(keepends=True)
    if not 0 <= insert_line <= len(lines):
        raise EditorError(f"insert_line must be between 0 and {len(lines)}")
    if not insert_text.endswith("\n"):
        insert_text += "\n"
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.insert(insert_line, insert_text)
    path.write_text("".join(lines))
    return f"Inserted text after line {insert_line} in {_show(path)}"


def run_editor(tool_input: dict) -> tuple[str, bool]:
    """Carry out one text editor command. Returns (result text, is_error)."""
    try:
        command = tool_input.get("command")
        path = safe_path(tool_input.get("path", ""))
        if command == "view":
            return view(path, tool_input.get("view_range")), False
        if command == "create":
            return create(path, tool_input.get("file_text", "")), False
        if command == "str_replace":
            return str_replace(path, tool_input["old_str"], tool_input.get("new_str", "")), False
        if command == "insert":
            return insert(path, tool_input["insert_line"], tool_input["insert_text"]), False
        raise EditorError(f"Unknown command: {command!r}")
    except (EditorError, KeyError, TypeError) as exc:
        return f"Error: {exc}", True


# --- The loop (same shape as assistant.py) ------------------------------------

def run_turn(messages: list) -> str:
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=[TEXT_EDITOR],
            messages=messages,
            output_config={"effort": "low"},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "refusal":
            return "(Claude declined this request.)"
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result, is_error = run_editor(block.input)
            short = {k: v for k, v in block.input.items() if k in ("command", "path", "view_range", "insert_line")}
            print(f"  [editor] {json.dumps(short)} -> {result.splitlines()[0] if result else ''}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
                "is_error": is_error,
            })
        messages.append({"role": "user", "content": tool_results})

    return "(Stopped: too many tool calls in one turn.)"


def main() -> None:
    NOTES_DIR.mkdir(exist_ok=True)
    messages: list = []
    print(f"Training notes editor. Files are saved in {NOTES_DIR}. Type 'quit' to exit.\n")
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
