# Building with the Claude API

My projects and notes from Anthropic's
[Building with the Claude API](https://academy.claude.com/courses/building-with-the-claude-api)
course. Each folder is one module, with code I wrote while working through it.

## Modules

| # | Module | What's inside |
|---|---|---|
| 01 | [API basics](01-api-basics/) | Requests, system prompts, a multi-turn terminal chat, and a temperature experiment |
| 02 | [Prompt evals](02-prompt-evals/) | An end-to-end eval pipeline: generated dataset, code + model graders, scored prompt versions |
| 03 | [Prompt engineering](03-prompt-engineering/) | An athlete meal plan prompt improved one technique at a time, each version scored by an eval |
| 04 | [Tool use](04-tool-use/) | A training log assistant with my own tools, web search with citations, and a text editor locked to one folder |

More modules are coming as I work through the course.

## Highlights

- **[Prompt eval pipeline](02-prompt-evals/):** tests a prompt the way you'd
  test code. It runs the prompt on a dataset, grades each output with a code
  grader (is it valid?) and a model grader (is it correct?), and reports an
  average score. Adding explicit output-format rules took the prompt from
  **3.17 to 9.67 / 10**.
- **[Prompt engineering experiment](03-prompt-engineering/):** clear
  instructions, specific guidelines and XML tags raised a meal plan prompt
  from 7.25 to 9.00 / 10. Adding a short example then *dropped* it to 7.00,
  because Claude copied the example's brevity. The README shows how the eval
  results revealed why.
- **[Tool use loop](04-tool-use/):** a hand-written loop where Claude calls
  four Python tools to log workouts and summarise training, plus Anthropic's
  web search and text editor tools. Paths from the model are checked so the
  editor can't leave its folder.

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
key can go in `.env` or `.env.local`; both are gitignored, so it never gets
committed.

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
python 02-prompt-evals/run_eval.py --version v2
python 03-prompt-engineering/run_eval.py --version v4
python 04-tool-use/assistant.py
python 04-tool-use/web_search.py "Who won the most recent Tour de France?"
python 04-tool-use/notes_editor.py
```

## Project layout

```
common/claude.py     shared client, model choice and helpers used by every module
01-api-basics/       module 1
02-prompt-evals/     module 2
03-prompt-engineering/  module 3
04-tool-use/         module 4
```

## Tech

Python · [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) ·
Pydantic (structured outputs) · Claude Opus 5.5 (and Claude Haiku 4.5 for the temperature demo)

## License

[MIT](LICENSE)
