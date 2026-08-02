# FinPath AI — 키워드 기반 임베딩 추천 보강 설계 문서

> 목적: 온보딩에서 사용자가 선택한 키워드를 텍스트로 조합해 임베딩하고, 정책/금융상품
> 설명 텍스트와의 유사도를 Scoring Engine의 `goal_relevance`에 보조 신호로 반영해
> 추천의 개인화 수준을 높인다.
>
> 전제: 실제 LLM/임베딩 API 키가 `LLM_API_KEY`에 설정되어 `rag_service.OpenAIEmbeddingProvider`가
> 활성화된 상태에서만 의미가 있다. 오프라인 해싱 폴백에서는 의미 기반 유사도를 계산할 수
> 없으므로, 이 기능은 API 키가 없을 때 기존 하드코딩 표 로직으로 자동 폴백한다.

---

## 1. 배경 및 설계 원칙

### 1.1 왜 필요한가

기존 `goal_relevance_component`는 목표 유형(4종) × 카테고리(13종)의 고정 가중치 표로
동작한다. 이 표는:

- 사용자별 차이를 전혀 반영하지 못한다 (같은 `SEED_MONEY` 목표면 모두 동일한 점수).
- 새 정책/카테고리가 추가될 때마다 표를 수동으로 갱신해야 한다.
- "곧 결혼하는데 프리랜서로 전환 준비 중"처럼 조합적인 상황을 표현할 방법이 없다.

### 1.2 왜 자유 서술이 아닌 키워드 선택인가

자유 서술은 텍스트 다양성은 높지만, 오탈자·주제 이탈·악의적 입력 등 통제가 어렵다.
대신 **도메인 전문가가 큐레이션한 키워드를 다중 선택**하게 하면:

- 어휘가 고정되어 있어 예측 가능하고 검증하기 쉽다.
- 축(axis)을 여러 개 두고 각 축에서 복수 선택하게 하면, 표현 가능한 조합 수가
  충분히 많아져 자유 서술에 준하는 다양성을 얻을 수 있다.
- 임베딩이 이해하기 좋은 문장 형태로 미리 다듬어져 있어 품질이 안정적이다.

### 1.3 설계 원칙 (설계 문서 11장과 동일한 원칙 적용)

- **자격 판정(Rule Engine)에는 절대 관여하지 않는다.** 임베딩 유사도는 오직
  `goal_relevance`(우선순위 점수의 일부)에만 영향을 준다.
- **완전 대체가 아닌 블렌딩.** 기존 하드코딩 표를 안전망으로 유지하고, 임베딩 유사도는
  보정치로만 더한다. 임베딩이 이상하게 나와도 결과가 크게 튀지 않는다.
- **API 키가 없으면 자동으로 기존 로직만 사용한다.** 새 기능이 없던 시절의 동작을
  깨지 않는다 (하위 호환).
- **선택은 선택 사항이다.** 사용자가 키워드를 하나도 안 고르면 기존 표 기반 점수만 쓴다.

---

## 2. 키워드 Taxonomy (확정)

5개 축, 축당 5~6개, 각 축 내에서 다중 선택 가능. 구조화 필드(나이/지역/혼인여부/목표유형)와
겹치지 않는 축만 선정했다 — 겹치면 임베딩 신호가 희석된다.

| 축 (axis) | 키워드 (keyword) |
|---|---|
| `CAREER` 직업/소득 상황 | 이직 준비중 · 프리랜서/1인사업 · 창업 준비중 · 사회초년생(첫 직장) · 소득이 불규칙함 · 안정적인 정규직 |
| `ASSET_PRIORITY` 자산형성 우선순위 | 목돈을 빠르게 모으고 싶음 · 절세 혜택이 중요함 · 장기 노후 준비 · 원금 손실 위험은 피하고 싶음 · 투자 수익률을 더 신경씀 |
| `HOUSING_CONCERN` 주거 관련 걱정 | 전세사기가 걱정됨 · 대출 이자 부담이 큼 · 보증금 마련이 급함 · 월세 부담을 줄이고 싶음 · 자가 마련이 최종 목표 |
| `FAMILY_PLAN` 가족/생애 계획 | 곧 결혼 예정 · 이미 신혼부부 · 출산·육아 계획 있음 · 1인 가구 유지 예정 · 부모님과 함께 거주중 |
| `FINANCIAL_HEALTH` 재무 건전성 우려 | 기존 대출을 정리하고 싶음 · 신용점수 관리가 필요함 · 비상자금이 부족함 · 지출 관리가 어려움 |

축 키(`CAREER` 등)는 내부 코드/DB 저장용이며 화면에는 한글 라벨만 노출한다.

---

## 3. 데이터 모델

### 3.1 신규 테이블: `interest_keywords`

`life_events`와 동일한 패턴(사용자당 여러 행, 단순 문자열 필드)으로 설계한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| axis | varchar | 축 키 (`CAREER`, `ASSET_PRIORITY`, `HOUSING_CONCERN`, `FAMILY_PLAN`, `FINANCIAL_HEALTH`) |
| keyword | varchar | 선택한 키워드 원문 (한글 라벨 그대로 저장 — 임베딩에 바로 쓸 것이므로) |

정책/상품 테이블처럼 별도 마스터 테이블로 키워드를 관리하지 않고, 프런트엔드
상수(`KEYWORD_TAXONOMY`)와 백엔드 상수를 동일한 값으로 하드코딩 동기화한다. 이 프로젝트
규모(축 5개, 키워드 30개 내외)에서는 마스터 테이블 도입이 과설계라고 판단.

### 3.2 마이그레이션

Alembic 마이그레이션 1개 추가 (`create interest_keywords table`).

---

## 4. 백엔드 설계

### 4.1 스키마 (`schemas/interest_keyword.py`)

```python
class InterestKeywordInput(BaseModel):
    axis: str
    keyword: str

class InterestKeywordCreate(InterestKeywordInput):
    user_id: uuid.UUID
```

`POST /api/v1/interest-keywords`는 배열을 한 번에 받는다 (온보딩에서 여러 개를 동시에
선택하므로 축별로 여러 번 호출하지 않는다):

```json
{
  "user_id": "...",
  "keywords": [
    {"axis": "CAREER", "keyword": "이직 준비중"},
    {"axis": "FAMILY_PLAN", "keyword": "곧 결혼 예정"}
  ]
}
```

### 4.2 임베딩 유사도 계산

`services/rag_service.py`에 함수 추가:

```python
def build_user_interest_text(keywords: list[str]) -> str:
    return " ".join(keywords)

def keyword_similarity_scores(db, keywords: list[str], candidates: list[tuple[str, str]]) -> dict[str, float]:
    """candidates: [(item_id, document_text), ...]. 반환: {item_id: 0~1 유사도}."""
```

`rag_service._document_text`가 이미 정책/상품의 title+category+description+benefit_info를
합친 텍스트를 만들고 있으므로, 이 함수를 재사용해 후보 문서 텍스트를 만들고
`get_embedding_provider().embed(...)`로 사용자 관심사 텍스트와 각 후보를 임베딩해
코사인 유사도를 계산한다.

**주의**: `LocalHashingEmbeddingProvider`(오프라인 폴백)로는 의미 유사도를 계산할 수
없다는 게 이 문서의 전제다. `get_embedding_provider()`가 `LocalHashingEmbeddingProvider`를
반환하는 경우, `keyword_similarity_scores`는 계산을 생략하고 빈 dict를 반환해
아래 블렌딩 로직이 자동으로 기존 표만 쓰도록 한다.

### 4.3 Scoring Engine 블렌딩 (`services/scoring_service.py`)

`goal_relevance_component`를 확장한다:

```python
KEYWORD_BLEND_WEIGHT = 0.4  # 임베딩 유사도가 있을 때, 기존 표 대비 반영 비율

def goal_relevance_component(goal_types, category, keyword_similarity: Optional[float] = None) -> float:
    table_score = ...  # 기존 로직 그대로 (안전망)
    if keyword_similarity is None:
        return table_score
    return table_score * (1 - KEYWORD_BLEND_WEIGHT) + keyword_similarity * KEYWORD_BLEND_WEIGHT
```

`score_and_rank`는 호출 전에 `keyword_similarity_scores`로 전체 후보의 유사도를 한 번에
계산해두고, 후보별로 해당 값을 `goal_relevance_component`에 넘긴다. 키워드가 없거나
오프라인 폴백이면 `keyword_similarity=None`이 전달되어 기존 동작과 100% 동일하다.

### 4.4 API 연동 지점

- `POST /api/v1/roadmaps/generate`, `POST /api/v1/recommendations/generate` 두 곳 모두
  `interest_keywords` 테이블에서 `user_id` 기준 조회 후 `score_and_rank`에 전달하도록 수정.
- 기존 시그니처 `score_and_rank(db, profile, goals, life_events)`에
  `keywords: Optional[list[str]] = None` 인자를 추가 (하위 호환 유지).

---

## 5. 프론트엔드 설계

### 5.1 온보딩 4단계 추가

`OnboardingWizard`에 4번째 단계 `KeywordForm`을 삽입한다 (프로필 → 목표 →
**관심사 키워드** → 미래이벤트, 또는 목표 → 미래이벤트 → **관심사 키워드** 순서는
확정 필요 — 5.2 참고).

`components/onboarding/KeywordForm.tsx`:
- 5개 축을 섹션으로 나눠 각각 칩(chip) 형태 다중선택 UI 렌더링
- 전체 스킵 가능 ("나중에 선택할게요" 버튼) — 선택 사항이므로 강제하지 않음
- 선택 결과를 `{axis, keyword}[]` 배열로 부모에 전달

### 5.2 온보딩 순서 확정 필요 사항

현재 순서: Profile → Goal → LifeEvent. 여기에 Keyword를 어디에 넣을지 결정 필요:

- **안**: Profile → Goal → **Keyword** → LifeEvent (목표 직후에 관심사를 물어보는 게
  자연스러움, LifeEvent는 이미 "선택 사항" 단계라 마지막에 두는 게 UX상 일관적)

이 설계 문서에서는 위 안을 기본값으로 채택한다. 구현 시 이견 있으면 조정.

### 5.3 API 클라이언트 (`lib/api.ts`)

```typescript
export function createInterestKeywords(userId: string, keywords: {axis: string; keyword: string}[]) {
  return postJson("/api/v1/interest-keywords", { user_id: userId, keywords });
}
```

### 5.4 타입 추가 (`types/finpath.ts`)

```typescript
export const KEYWORD_TAXONOMY = {
  CAREER: ["이직 준비중", "프리랜서/1인사업", "창업 준비중", "사회초년생(첫 직장)", "소득이 불규칙함", "안정적인 정규직"],
  ASSET_PRIORITY: ["목돈을 빠르게 모으고 싶음", "절세 혜택이 중요함", "장기 노후 준비", "원금 손실 위험은 피하고 싶음", "투자 수익률을 더 신경씀"],
  HOUSING_CONCERN: ["전세사기가 걱정됨", "대출 이자 부담이 큼", "보증금 마련이 급함", "월세 부담을 줄이고 싶음", "자가 마련이 최종 목표"],
  FAMILY_PLAN: ["곧 결혼 예정", "이미 신혼부부", "출산·육아 계획 있음", "1인 가구 유지 예정", "부모님과 함께 거주중"],
  FINANCIAL_HEALTH: ["기존 대출을 정리하고 싶음", "신용점수 관리가 필요함", "비상자금이 부족함", "지출 관리가 어려움"],
} as const;
```

백엔드 상수와 값이 동일해야 한다 (3.1의 "동기화" 언급 참고). 백엔드는 값 검증을 하지
않고 그대로 저장하므로, 프런트가 이 표에서 벗어난 값을 보내지 않도록 UI로만 제어한다.

---

## 6. 테스트 계획

- **backend**
  - `test_rag_service.py`: `keyword_similarity_scores`가 실제 OpenAI 키 없이(해싱 폴백)
    호출되면 빈 dict를 반환하는지, 관련 키워드와 무관 키워드 간 상대적 유사도 순서가
    맞는지(모킹된 임베딩 provider로 검증)
  - `test_scoring_service.py`: `keyword_similarity=None`일 때 기존 결과와 완전히 동일한지
    (회귀 테스트), `keyword_similarity` 값이 주어졌을 때 블렌딩 공식이 정확한지
  - API 테스트: `POST /api/v1/interest-keywords` 정상 생성/404 케이스
- **frontend**: `KeywordForm` 렌더링, 다중 선택 상태 관리, 스킵 동작

## 7. 구현 순서 제안

1. DB 마이그레이션 + 모델 + 스키마 + API (`interest-keywords`)
2. `rag_service.keyword_similarity_scores` + 오프라인 폴백 시 빈 dict 반환 로직
3. `scoring_service.goal_relevance_component` 블렌딩 + `score_and_rank` 연동
4. 프론트 `KeywordForm` + 온보딩 순서 변경 + API 연동
5. 테스트 작성 및 전체 회귀 테스트 확인 (기존 64건 계속 통과해야 함)
6. 실제 API 키로 임베딩 품질 수동 검증 (해싱 폴백으로는 검증 불가한 부분)
