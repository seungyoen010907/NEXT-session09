import os
from dotenv import load_dotenv

load_dotenv()
ok_count = 0

for name in ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]:
    print(f"[OK]   .env에 {name} 있음" if os.getenv(name) else f"[실패] .env에 {name} 없음")

try:
    from openai import OpenAI
    models = OpenAI().models.list()
    print(f"[OK]   OpenAI 호출 성공 (사용 가능한 모델 {len(models.data)}개)")
    ok_count += 1
except Exception as e:
    print(f"[실패] OpenAI 호출: {e}")

try:
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    rows = sb.table("illustrations").select("id, title, tags").limit(3).execute().data
    print(f"[OK]   Supabase 조회 성공 (illustrations에서 {len(rows)}개 읽음)")
    for r in rows:
        print(f"         - {r['id']}: {r['title']} {r['tags']}")
    if not rows:
        print("         (0개라면 더미 데이터를 아직 안 넣었거나 RLS 설정 문제)")
    ok_count += 1
except Exception as e:
    print(f"[실패] Supabase 조회: {e}")

print()
print("환경 체크 통과!" if ok_count == 2 else "환경 체크 실패 - 위의 [실패] 줄을 확인하세요")
