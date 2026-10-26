import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools.search_illustrations import SCHEMA as SEARCH_SCHEMA, search_illustrations

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_STEPS = int(os.getenv("MAX_STEPS", "10"))

SYSTEM_PROMPT = """너는 사용자가 입력한 분위기에 맞는 일러스트를 찾아주는 에이전트다.
- 분위기를 입력받으면 가장 먼저 search_illustrations를 사용한다.
- 태그는 도구 결과의 available_tags 안에서 최대 3개를 고른다.
- 결과가 0개면 다른 태그로 최대 2번까지 다시 검색하고, 그래도 없으면 "찾지 못함"이라고 답한다.
- 재검색할 때는 반드시 이전 결과의 사용 가능한 태그 목록(available_tags)에 있는 태그만 사용한다.
- 최대 5개 작품을 보여준다. 각 작품에 이미지 주소, 작가, 원본 링크, 추천 이유를 쓴다.
- 도구 결과에 없는 내용은 절대 쓰지 않는다. 값이 비어 있으면 "찾지 못함"이라고 쓴다.
- 각 정보의 출처로 원본 링크를 붙인다."""

TOOLS = [SEARCH_SCHEMA]
TOOL_FUNCTIONS = {
    "search_illustrations": search_illustrations,
}


def format_args(args):
    return ", ".join(f"{k}={v!r}" for k, v in args.items())


def run_agent(user_input):
    client = OpenAI()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    for step in range(1, MAX_STEPS + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            print()
            print(message.content)
            return

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"[step {step}] {name}({format_args(args)})")

            func = TOOL_FUNCTIONS.get(name)
            if func is None:
                result = {"error": f"알 수 없는 도구: {name}"}
            else:
                try:
                    result = func(**args)
                except Exception as e:
                    result = {"error": str(e)}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    print("max_steps 도달")


if __name__ == "__main__":
    user_input = input("원하는 분위기를 한 줄로 입력하세요: ").strip()
    if user_input:
        run_agent(user_input)
