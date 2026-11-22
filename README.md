# Building with the Claude API

My projects and notes from Anthropic's
[Building with the Claude API](https://academy.claude.com/courses/building-with-the-claude-api)
course. Each folder is one module, with code I wrote while working through it.

## Modules

| # | Module | What's inside |
|---|---|---|
| 01 | [API basics](01-api-basics/) | Requests, system prompts, a multi-turn terminal chat, and a temperature experiment |

More modules (prompt evaluation, tool use) are coming as I work through the course.

## Highlights

- **[`chat.py`](01-api-basics/chat.py):** a terminal chat that keeps the
  conversation history itself, because the API is stateless.
- **[`temperature.py`](01-api-basics/temperature.py):** runs the same prompt
  several times at temperature 0 and 1 to show how sampling changes the
  variety of answers, and why this setting is being phased out on newer models.

## Setup

Requires Python 3.9+.

```bash
git clone https://github.com/<your-username>/building-with-claude.git
cd building-with-claude
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your API key to .env
```

Get an API key from the [Claude Console](https://platform.claude.com). The
`.env` file is gitignored, so the key never gets committed.

Each time you open a new terminal, activate the environment again before
running anything:

```bash
source .venv/bin/activate
```

Once it's active, `python` points at the environment's Python, which has the
packages installed. Your prompt shows `(.venv)` while it's active. Without
activating, macOS only has `python3`, which won't find the packages.

Then run:

```bash
python 01-api-basics/chat.py
python 01-api-basics/temperature.py
```

## Project layout

```
common/claude.py     shared client, model choice and helpers used by every module
01-api-basics/       module 1
```

## Tech

Python · [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) ·
Claude Opus 5.5 (and Claude Haiku 4.5 for the temperature demo)

## License

[MIT](LICENSE)
