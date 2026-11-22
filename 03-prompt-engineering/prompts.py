"""Prompt versions for the athlete meal plan task.

Each version adds one prompt engineering technique on top of the previous
one, so the eval shows how much each technique helps:

  v1  baseline             - a vague, one-line request
  v2  clear and direct     - say exactly what to produce, as an instruction
  v3  specific guidelines  - list what a good answer must include
  v4  XML tags             - separate the athlete data from the instructions
  v5  example (one-shot)   - show the expected output format once
  v6  better example       - a detailed example whose numbers add up, plus a
                             note that it shows the format, not the length
"""

import json

TASK = "a one-day meal plan for an athlete"

V1 = """What should this athlete eat today?

{athlete_text}
"""

V2 = """Generate a one-day meal plan for the athlete described below.
The plan must support their goal for today and respect their dietary restrictions.

{athlete_text}
"""

GUIDELINES = """Guidelines:
1. Start with the daily calorie target and the protein / carbs / fat split in grams.
2. List every meal and snack with a time, the foods, and portion sizes in grams.
3. Time the meals around the athlete's training and goal.
4. Strictly respect the dietary restrictions. Never include a forbidden food.
5. Keep it practical: common foods that are easy to prepare.
6. End with one or two short tips specific to this athlete."""

V3 = """Generate a one-day meal plan for the athlete described below.
The plan must support their goal for today and respect their dietary restrictions.

{athlete_text}

""" + GUIDELINES + "\n"

V4 = """Generate a one-day meal plan for the athlete whose details are in the
<athlete> tags. The plan must support their goal for today and respect their
dietary restrictions.

<athlete>
{athlete_text}
</athlete>

<guidelines>
""" + GUIDELINES.removeprefix("Guidelines:\n") + """
</guidelines>
"""

EXAMPLE = """<example>
Athlete: tennis player, 70 kg, goal: match at 14:00, no restrictions.

Daily target: 2,700 kcal · protein 130 g · carbs 380 g · fat 75 g

07:30 Breakfast: oatmeal (80 g oats, 250 ml milk), 1 banana, 15 g honey
10:30 Snack: Greek yoghurt (170 g), 30 g granola
12:00 Pre-match lunch: white rice (90 g dry), grilled chicken (120 g), cooked carrots (100 g)
16:00 Recovery: chocolate milk (400 ml), 1 bagel with 20 g jam
19:30 Dinner: wholewheat pasta (100 g dry), salmon (150 g), salad with 10 ml olive oil

Tips: sip water with electrolytes during the match; keep lunch low in fibre
and fat so it digests before 14:00.
</example>"""

V5 = V4 + """
Here is an example of the expected format, for a different athlete. Use the
same structure, but base every number on the athlete above:

""" + EXAMPLE + "\n"

# v5's example was short, and Claude copied that: v5 plans were about half as
# long as v4's, and their foods no longer added up to the stated targets.
# v6 uses an example as detailed as the answer should be, with per-meal
# numbers that really add up to the daily total, and says what it's for.
DETAILED_EXAMPLE = """<example>
Athlete: tennis player, 70 kg, goal: match at 14:00, no restrictions.

Daily target: 2,800 kcal · protein 150 g · carbs 390 g · fat 70 g
(about 2.1 g protein and 5.6 g carbs per kg, for a match day)

07:30 Breakfast (570 kcal · P 20 g · C 104 g · F 10 g)
- Oats, 80 g, cooked in 250 ml semi-skimmed milk
- 1 banana (120 g), sliced on top
- Honey, 15 g

10:30 Snack (260 kcal · P 20 g · C 27 g · F 9 g)
- Greek yoghurt (2% fat), 170 g
- Granola, 30 g

12:00 Pre-match lunch (600 kcal · P 44 g · C 80 g · F 10 g)
- White rice, 90 g dry weight
- Grilled chicken breast, 120 g cooked
- Steamed carrots, 100 g, with 5 ml olive oil
Low in fibre and fat so it digests before 14:00.

16:00 Recovery, within 30 minutes of the match (615 kcal · P 23 g · C 111 g · F 10 g)
- Chocolate milk, 400 ml
- 1 plain bagel (90 g) with 20 g jam

19:30 Dinner (760 kcal · P 44 g · C 69 g · F 32 g)
- Wholewheat pasta, 100 g dry weight
- Baked salmon, 150 g raw weight
- Mixed salad, 100 g, with 10 ml olive oil

Totals: 2,805 kcal · P 151 g · C 391 g · F 71 g (matches the target)

Tips:
- Sip 500-750 ml of water with electrolytes per hour of play.
- If the match moves, keep lunch 2-3 hours before it and shift the snacks.
</example>"""

V6 = V4 + """
Here is an example for a different athlete. It shows the structure and the
level of detail expected: per-meal calories and macros, portions for every
food, and totals that match the target. Base every number on the athlete
above, not on the example. Include as many foods and meals as the athlete
needs, and before you finish, check that your foods really add up to your
daily target.

""" + DETAILED_EXAMPLE + "\n"

PROMPTS = {"v1": V1, "v2": V2, "v3": V3, "v4": V4, "v5": V5, "v6": V6}


def athlete_text(athlete: dict) -> str:
    return "\n".join(f"- {key.replace('_', ' ')}: {value}" for key, value in athlete.items())


def build_prompt(athlete: dict, version: str) -> str:
    return PROMPTS[version].format(athlete_text=athlete_text(athlete))


if __name__ == "__main__":
    # Print every version for the first athlete, to compare them side by side.
    from pathlib import Path

    first = json.loads((Path(__file__).parent / "dataset.json").read_text())[0]["athlete"]
    for name in PROMPTS:
        print(f"===== {name} =====\n{build_prompt(first, name)}")
