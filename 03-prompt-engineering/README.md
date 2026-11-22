# 03 · Prompt engineering

Prompt engineering means improving a prompt step by step, and using an eval
to prove each step helped. This module takes one task, **a one-day meal plan
for an athlete**, and builds the prompt up one technique at a time. Every
version is scored by the same eval, so the effect of each technique shows up
as a number.

## The techniques

| Version | Technique | What changes in the prompt |
|---|---|---|
| `v1` | Baseline | "What should this athlete eat today?" plus the athlete's details |
| `v2` | **Be clear and direct** | An instruction that says exactly what to produce and what it must respect |
| `v3` | **Be specific** | A numbered list of guidelines: calorie and macro targets, times, portions in grams, restrictions, tips |
| `v4` | **Structure with XML tags** | The athlete data and the guidelines go in `<athlete>` and `<guidelines>` tags, so instructions and data can't be confused |
| `v5` | **Give an example** (one-shot) | One sample plan for a different athlete, showing the exact format expected |
| `v6` | **A better example** | A detailed sample plan whose numbers really add up, plus a note that it shows the format and level of detail, not a length limit |

All versions are in [`prompts.py`](prompts.py). To see them side by side:

```bash
python 03-prompt-engineering/prompts.py
```

## The eval

- **Dataset:** [`dataset.json`](dataset.json) has four athletes with different
  sports, goals and dietary restrictions (vegetarian, lactose intolerant,
  gluten-free). Each has extra criteria a good plan must meet.
- **Grader:** a model grader only. There's no code check that can tell a
  good meal plan from a bad one, so Claude, acting as a sports nutritionist,
  scores each plan 1-10 against general criteria plus the athlete's extra
  criteria. A plan that includes a forbidden food scores 3 or lower.

## Run it

```bash
python 03-prompt-engineering/run_eval.py --version v1   # one version
python 03-prompt-engineering/run_eval.py --all          # every version, with a summary
```

Each version makes 8 API calls (4 athletes × a plan and a grade). Meal plans
are long answers, so `--all` costs roughly a dollar.

## Results

| Version | Technique | Average score |
|---|---|---|
| `v1` | Baseline | 7.25 / 10 |
| `v2` | Clear and direct | 8.25 / 10 |
| `v3` | Specific guidelines | 8.75 / 10 |
| `v4` | XML tags | **9.00 / 10** |
| `v5` | One-shot example | 7.00 / 10 |
| `v6` | Better example | *(not run yet)* |

### Why v5 got worse

Adding an example *lowered* the score below the baseline. The results files
show why: Claude copied the example's short, compact style, not just its
layout.

| Athlete | v4 score | v5 score | v4 plan length | v5 plan length |
|---|---|---|---|---|
| Marathon (vegetarian) | 9 | 7 | 3,287 chars | 1,307 chars |
| Powerlifting (lactose-free) | 9 | 6 | 2,767 chars | 1,528 chars |
| Swimming | 9 | 6 | 2,686 chars | 1,230 chars |
| Cycling (gluten-free) | 9 | 9 | 3,401 chars | 1,993 chars |

v5 plans were about half as long. In three of the four cases the grader's
main complaint was the same: the foods listed didn't add up to the plan's own
calorie and protein targets (e.g. a stated 3,100 kcal, but foods worth about
2,500 kcal). With less room for detail, the numbers stopped matching.

`v6` tests the fix: an example that is as detailed as the answer should be,
whose numbers really add up, plus an explicit note on what the example is for.

## What I learned

- **Prompt engineering is iterative, and every step needs a measurement.**
  I changed one thing per version and ran the same eval each time, so each
  score change can be traced to one technique.
- **Clear, specific instructions gave steady gains.** Saying exactly what to
  produce (v2, +1.0), listing what a good answer must include (v3, +0.5) and
  separating data from instructions with XML tags (v4, +0.25) took the
  prompt from 7.25 to 9.00. The biggest single jump came from the simplest
  change: turning a vague question into a direct instruction.
- **XML tags help Claude tell the parts of a prompt apart.** Wrapping the
  athlete's details in `<athlete>` and the rules in `<guidelines>` makes it
  clear what is data and what is instruction. This matters more as prompts
  get longer.
- **An example is the strongest signal in a prompt, and it can backfire.**
  Adding a one-shot example (v5) dropped the score to 7.00, below the
  baseline. Claude copied the example's short, compact style, so its plans
  came out about half as long, and the foods no longer added up to the
  plan's own calorie targets. The model imitates the length, detail and tone
  of an example, not just its layout.
- **A good example has to be as good as the answer you want.** It should be
  as detailed as a real answer and correct in every detail. The prompt
  should also say what the example is for (format, not length). `v6` tests
  exactly this fix.
- **More techniques don't automatically mean a better prompt.** Without the
  eval, v5 would look like the most "advanced" prompt. Only the measurement
  showed it was the worst one.
- **Read the grader's reasoning, not only the score.** The average said
  *that* v5 was worse. The results files said *why*: the same weakness came
  up in three of four cases.
- **Small datasets are noisy.** With only four athletes, a difference of 0.25
  could be chance. The v5 drop is believable because it was large and had
  the same cause in most cases. A bigger dataset would make the smaller
  differences more trustworthy.
