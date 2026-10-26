# PRD: 분위기 기반 일러스트 핀 추천 에이전트

## 1. 목표

사용자가 원하는 분위기를 **한 줄**로 입력하면, 에이전트가 저장된 일러스트 데이터에서 그 분위기에 맞는 태그로 작품을 찾아 **최대 5개**를 핀 카드로 보여준다.

- 정렬 기준: 겹치는 태그 수(관련도)가 많은 순 → 관련도가 같으면 **조회수 높은 순**
- 핀 카드 구성: 이미지 주소, 작가, 원본 링크, 추천 이유
- 사용자가 저장할 카드를 고르고 **승인(y)** 하면 고른 작품만 내 컬렉션에 저장한다
- 맞는 작품이 없으면 **"찾지 못함"** 을 알리고 끝낸다

### 1.1 고정 워크플로우가 아닌 에이전트로 만드는 이유

- 분위기 입력은 자유 표현이라("비 오는 날 창가 같은 느낌") 저장된 태그와 바로 일치하지 않는다. 사용 가능한 태그 목록을 보고 의미가 맞는 태그를 골라야 한다.
- 검색 결과에 따라 다음 행동이 매번 달라진다.
  - 결과 0개 → 다른 태그로 재검색 (최대 2번)
  - 작가/이미지 주소가 빈 작품 → 원본 링크로 정보 보충
  - 재검색 후에도 0개 → 중단하고 "찾지 못함"

### 1.2 하지 않을 것 (Non-goals)

- 승인(y) 없이 컬렉션에 저장하지 않는다. 이미 저장된 항목을 수정하거나 삭제하지 않는다.
- 이미지 파일을 다운로드하거나 재게시하지 않는다. 저장된 목록 밖의 사이트를 돌아다니며 수집하지 않는다.
- 데이터에 없는 작품, 작가, 조회수를 지어내지 않는다.

## 2. 사용자 흐름

```
1. 사용자: "몽환적이고 차분한 밤하늘 느낌"
2. 에이전트: search_illustrations(tags=["밤", "몽환", "차분"], limit=5)
3. (작가/이미지 주소 누락 작품이 있으면) fetch_image_preview(url=원본 링크)
4. 에이전트: 핀 카드 최대 5개 출력
5. 사용자: 저장할 카드 선택 (예: 1, 3)
6. 시스템: 저장할 작품 제목 표시 → "저장할까요? (y/n)"
7. y → save_to_collection(illustration_ids=[...]) / n → 아무것도 저장하지 않음
```

## 3. 도구 목록

| 이름 | 입력 | 출력 | description |
|---|---|---|---|
| `search_illustrations` | `tags: string[]` (최대 3개), `limit: int` | 작품 목록 (id, 제목, 작가, 플랫폼, 태그, 조회수, 이미지 주소, 원본 링크), 사용 가능한 태그 목록 | 사용자가 분위기를 입력했을 때 가장 먼저 사용한다. 출력에 함께 오는 사용 가능한 태그 목록 중에서 분위기에 맞는 태그를 최대 3개 골라 검색한다. 결과는 겹치는 태그 수가 많은 순, 같으면 조회수 순이다. 결과가 0개면 다른 태그로 최대 2번까지 다시 검색하고, 그래도 없으면 찾지 못함으로 끝낸다. |
| `fetch_image_preview` | `url: string` | 이미지 주소, 제목, 작가, 원본 링크, 상태(`ok`/`찾지 못함`) | 검색 결과 중 작가나 이미지 주소가 비어 있는 작품에만 사용한다. 그 작품의 원본 링크 1개를 읽어 정보를 보충한다. 검색 용도로 쓰지 않는다. |
| `save_to_collection` | `illustration_ids: string[]` | 저장된 개수, 저장 상태 | 추천 카드를 보여준 뒤 사용자가 저장할 작품을 골랐을 때만 사용한다. 추천한 작품 중 사용자가 고른 id만 넣는다. **쓰기 작업이다.** |

- 읽기 도구: `search_illustrations`, `fetch_image_preview`
- 쓰기 도구: `save_to_collection` (실행 전 사람 확인 y/n 필수)

## 4. 데이터

> ⚠️ **illustrations 테이블의 일러스트 데이터는 모두 개발·테스트용 더미 데이터다.** 실제 작품, 작가, 조회수가 아니다.

Supabase에 두 개의 테이블을 둔다.

### 4.1 `illustrations` (더미 20~30개)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | text (PK) | 작품 id |
| `title` | text | 제목 |
| `artist` | text, nullable | 작가 (일부 비워서 보충 흐름 테스트) |
| `platform` | text | 플랫폼 이름 |
| `tags` | text[] | 분위기 태그 |
| `views` | int | 조회수 |
| `image_url` | text, nullable | 이미지 주소 (일부 비워서 보충 흐름 테스트) |
| `source_url` | text | 원본 링크 |

### 4.2 `collection`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | bigint (PK, auto) | 저장 항목 id |
| `illustration_id` | text (FK → illustrations.id) | 저장한 작품 |
| `saved_at` | timestamptz (default now()) | 저장 시각 |

- 에이전트는 `collection`에 **INSERT만** 한다. UPDATE/DELETE는 하지 않는다.

## 5. 스택

- Python
- OpenAI API (function calling 기반 에이전트 루프)
- Supabase (`supabase-py`)

## 6. 성공 기준

| # | 기준 | 확인 방법 |
|---|---|---|
| 1 | 분위기 입력 시 첫 도구 호출이 `search_illustrations`이고, 태그는 사용 가능한 태그 목록 안에서 최대 3개다 | 터미널 로그의 `[step 1] search_illustrations(tags=[...], limit=...)` 확인 |
| 2 | 카드는 최대 5개, 관련도 → 조회수 순으로 정렬된다 | 출력 카드 순서와 `search_illustrations` 결과의 태그 겹침 수·조회수 비교 |
| 3 | 카드의 모든 정보(이미지 주소, 작가, 원본 링크, 조회수)가 도구 결과에 존재한다 | 카드 내용과 로그에 찍힌 도구 결과 대조. 비어 있는 값은 "찾지 못함"으로 표시 |
| 4 | 작가/이미지 주소가 빈 작품에만 `fetch_image_preview`가 호출된다 | 로그에서 `fetch_image_preview(url=...)` 호출 대상이 누락 작품의 원본 링크인지 확인 |
| 5 | 결과 0개일 때 재검색은 최대 2번, 이후 "찾지 못함"으로 종료된다 | 데이터에 없는 분위기(예: "사이버펑크 공룡 요리")로 실행 → 로그에 `search_illustrations` 최대 3회 후 "찾지 못함" 출력 |
| 6 | 저장 전 작품 제목이 표시되고 y/n 확인을 받는다. n이면 아무것도 저장되지 않는다 | n 입력 후 Supabase `collection` 테이블 행 수가 변하지 않았는지 확인 |
| 7 | y 승인 시 사용자가 고른 id만 저장된다 | 로그의 `save_to_collection(illustration_ids=[...])` 인자와 `collection` 테이블 새 행 비교 |
| 8 | 루프는 `max_steps`를 넘지 않는다 | 로그의 마지막 `[step N]`에서 N ≤ max_steps 확인 |

### 6.1 로그 형식

모든 도구 호출은 터미널에 다음 형식으로 남는다.

```
[step 1] search_illustrations(tags=['밤', '몽환', '차분'], limit=5)
[step 2] fetch_image_preview(url='https://example.com/art/007')
[step 3] save_to_collection(illustration_ids=['ill_003', 'ill_011'])
```

### 6.2 로그 확인 방법

1. `python main.py` 실행 후 분위기 입력
2. 터미널에서 `[step N]` 줄을 순서대로 읽어 도구 호출 순서·인자를 확인
3. 저장 확인이 필요하면 Supabase 대시보드 → Table Editor → `collection` 테이블에서 행 확인
4. (선택) `python main.py 2>&1 | tee run.log` 로 실행해 `grep "\[step" run.log` 로 호출만 추려 본다
