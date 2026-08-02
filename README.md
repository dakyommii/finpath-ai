# FinPath AI

개인 맞춤형 금융 로드맵 설계 및 정책·금융상품 추천 플랫폼 (해커톤 MVP)

- 설계 문서: `FinPath_AI_금융로드맵_MVP_최종설계문서.md`
- 개발 실행 가이드(Phase별 프롬프트): `FinPath_AI_MVP_개발_실행_가이드.md`

## 프로젝트 구조

```text
FinPath/
├── backend/    FastAPI (API, Rule/Scoring/Roadmap Engine, RAG, LLM)
├── frontend/   Next.js + TypeScript + Tailwind CSS
└── data/       정책·금융상품 시드 데이터 (Phase 2에서 추가 예정)
```

## 실행 방법

### Docker Compose (권장)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (`/health`, `/docs`)
- DB: localhost:5432 (postgres/pgvector)

### 로컬 개별 실행

**DB (Homebrew PostgreSQL 16)**

이 개발 머신은 macOS 13이라 Docker Desktop 설치가 불가능해, 로컬 개발은 Homebrew로 설치한
PostgreSQL 16을 직접 사용한다. 시스템에 이미 다른 PostgreSQL(포트 5432)이 떠 있어
**포트 5433**으로 분리했다.

```bash
brew services start postgresql@16   # 이미 실행 중이면 생략
export PATH="/usr/local/opt/postgresql@16/bin:$PATH"
psql -p 5433 finpath   # 접속 확인 (role/db: finpath / finpath)
```

pgvector 확장은 macOS 13 + 구버전 Xcode 조합에서 Homebrew 빌드가 실패해 아직 설치되지 않았다.
Phase 9(RAG 임베딩)에서 필요해지면 pgvector를 postgresql@16 소스에 직접 빌드하거나,
Supabase/Neon 등 관리형 Postgres(pgvector 기본 지원)로 대체한다.

**Backend**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL은 5433 포트로 이미 설정되어 있음
uvicorn main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose 관련 참고

`docker-compose.yml`의 DB는 컨테이너 내부 네트워크에서 5432를 그대로 쓰므로 로컬 포트 충돌과
무관하다. 다만 이 머신에는 Docker Desktop을 설치할 수 없어(요구사항: macOS 14+) 아직
`docker compose up`으로 직접 검증하지 못했다. 배포 환경에서는 21장 기술스택대로 진행한다.

## 시드 데이터

```bash
cd backend
source venv/bin/activate
python3 -m repositories.seed
```

`data/policies.json`(정책·대출 30건), `data/financial_products.json`(예적금·ISA·연금저축 등 20건)을
DB에 적재한다. title(정책) / provider+title(금융상품) 기준으로 중복 없이 재실행 가능하다.
모든 수치는 데모용 예시이며 실제 신청 전 공식 기관 확인이 필요하다.

## API (Phase 3)

- `POST /api/v1/profiles` — 프로필 생성. 요청 본문에 `user_id`가 없고, 호출 시 새 `User`를 함께
  생성해 응답에 `user_id`를 반환한다. 이후 목표/생애이벤트 생성 시 이 `user_id`를 사용한다.
  (설계 문서에는 인증/로그인 개념이 없어 이렇게 처리함)
- `POST /api/v1/goals` — 목표 생성. `user_id` 필수, 존재하지 않으면 404.
- `POST /api/v1/life-events` — 생애 이벤트 생성. `user_id` 필수, 존재하지 않으면 404.

### 테스트

```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt
psql -p 5433 postgres -c "CREATE DATABASE finpath_test OWNER finpath;"   # 최초 1회
python3 -m pytest -v
```

테스트는 `finpath_test`라는 별도 DB를 사용하며, 각 테스트 종료 후 전체 테이블을 비운다
(개발용 `finpath` DB와 분리되어 있어 시드 데이터에 영향 없음).

## Rule Engine (Phase 4)

`backend/rules/policy_rules.py` + `backend/services/eligibility_service.py`. LLM을 전혀 사용하지
않는 순수 규칙 기반 판별기이며, 정책/금융상품의 `eligibility_rules` / `product_rules` jsonb를
프로필과 비교해 각 평가요소(나이/소득/지역/혼인상태/무주택여부)를 `MET` / `NOT_MET` /
`NEEDS_CONFIRMATION` / `NOT_APPLICABLE`로 판정한다.

- 하나라도 `NOT_MET`이면 `NOT_ELIGIBLE`
- `NOT_MET`은 없지만 `NEEDS_CONFIRMATION`이 있으면 `CONDITIONAL`
- 전부 충족되면 `ELIGIBLE`

`FinancialProfile`에는 "무주택 여부"를 나타내는 필드가 없어(`housing_type`은 현재 거주형태일 뿐
주택 보유 여부를 단정할 수 없음), 무주택 조건이 있는 항목은 임의 추정하지 않고 항상
`NEEDS_CONFIRMATION`(→ `CONDITIONAL`)으로 표시한다.

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/test_eligibility_service.py tests/test_eligibility_integration.py -v
```

## Scoring Engine (Phase 5)

`backend/services/scoring_service.py`. 설계 문서 7.5/11.3의 가중치 공식을 그대로 구현했다.

```text
priority_score = eligibility*0.35 + goal_relevance*0.25 + benefit*0.15
               + urgency*0.10 + risk_reduction*0.10 + life_event_relevance*0.05
               - conflict_penalty
```

- `goal_relevance`, `risk_reduction`: 카테고리별 휴리스틱 가중치 표(하드코딩) 기반. 실제 금액
  최적화가 아닌 MVP용 근사치이며 표에 없는 조합은 기본값(0.3) 사용.
- `benefit`: 금융상품은 `rate_info.max_rate`, 정책은 `benefit_info` 텍스트에서 "OOO만원" 패턴을
  정규식으로 추출해 정규화. 정교한 금액 비교는 아니며 상대적 크기 신호 정도로만 사용.
- `urgency`: `application_end`까지 90일 이내로 다가올수록 1.0에 수렴.
- `conflict_penalty`: 같은 "대출" 카테고리 내에서 1순위를 제외한 항목에 감점(중복/상충 완화).
- `POST /api/v1/recommendations/generate` — `user_id`로 프로필/목표/생애이벤트를 조회해 순위화된
  추천 목록 반환 (`priority_score`는 0~100 스케일).

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/test_scoring_service.py tests/test_recommendations.py -v
```

## Roadmap Planning Engine (Phase 6)

`backend/rules/roadmap_dependencies.py`(단계 템플릿·선행관계) +
`backend/services/roadmap_service.py`(단계별 후보 선정·타임라인 계산) +
`backend/repositories/roadmap_repository.py`(저장).

- 12.2 선행관계(비상자금 → 부채상환 → 자산형성 → 전세자금 → 주택구입)를 기본 골격으로,
  사용자 목표(JEONSE/HOME_PURCHASE/SEED_MONEY)와 생애이벤트(MARRIAGE)에 따라 단계를
  동적으로 추가/제외한다 (모든 사용자에게 동일 순서를 강제하지 않음).
- 각 단계는 Phase 5의 `score_and_rank` 결과에서 카테고리·키워드로 필터링해 최적 후보를 연결한다.
- 타임라인은 단계별 예상 소요기간(개월)을 순차적으로 누적하는 방식으로 계산한다(단순화된 근사).
- 비상자금 단계는 `liquid_assets >= 600만원`이면 자동으로 COMPLETED 처리.
- `POST /api/v1/roadmaps/generate`, `GET /api/v1/roadmaps/{roadmap_id}` API 구현.

**알려진 한계**: "전세자금 마련" 단계가 카테고리를 공유하는 다른 "대출" 항목들의 상호 상충
감점(conflict penalty) 때문에 의도한 대출 상품이 아닌 인접 카테고리(예: 보증금 반환보증 지원)를
추천 후보로 고를 때가 있다. 틀린 추천은 아니지만 Phase 9(LLM 설명) 또는 추후 카테고리 우선순위
정교화에서 개선 여지가 있다.

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/test_roadmap_service.py tests/test_roadmaps_api.py -v
```

## 프론트엔드 — 온보딩 & 금융 진단 (Phase 7)

- `components/onboarding/`: `ProfileForm`(기본정보·소득및자산·주거및부채 3개 섹션),
  `GoalForm`, `LifeEventForm`(선택, 건너뛰기 가능), `OnboardingWizard`(3단계 오케스트레이션)
- `components/diagnosis/`: `FinancialStageCard`, `SavingRateCard`, `GoalProgressCard`
- `lib/api.ts`: 백엔드 API 클라이언트 (`NEXT_PUBLIC_API_BASE_URL` 환경변수로 baseURL 설정)
- 흐름: 온보딩 완료 시 profiles → goals → (선택)life-events → roadmaps/generate,
  recommendations/generate를 순차 호출해 진단 화면에 필요한 데이터를 모두 확보한 뒤 렌더링
- 별도 진단 API는 만들지 않고, 저축률/비상자금충족도/목표달성률/활용가능정책수는
  roadmap·recommendations 응답으로부터 프론트엔드에서 계산 (백엔드 스코프 최소화)

**브라우저로 실제 검증**: claude-in-chrome으로 온보딩 3단계 → 로드맵 생성 → 진단 화면까지
전체 플로우를 직접 실행해 확인했다. 이 과정에서 진단 화면 `<main>`에 배경색이 지정되지 않아
시스템 다크모드에서 카드 내부 텍스트가 거의 안 보이는 대비 문제를 발견해 수정했다
(`bg-white`/`bg-gray-50` 명시).

## 로드맵 타임라인 시각화 & 추천 상세 (Phase 8)

- `components/roadmap/`: `StatusBadge`(9.5 상태 6종), `RoadmapSummary`(9.4 목표 요약),
  `RoadmapProgress`(단계 완료 비율), `RoadmapStepCard`(9.3 카드 포맷), `RoadmapTimeline`(9.1/9.2
  세로형 타임라인)
- `components/recommendations/`: `EligibilityBadge`, `EvidencePanel`(17.4: 조건별 판별 결과,
  예상 혜택, 신청기한, 공식 출처, 면책 문구), `RecommendationCard`
- 백엔드 보강: `RecommendationItem` 응답에 `eligibility_factors`, `benefit_info`,
  `application_end`, `official_url`을 추가해 17.4 화면에 필요한 근거 데이터를 별도 API 없이
  기존 추천 API로 제공 (scoring_service.RankedRecommendation에 필드 추가, 테스트 36건 계속 통과)
- 화면 흐름: 진단 화면 ↔ 로드맵 화면을 토글 버튼으로 전환. 로드맵의 각 단계 카드에서
  "자세히 보기"를 누르면 해당 단계에 연결된 추천 상품/정책의 `RecommendationCard`가 펼쳐짐

**브라우저 실사용 검증**: claude-in-chrome으로 온보딩 → 로드맵 화면 → 단계별 "자세히 보기"까지
직접 클릭해 확인. 이 과정에서 두 가지를 발견:
- `computer` 툴의 좌표/ref 클릭이 이 환경에서 간헐적으로 씹혀(React 이벤트가 등록되지 않는
  것으로 보임) 폼 제출이 안 되는 현상 — `javascript_tool`로 `button.click()`을 직접 호출하는
  방식으로 우회해 검증을 완료함. 실제 사용자가 마우스/터치로 클릭하는 것은 이 이슈와 무관함
  (자동화 도구 자체의 한계로 보임).
- 예금처럼 자격조건이 없는 상품은 EvidencePanel의 "조건별 판별 결과" 섹션이 정상적으로
  숨겨지고(모든 factor가 NOT_APPLICABLE), 실제 연령 조건이 있는 정책(청년내일채움공제)에서는
  판별 결과 표가 정상 표시됨을 확인.

## RAG + LLM 설명 생성 (Phase 9)

이 환경은 **pgvector 미설치**(README 상단 참고) + **LLM API 키 없음** 두 제약이 있어, 둘 다
플러그인 구조로 구현하고 오프라인 폴백을 기본값으로 뒀다. API 키만 넣으면 실제 LLM/임베딩으로
전환된다.

- `services/rag_service.py`:
  - `LocalHashingEmbeddingProvider` (기본값, API 키 불필요): 문자 2-gram 해시 기반 임베딩.
    pgvector 없이 애플리케이션 계층에서 코사인 유사도 계산. 정책+상품 50건 규모라 매 호출마다
    인덱스를 재구성해도 성능 문제 없음.
  - `OpenAIEmbeddingProvider`: `LLM_API_KEY`가 설정되면 자동 전환. **실제 키로 검증하지
    못했음** — OpenAI Embeddings API 규격대로 작성, 키 설정 후 소규모 테스트 필요.
  - `retrieve_documents(db, query, top_k)`가 두 provider 모두에서 동일하게 동작.
- `services/llm_service.py`:
  - `LLM_API_KEY` 미설정 시 `TemplateLLMClient`류 오프라인 폴백이 16.1 프롬프트의 6개 항목
    (이유/행동/효과/완료조건/주의사항/다음단계연결)을 구조화된 입력값만으로 채움.
  - 키 설정 시 `OpenAICompatibleLLMClient`(`/chat/completions` 규격)로 전환하며, 호출 실패 시
    자동으로 템플릿 폴백에 안전하게 대체됨.
  - `_flag_unsupported_numbers`: 설명문의 숫자가 근거 문서나 Rule Engine이 이미 확정한
    텍스트(단계 행동·완료조건) 어디에도 없으면 경고 로그만 남김 (26.3 환각 방지, 하드 실패 아님).
- `roadmap_service.enrich_steps_with_explanations`: 12.1의 10단계로, Rule/Scoring/Roadmap
  Engine이 이미 정한 순서·후보는 바꾸지 않고 `reason`/`sources`만 보강. RAG 질의는 단계
  제목이 아니라 **이미 선택된 추천 후보명**으로 수행해, 설명문이 인용하는 문서와 화면에 뜨는
  추천 카드가 항상 일치하도록 함(처음엔 둘이 어긋나는 문제가 있어 수정함).
- `POST /api/v1/roadmaps/generate`가 이 보강 단계를 자동으로 거침(별도 API 없음).

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/test_rag_service.py tests/test_llm_service.py -v
```

**실제 LLM/임베딩으로 전환하려면**: `backend/.env`의 `LLM_API_KEY`를 실제 키로 바꾸면 된다
(OpenAI 호환 엔드포인트 기준). pgvector는 여전히 미설치 상태이므로, 데이터 규모가 커져
애플리케이션 계층 코사인 유사도로 부족해지면 그때 `rag_service._build_index`/
`retrieve_documents`만 pgvector 기반으로 교체하면 된다.

## 금융 목표 시뮬레이션 (Phase 11)

- `services/simulation_service.py` — 저장된 로드맵(`roadmap.steps`, "변경 전")과, 프로필의
  월 저축액/연 소득/생애이벤트를 덮어써 재계산한 로드맵("변경 후")을 비교한다. 변경 후
  로드맵은 DB에 저장하지 않는다(순수 시뮬레이션).
- `POST /api/v1/roadmaps/{roadmap_id}/simulate` — `monthly_saving`, `annual_income`,
  `life_events` 중 바뀐 값만 전달. 응답에 목표 달성 시점 변화(`months_saved`)와 단계
  추가/삭제(`added_steps`/`removed_steps`), 변경 후 전체 단계 목록을 포함.
- **중요한 버그 수정**: 원래는 `JEONSE_PREP`/`HOME_PURCHASE_PREP` 단계의 소요기간이
  `rules/roadmap_dependencies.py`에 하드코딩된 고정 개월 수여서, **월 저축액을 바꿔도 목표
  달성 시점이 전혀 변하지 않는** 문제가 있었다. 설계 문서 10.2의 핵심 데모 시나리오(저축액
  증가 → 기간 단축)가 실제로는 동작하지 않는 상태였던 것 — 브라우저로 직접 시뮬레이션을
  돌려보다가 발견했다. `roadmap_service._savings_driven_duration_months`를 추가해 목표금액이
  있는 단계는 "(목표금액 − 현재 자산) ÷ 월 저축액"으로 소요기간을 동적으로 계산하도록 수정.

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/test_simulation_service.py tests/test_simulations_api.py -v
```

**브라우저 실사용 검증**: 목표금액 1억원짜리 HOME_PURCHASE 목표로 온보딩 후, 시뮬레이션에서
월 저축액만 100→120만원으로 바꿔 실행 — 목표 달성 시점이 2033-09 → 2032-08로 **13개월
단축**되는 것을 확인. 결혼 이벤트를 함께 켠 다른 케이스에서는 "신혼부부 지원 검토" 단계
추가(+2개월)가 저축액 증가 효과를 상쇄해 오히려 지연으로 나오는 경우도 확인했는데, 이는
버그가 아니라 두 효과가 실제로 반대 방향이라 발생하는 정상적인 결과.

## 통합 테스트 & 예외 처리 (Phase 12, 일부)

데모 데이터 고정(`data/demo_seed.json`)은 보류하고, 통합 테스트와 예외 처리만 진행했다.

- `tests/test_e2e_demo_scenario.py` — 24.1 입력값으로 프로필·목표 생성 → 24.2/24.3처럼 진단·
  7단계 로드맵이 나오는지, 24.5 시뮬레이션(저축액 증가 + 결혼 예정)이 기대한 단계 추가를
  만드는지 API 엔드투엔드로 검증 (24.4 AI 상담은 Phase 10 보류로 제외).
- `tests/test_data_quality.py` — 25장 평가지표에 대응하는 회귀 테스트: `CONDITIONAL` 판정에는
  항상 `NEEDS_CONFIRMATION` 근거가 있는지, 로드맵 단계가 12.2 선행관계(비상자금→부채상환→
  자산형성, 전세자금→주택구입)를 위반하지 않는지, 추천 후보가 연결된 단계에는 출처가
  비어있지 않은지.
- `tests/test_error_handling.py` — 예외 케이스 점검 중 실제로 검증 누락 1건을 발견해 수정함:
  `SimulationRequest`의 `monthly_saving`/`annual_income`이 음수를 그대로 통과시키고 있었다
  (`ProfileInput`과 달리 `Field(ge=0)`이 없었음) → 스키마에 검증 추가. 그 외 잘못된 UUID,
  목표/후보가 전혀 없는 빈 상태, 월 저축액 0(0으로 나누기 위험), 알 수 없는 생애이벤트
  타입 등은 이미 안전하게 처리되고 있음을 확인(500 없이 정상 응답).

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/test_e2e_demo_scenario.py tests/test_data_quality.py tests/test_error_handling.py -v
```

## 저장소 & 배포 (Phase 13)

발표자료(`docs/presentation_outline.md`)는 만들지 않았다 — 사용자 요청으로 배포 준비만 진행.

### GitHub

이 프로젝트는 `/Users/dalkkommi`(홈 디렉토리) 전체를 루트로 하는 기존 git 저장소
(`dakyommii/AlgorithmReview`, 알고리즘 문제풀이용) 안의 하위 폴더였다. GitHub Actions CI를
쓰려면 독립된 저장소가 필요해서, `FinPath/` 자체를 별도 git 저장소로 새로 만들고 새 GitHub
저장소에 올렸다.

- 저장소: https://github.com/dakyommii/finpath-ai (public)
- `.env`, `venv/`, `node_modules/`, `.next/`, `.claude/` 등은 각 디렉토리의 `.gitignore`로
  제외됨 (커밋 전 `git status`로 확인함).

### CI (`.github/workflows/ci.yml`)

- `backend-tests`: GitHub Actions의 `postgres:16` 서비스 컨테이너를 띄우고
  `python3 -m pytest`로 64건 테스트 실행.
- `frontend-build`: `npm ci` → `next lint` → `tsc --noEmit` → `next build`.
- push/PR to `main`마다 자동 실행.
- `tests/conftest.py`가 `DATABASE_URL`을 5433번 포트로 하드코딩하고 있던 걸
  `os.environ.setdefault(...)`로 바꿔서, CI가 표준 5432 포트로 준 값을 덮어쓰지 않게 수정함
  (로컬 개발 환경은 기존처럼 5433 기본값 유지).

### 배포 설정 — 실제 배포 완료

- **Frontend → Vercel**: https://finpath-ai-kyo7.vercel.app (프로덕션, 공개 접근)
- **Backend → Render**: https://finpath-ai-zgh8.onrender.com (Free 웹서비스)
- **DB → Neon**: 카드 인증 없는 서버리스 Postgres

**Render는 Blueprint(`render.yaml`)가 아니라 "New Web Service"로 직접 만들었다.** Blueprint는
DB를 포함하지 않아도 계정에 결제수단 등록을 요구했다(무료 웹서비스 단독 생성은 요구하지
않음 — 계정에 이미 있던 다른 무료 서비스로 확인). `render.yaml`은 IaC 문서 성격으로
레포에 남겨두되, 실제로는 Render 대시보드에서 아래처럼 수동 설정했다:

- Root Directory: `backend`, Dockerfile Path: `Dockerfile`, Build Context: `.` (모두
  `backend` 기준 상대경로 — 처음에 `backend/Dockerfile`로 남겨둬서 `backend/backend`가 되는
  실수를 했다가 수정함)
- 환경변수 5개를 Render 대시보드에서 직접 입력: `DATABASE_URL`(Neon 연결 문자열),
  `LLM_API_KEY=changeme`(오프라인 폴백 유도), `LLM_API_BASE`, `EMBEDDING_MODEL`, `ENV=production`
- DB 스키마/시드는 로컬에서 `DATABASE_URL`을 Neon으로 바꿔 `alembic upgrade head` +
  `python3 -m repositories.seed` 실행해 미리 채워둠

**배포 중 실제로 만나서 고친 버그**:
1. Render 무료 Postgres는 카드 인증 필요 → Neon으로 전환 (위 설명)
2. Dockerfile Path를 `backend/Dockerfile`로 남겨둬서 `backend/backend/Dockerfile`을 찾다 빌드
   실패 → Root Directory 설정 시 하위 경로들도 그에 맞게 상대경로로 재조정해야 함을 확인
3. **CORS**: `main.py`가 `http://localhost:3000`만 허용하고 있어서 배포된 프론트엔드의 모든
   API 호출이 "Failed to fetch"로 실패함 → `allow_origin_regex`로 이 프로젝트의 모든
   `*.vercel.app` 도메인을 허용하도록 수정 (커밋 `a65f37d`)
4. Vercel 팀(`kyo7`)에 Deployment Protection(SSO)이 기본 켜져 있어 로그인 없인 접속 불가
   → `vercel project protection disable finpath-ai --sso`로 해제

브라우저로 온보딩 → 진단 → 로드맵까지 실제 배포 URL에서 전체 플로우 재현해 확인 완료
(테스트로 생성한 데이터는 Neon에서 정리함).

## 키워드 기반 임베딩 추천 보강

설계 문서: `FinPath_AI_키워드_임베딩_추천_설계문서.md`. 온보딩에서 사용자가 선택한 관심사
키워드를 임베딩해 정책/상품 설명과의 유사도를 `goal_relevance` 점수에 보조 신호로
블렌딩한다(기존 표 60% + 유사도 40%).

- 신규 테이블 `interest_keywords` (`user_id`, `axis`, `keyword`), API `POST
  /api/v1/interest-keywords`
- 온보딩 4단계 구성: 프로필 → 목표 → **관심사 키워드(신규)** → 미래이벤트. 5개 축(직업/소득,
  자산형성 우선순위, 주거 걱정, 가족계획, 재무건전성) × 5~6개 키워드, 다중선택, 스킵 가능
- `services/rag_service.keyword_similarity_scores`: 오프라인 해싱 폴백(API 키 없음)일 때는
  항상 빈 dict를 반환해 **자동으로 기존 로직만 사용** — 하위 호환 100% 유지, 회귀 테스트로 검증
- `services/scoring_service.goal_relevance_component`가 `keyword_similarity`를 선택적으로
  받아 블렌딩. Rule Engine(자격 판정)에는 전혀 관여하지 않음
- 테스트 9건 추가(API 3 + rag_service 3 + scoring_service 3), **전체 73건 통과**
- 로컬 브라우저로 4단계 온보딩 전체 플로우 실행 및 DB 저장 확인 완료. 실제 임베딩 품질은
  API 키가 없어 미검증 (가짜 provider로 블렌딩 로직 자체는 단위 테스트로 검증함)

## 개발 진행 상태

- Phase 0: 프로젝트 스캐폴딩 완료
- Phase 1: DB 스키마 구축 완료 (로컬 PostgreSQL 16, 포트 5433 — 시스템에 이미 5432를 쓰는 다른
  PostgreSQL이 있어 분리)
- Phase 2: 정책·금융상품 시드 데이터 구축 완료 (정책 30건, 금융상품 20건)
- Phase 3: 프로필·목표·생애이벤트 온보딩 API 완료 (테스트 10건 통과)
- Phase 4: Rule Engine(자격조건 판별) 완료 (테스트 9건 추가, 총 19건 통과)
- Phase 5: Scoring Engine + 추천 생성 API 완료 (테스트 8건 추가, 총 27건 통과)
- Phase 6: Roadmap Planning Engine + 로드맵 생성/조회 API 완료 (테스트 9건 추가, 총 36건 통과)
- Phase 7: 온보딩 위저드 + 금융 진단 화면 완료, 브라우저 실사용 검증 및 다크모드 대비 버그 수정
- Phase 8: 로드맵 타임라인 시각화 + 추천 상세(EvidencePanel) 완료, 브라우저 실사용 검증
- Phase 9: RAG(오프라인 폴백 임베딩) + LLM 설명 생성(오프라인 폴백) 완료 (테스트 8건 추가,
  총 44건 통과). 실제 LLM/임베딩 API 키 연동은 미검증 상태로 남겨둠.
- Phase 10: **보류** — AI 상담 챗봇은 추후 고도화 시점에 별도로 연다 (사용자 결정, 2026-07-31).
  다만 이때 필요한 RAG(`retrieve_documents`)와 LLM 클라이언트(`get_llm_client`)는 Phase 9에서
  이미 구현되어 있어, 여는 시점엔 `api/chat.py` + 16.2 프롬프트만 추가하면 된다.
- Phase 11: 금융 목표 시뮬레이션 완료 (테스트 8건 추가, 총 52건 통과). 브라우저 실사용 검증.
- Phase 12: 통합 테스트 + 예외 처리 완료, **데모 데이터 고정은 보류**(사용자 결정,
  2026-07-31) (테스트 12건 추가, 총 64건 통과). 검증 중 `SimulationRequest`의 음수값 미검증
  버그 발견 및 수정.
- Phase 13: **실제 배포 완료**(발표자료는 보류, 사용자 결정, 2026-08-01). 독립 GitHub 저장소
  신설(`dakyommii/finpath-ai`) + GitHub Actions CI(그린) + Vercel(프론트엔드)·Render
  (백엔드)·Neon(DB)에 실제로 배포하고 브라우저로 전체 플로우 검증까지 완료.
  - Frontend: https://finpath-ai-kyo7.vercel.app
  - Backend: https://finpath-ai-zgh8.onrender.com

FinPath_AI_MVP_개발_실행_가이드.md의 Phase 0~13(발표자료 제외)을 모두 진행했고, 실제
클라우드 배포까지 마쳤다. 남은 항목은 Phase 10(AI 상담 챗봇, 보류)과 Phase 13의 발표자료뿐이다.
