import os

from supabase import create_client

MAX_TAGS = 3

SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_illustrations",
        "description": (
            "사용자가 분위기를 입력했을 때 가장 먼저 사용한다. "
            "출력에 함께 오는 사용 가능한 태그 목록 중에서 분위기에 맞는 태그를 최대 3개 골라 검색한다. "
            "결과는 겹치는 태그 수가 많은 순, 같으면 조회수 순이다. "
            "결과가 0개면 다른 태그로 최대 2번까지 다시 검색하고, 그래도 없으면 찾지 못함으로 끝낸다. "
            "재검색할 때는 반드시 이전 결과의 사용 가능한 태그 목록(available_tags)에 있는 태그만 사용한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": MAX_TAGS,
                    "description": "검색할 분위기 태그 (최대 3개)",
                },
                "limit": {
                    "type": "integer",
                    "description": "돌려받을 최대 작품 수",
                },
            },
            "required": ["tags", "limit"],
        },
    },
}


def search_illustrations(tags, limit=5):
    tags = [t.strip() for t in tags if t and t.strip()][:MAX_TAGS]

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    rows = sb.table("illustrations").select(
        "id, title, artist, platform, tags, views, image_url, source_url"
    ).execute().data

    available_tags = sorted({t for r in rows for t in (r.get("tags") or [])})

    wanted = set(tags)
    matched = []
    for r in rows:
        overlap = len(wanted & set(r.get("tags") or []))
        if overlap > 0:
            matched.append({**r, "matched_tag_count": overlap})

    matched.sort(key=lambda r: (r["matched_tag_count"], r.get("views") or 0), reverse=True)

    return {
        "searched_tags": tags,
        "count": len(matched[:limit]),
        "illustrations": matched[:limit],
        "available_tags": available_tags,
    }
