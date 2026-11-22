# 01 · API basics

- Making a request with the official Python SDK
- System prompts
- Multi-turn conversations: the API is stateless, so the client keeps the
  message history and sends all of it each time

- Temperature: how it changes the variety of answers

```bash
python 01-api-basics/chat.py
python 01-api-basics/temperature.py
```

## What I learned

- **A plain API call is just the model.** With no tools attached, Claude answers
  only from what it learned in training. It has no internet access, so it can't
  look up live information (news, prices, web pages), and anything after its
  training cutoff is unknown to it.
- **It can't take actions on its own.** It can't open files, run code or check
  facts. It only returns text. Tools (like the built-in web search tool, or
  functions I define) are what let it do more, which is the topic of a later
  module on tool use.
- **The API is stateless.** Claude doesn't remember earlier messages between
  requests. The chat feels continuous only because my script keeps the message
  history and sends all of it with each new message. When the script stops,
  the conversation is gone.
- **A system prompt sets the behaviour for the whole conversation**, e.g. tone
  and answer length, without being part of the user's messages.
- **LLMs generate text by probability.** The model writes one token (a word or
  part of a word) at a time. For each step it gives every possible next token
  a probability, then picks one.
- **Temperature controls how that pick is made.** At low temperature (0) the
  model almost always takes the most likely token, so the same prompt gives
  nearly the same answer every time. At higher temperature (up to 1 on Claude)
  less likely tokens get picked more often, so answers vary more and feel more
  "creative", but also drift off-target more easily.
  [`temperature.py`](temperature.py) runs the same prompt several times at 0
  and at 1 so you can see the difference.
- **Temperature is being phased out.** Newer Claude models (4.7 and later)
  don't accept it, and the newest API version removes it for every model, so
  my demo uses the older `claude-haiku-4-5`. On current models there's no
  replacement setting: to get more varied or more consistent answers you say
  so in the prompt.
