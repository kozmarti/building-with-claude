"""Give Claude internet access with the built-in web search tool.

A plain API call only knows what Claude learned in training. Web search is a
*server tool*: Anthropic runs the searches, so there's no function to write
and no tool loop on our side. We add the tool to the request, Claude decides
when to search, and the answer comes back with citations to its sources.

Each search costs a small fee on top of the tokens; max_uses caps how many
searches one request can make.

Run:  python 04-tool-use/web_search.py "Who won the most recent Tour de France?"
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.claude import FALLBACK_BETA, MODEL, client  # noqa: E402

WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 3}


def search(question: str):
    messages = [{"role": "user", "content": question}]
    while True:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            tools=[WEB_SEARCH],
            messages=messages,
            output_config={"effort": "low"},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
        # A long server-side search can pause; send the reply back and it resumes.
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        return response


def main() -> None:
    question = " ".join(sys.argv[1:]) or "What is the current world record for the men's marathon?"
    print(f"Question: {question}\n")
    response = search(question)

    if response.stop_reason == "refusal":
        print("(Claude declined this request.)")
        return

    sources = {}
    for block in response.content:
        if block.type == "server_tool_use":
            print(f"  [searched] {block.input.get('query', block.input)}")
        elif block.type == "text":
            print(block.text, end="")
            for citation in block.citations or []:
                if citation.type == "web_search_result_location":
                    sources[citation.url] = citation.title or citation.url
    print("\n")

    if sources:
        print("Sources:")
        for url, title in sources.items():
            print(f"  - {title}: {url}")


if __name__ == "__main__":
    main()
