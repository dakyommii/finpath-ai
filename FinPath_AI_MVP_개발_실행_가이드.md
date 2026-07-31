# FinPath AI MVP 개발 실행 가이드

> 본 문서는 `FinPath_AI_금융로드맵_MVP_최종설계문서.md`(이하 "설계 문서")를 실제 코드로 구현하기 위한
> 단계별 개발 계획과, 각 단계에서 Claude Code(또는 유사 AI 코딩 도구)에 바로 입력할 수 있는 프롬프트를 정리한 문서다.
>
> 사용법: 각 Phase를 순서대로 진행하며, "프롬프트" 블록을 그대로 복사해 AI 코딩 도구에 붙여넣고 실행한다.
> 각 프롬프트는 이전 Phase의 산출물을 전제로 작성되어 있으므로 순서를 건너뛰지 않는다.

---

## 0. 사전 준비

### 0.1 진행 원칙

- 설계 문서 11장의 원칙(Rule Engine + Scoring Engine + RAG + LLM 역할 분리)을 코드 구조에도 그대로 반영한다.
- 각 Phase는 "동작하는 최소 단위"를 목표로 한다. 다음 Phase로 넘어가기 전에 반드시 실행/테스트로 확인한다.
- AI 코딩 도구에는 매번 설계 문서의 관련 장 번호를 함께 제시하여 임의 설계 변경을 막는다.

### 0.2 저장소 초기 구조

```text
FinPath/
├── FinPath_AI_금융로드맵_MVP_최종설계문서.md
├── FinPath_AI_MVP_개발_실행_가이드.md   (본 문서)
├── backend/
├── frontend/
├── data/
└── docs/
```

### Phase 0 프롬프트 — 프로젝트 스캐폴딩

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md의 19장(백엔드 구조), 21장(기술 스택)을 참고해서
프로젝트 초기 구조를 만들어줘.

요구사항:
1. backend/ 디렉토리에 FastAPI 프로젝트 생성
   - api/, services/, rules/, models/, schemas/, repositories/, prompts/ 폴더 구성 (19.2 구조 그대로)
   - SQLAlchemy + Pydantic 설정
   - PostgreSQL 연결 설정 (환경변수 기반, .env.example 포함)
2. frontend/ 디렉토리에 Next.js + TypeScript + Tailwind CSS 프로젝트 생성
   - 18장의 컴포넌트 폴더 구조(onboarding/, diagnosis/, roadmap/, recommendations/, simulation/, chat/) 생성
3. docker-compose.yml 작성: PostgreSQL(pgvector 확장 포함), backend, frontend 서비스 정의
4. 루트에 README.md 작성 (실행 방법만 간단히)

지금은 비즈니스 로직을 구현하지 말고, 실행 가능한 빈 뼈대만 만들어줘.
완료 후 docker-compose up으로 세 서비스가 기동되는지 확인해줘.
```

---

## Phase 1. 데이터베이스 스키마 구축

**목표**: 설계 문서 14장의 테이블을 실제 마이그레이션으로 구현.

**산출물**: `users`, `financial_profiles`, `financial_goals`, `life_events`, `policies`, `financial_products`, `roadmap_steps` 테이블 + Alembic 마이그레이션.

### Phase 1 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 14장(데이터베이스 설계)을 참고해서
backend/models/ 에 SQLAlchemy 모델을 작성하고 Alembic 마이그레이션을 생성해줘.

대상 테이블: users, financial_profiles, financial_goals, life_events,
policies, financial_products, roadmap_steps (14.1~14.7 스키마 그대로 컬럼 구성)

추가 요구사항:
- roadmap_steps는 12.3의 로드맵 출력 스키마(JSON)와 정합되도록 status, related_items,
  sources 필드를 jsonb로 추가해줘.
- policies, financial_products의 eligibility_rules / product_rules는 jsonb로,
  13.1/13.2의 필드(신청기간, 공식 URL, 최종 확인일 등)를 빠짐없이 반영해줘.
- 각 모델에 대응하는 Pydantic 스키마(schemas/)도 함께 만들어줘.
- 마이그레이션 적용 후 psql로 테이블 목록을 확인해줘.
```

---

## Phase 2. 정책·금융상품 시드 데이터 구축

**목표**: 설계 문서 13.3에 따라 데모용 대표 정책/상품 30~100건을 고품질로 정제.

**산출물**: `data/policies.json`, `data/financial_products.json`, 시드 스크립트.

### Phase 2 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 7.3(정책 및 금융상품 추천 범위), 13장(데이터 설계)을
참고해서 데모용 시드 데이터를 만들어줘.

요구사항:
1. data/policies.json: 청년 자산형성, 청년/신혼부부 전세대출, 주거비 지원, 신혼부부 지원,
   출산·양육 지원 등 7.3의 카테고리를 아우르는 정책 30건 (실제 존재하는 유형을 참고해
   합리적인 자격조건·혜택 구조로 작성, 출처 URL 필드는 플레이스홀더로 표시)
   - 각 정책은 13.1 필드(연령/소득/지역/혼인/주택보유 조건, 신청기간, 신청기관, 준비서류,
     최종 확인일 등)를 모두 포함
2. data/financial_products.json: 예적금, 청년 자산형성 계좌, ISA, 연금저축 등 상품 20건
   - 13.2 필드(금리, 우대조건, 세제혜택 등) 포함
3. backend/repositories/ 에 시드 스크립트(seed.py) 작성: json을 읽어 Phase 1의
   policies / financial_products 테이블에 upsert
4. 시드 실행 후 DB에 데이터가 정상 적재되었는지 카운트로 확인해줘.

주의: 실제 금리·지원금액 수치를 단정적으로 지어내지 말고, "데모용 예시 데이터이며
실제 신청 전 공식 기관 확인이 필요함"이라는 주석을 시드 파일 상단에 명시해줘.
```

---

## Phase 3. 프로필·목표 온보딩 API

**목표**: 설계 문서 7.1, 15.1~15.2의 프로필/목표 생성 API 구현.

### Phase 3 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 7.1(금융 프로필 생성), 15.1~15.2(API 설계)를
참고해서 backend/api/profiles.py, backend/api/goals.py를 구현해줘.

요구사항:
- POST /api/v1/profiles : 15.1 Request 스키마 그대로. 7.1의 개인정보 최소화 원칙에 따라
  주민번호·계좌번호는 받지 않고, income/assets는 구간 입력도 허용하도록 스키마 설계
- POST /api/v1/goals : 15.2 Request 스키마 그대로
- POST /api/v1/life-events : life_events 테이블(14.4)에 대응하는 생성 API 추가
  (설계 문서에 명시적 엔드포인트는 없으나 14.4 스키마를 활용하기 위해 필요)
- Pydantic validation: age, income 등은 양수만 허용
- 각 API에 대한 pytest 테스트 작성 (정상 케이스 + 필수값 누락 케이스)

완료 후 pytest 실행 결과를 보여줘.
```

---

## Phase 4. Rule Engine (자격조건 판별)

**목표**: 설계 문서 11.2, 7.4의 Eligibility 판별 로직 구현. **이 엔진은 LLM을 사용하지 않는다.**

### Phase 4 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 11.2(Rule Engine), 7.4(Eligibility Score)를
참고해서 backend/rules/policy_rules.py, backend/services/eligibility_service.py를 구현해줘.

요구사항:
- 순수 규칙 기반 판별만 수행 (LLM 호출 절대 없음 — 26.3 환각 방지 원칙 준수)
- 입력: financial_profile + financial_goals + policy(또는 product)의 eligibility_rules(jsonb)
- 출력: 7.4의 3단계 상태
  - ELIGIBLE (신청 가능)
  - CONDITIONAL (조건부 가능)
  - NOT_ELIGIBLE (현재 신청 어려움)
  - 판별 근거로 7.4 표처럼 평가요소별 충족 여부(나이/소득/거주/무주택 등)를 함께 반환
- 무주택 조건처럼 프로필에 없는 정보는 "사용자 확인 필요"로 명시적으로 표시 (임의 추정 금지)
- 전체 policies/financial_products에 대해 배치로 판별하는
  evaluate_all(profile, goals) -> list[EligibilityResult] 함수 작성
- 단위 테스트: 나이 초과, 소득 초과, 지역 불일치, 조건 충족 케이스 각각 작성

완료 후 테스트를 실행해서 결과를 보여줘.
```

---

## Phase 5. Scoring Engine (우선순위 계산)

**목표**: 설계 문서 7.5, 11.3의 Priority Score 구현.

### Phase 5 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 7.5(추천 우선순위), 11.3(Scoring Engine)을
참고해서 backend/services/scoring_service.py를 구현해줘.

요구사항:
- 11.3의 가중치 공식 그대로 구현:
  score = eligibility_score*0.35 + goal_relevance*0.25 + benefit_score*0.15
        + urgency_score*0.10 + risk_reduction*0.10 + life_event_relevance*0.05
- 7.5의 Conflict Penalty(중복/상충 감점)도 별도 항목으로 추가해 최종 priority_score 계산
- 각 하위 점수 계산 로직:
  - eligibility_score: Phase 4의 ELIGIBLE/CONDITIONAL/NOT_ELIGIBLE을 1.0/0.5/0.0으로 매핑
  - goal_relevance: financial_goals.goal_type과 policy.category 매칭도
  - urgency_score: policy.application_end까지 남은 기간이 짧을수록 높게
  - life_event_relevance: life_events와 정책 대상(신혼부부/출산 등) 매칭
- Phase 4의 evaluate_all 결과를 받아 score_and_rank(profile, goals, life_events, eligibility_results)
  -> list[RankedRecommendation] 함수로 통합
- 단위 테스트로 우선순위가 기대한 순서대로 나오는지 검증

완료 후 15.3(추천 생성 API)의 Response 스키마에 맞춰
backend/api/recommendations.py의 POST /api/v1/recommendations/generate를 구현하고
테스트해줘.
```

---

## Phase 6. Roadmap Planning Engine

**목표**: 설계 문서 8장, 12장의 로드맵 생성 로직 구현. Rule/Scoring Engine 결과를 바탕으로 단계·순서·의존관계를 구성.

### Phase 6 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 8장(개인 맞춤 금융 로드맵), 12장(로드맵 생성 로직)을
참고해서 backend/services/roadmap_service.py, backend/rules/roadmap_dependencies.py를 구현해줘.

요구사항:
- 12.1의 10단계 절차 중 1~9단계(LLM 설명 생성 제외)를 구현
- 12.2의 선행관계 예시(비상자금 확보 → 고금리 부채 상환 → 자산형성 상품 가입 →
  전세자금 마련 → 주택구입 준비)를 기본 템플릿으로 하되, 목표 유형(goal_type)과
  Phase 5의 랭킹 결과에 따라 단계를 추가/삭제/재정렬하는 로직 작성
- life_events(결혼 예정 등)가 있으면 5.2 시나리오처럼 관련 단계를 삽입
  (예: 결혼 예정 시 "신혼부부 전세지원 검토", "공동자산 계획" 단계 추가)
- 각 단계는 12.3 JSON 스키마의 필드를 모두 채워서 생성:
  order, title, status, recommended_start, expected_end, action, reason,
  completion_condition, related_items, sources
  (reason 필드는 이 단계에서는 템플릿 문자열로 채우고, Phase 9에서 LLM이 다듬도록 남겨둠)
- generate_roadmap(profile, goals, life_events) -> RoadmapJSON 함수로 통합
- Phase 1의 roadmap_steps 테이블에 저장하는 repository 함수 작성
- 15.4/15.5(로드맵 생성/조회 API) 구현: POST /api/v1/roadmaps/generate, GET /api/v1/roadmaps/{id}

테스트: 5.1 기본 시나리오(27세, 서울, 연봉 3800만원 등) 입력 시 8.2와 유사한
7단계 로드맵이 생성되는지 검증하는 통합 테스트를 작성하고 실행해줘.
```

---

## Phase 7. 프론트엔드 — 온보딩 & 금융 진단 화면

**목표**: 설계 문서 17.1, 17.2, 18장의 온보딩/진단 UI 구현.

### Phase 7 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 17.1(온보딩), 17.2(금융 진단 화면), 18장(컴포넌트 구조)을
참고해서 frontend/components/onboarding/, frontend/components/diagnosis/ 를 구현해줘.

요구사항:
- ProfileForm, GoalForm, LifeEventForm: 17.1의 5단계 흐름(기본정보 → 소득/자산 →
  주거/부채 → 금융목표 → 미래이벤트)을 하나의 온보딩 위저드로 구성
  - 7.1 입력 항목 표를 그대로 폼 필드로 매핑, 필수/선택 구분 반영
  - 제출 시 Phase 3의 POST /api/v1/profiles, /goals, /life-events 순차 호출
- FinancialStageCard, SavingRateCard, GoalProgressCard: 17.2에 명시된 지표
  (현재 금융 단계, 저축률, 비상자금 충족도, 목표 달성률, 활용 가능 정책 개수,
  우선 해결 과제)를 표시
- Tailwind CSS로 스타일링, 반응형 레이아웃
- 폼 검증 에러 메시지 표시

완료 후 개발 서버를 실행해서 온보딩 → 진단 화면까지 실제로 입력이 흘러가는지
브라우저에서 확인해줘.
```

---

## Phase 8. 프론트엔드 — 로드맵 타임라인 시각화

**목표**: 설계 문서 9장의 타임라인/카드/진행률 UI 구현.

### Phase 8 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 9장(로드맵 시각화 설계), 17.3(메인 로드맵 화면),
17.4(추천 상세 화면)을 참고해서 frontend/components/roadmap/, recommendations/ 를 구현해줘.

요구사항:
- RoadmapTimeline: 9.1/9.2 스타일의 세로형(또는 가로형) 타임라인. React Flow 또는
  SVG 기반으로 구현 (21장 기술스택 참고)
- RoadmapStepCard: 9.3 카드 포맷 그대로
  (상태, 신청 가능성, 우선순위, 예상 효과, 추천 이유, 완료 조건)
- RoadmapProgress: 9.4의 목표 달성률 프로그레스 바
- 9.5 상태 색상/아이콘 체계(완료/진행중/지금권장/예정/확인필요/신청불가)를
  일관된 배지 컴포넌트(StatusBadge)로 분리
- RecommendationCard, EligibilityBadge, EvidencePanel: 17.4의 추천 상세 화면 구성
  (신청 가능 상태, 조건별 판별 결과, 예상 혜택, 신청기간, 준비서류, 공식 출처)
- Phase 6의 GET /api/v1/roadmaps/{id} 응답을 그대로 렌더링

완료 후 Phase 6에서 만든 데모 시나리오 데이터로 실제 화면을 렌더링해서
캡처 또는 확인해줘.
```

---

## Phase 9. RAG 파이프라인 + LLM 설명 생성

**목표**: 설계 문서 11.4, 11.5, 16.1의 RAG/LLM 서비스 구현. **LLM은 설명 역할만 수행하고 자격 판정에는 관여하지 않는다.**

### Phase 9 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 11.4(RAG), 11.5(LLM 역할), 16.1(로드맵 설명 프롬프트)을
참고해서 backend/services/rag_service.py, backend/services/llm_service.py를 구현해줘.

요구사항:
1. RAG 파이프라인 (11.4 처리 흐름):
   - Phase 2 시드 데이터의 정책/상품 설명 텍스트를 청크로 분할
   - 임베딩 생성 (BGE-M3 또는 OpenAI 임베딩 API, 21장 기술스택 참고) 후 pgvector에 저장
   - 사용자 질의/프로필 기반 유사도 검색 함수 retrieve_documents(query, profile) 작성
2. LLM 설명 서비스 (11.5, 16.1):
   - 16.1 프롬프트를 시스템 프롬프트로 사용, backend/prompts/roadmap_explanation.py에 저장
   - Phase 6에서 생성된 로드맵 JSON의 각 step에 대해 reason/action/주의사항 등을
     자연어로 다듬어 채우는 explain_roadmap_step(step, retrieved_docs) 함수 작성
   - 11.5 "LLM이 하지 않는 역할" 준수: 자격조건 판정, 금리/수치 임의 생성, 대출승인 보장
     등을 금지하는 문구를 프롬프트에 명시하고, 출력 후 숫자가 RAG 문서에 없으면
     경고 로그를 남기는 간단한 검증 로직 추가
3. Rule/Scoring Engine이 확정한 순서와 후보를 LLM이 변경하지 못하도록,
   LLM 입력에는 이미 정렬된 로드맵 JSON만 전달하고 출력은 텍스트 필드만 갱신하도록 제한

테스트: RAG 검색이 관련 문서를 반환하는지, LLM 설명 생성이 26.2(근거 표시) 요건대로
출처와 기준일을 포함하는지 확인하는 테스트를 작성해줘.
```

---

## Phase 10. AI 상담 챗봇

**목표**: 설계 문서 16.2, 15.7, 17.6의 상담 기능 구현.

### Phase 10 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 16.2(상담 프롬프트), 15.7(AI 상담 API),
17.6(AI 상담 화면)을 참고해서 backend/api/chat.py와 frontend/components/chat/를 구현해줘.

요구사항:
- POST /api/v1/chat (15.7 스키마): roadmap_id, question을 받아
  1) Phase 9의 retrieve_documents로 관련 문서 검색
  2) 로드맵 + 프로필 + 검색 문서를 컨텍스트로 16.2 프롬프트 규칙에 따라 답변 생성
     (결론 우선, 사용자 조건 반영, 근거/출처 제시, 대안 비교, 불확실 정보 단정 금지,
     공식기관 확인 안내)
- ChatPanel, SuggestedQuestions 컴포넌트: 17.6의 추천 질문 예시를 기본 제공
  ("왜 이 상품이 1순위인가요?" 등)
- 대화 컨텍스트 유지: 같은 roadmap_id 내 이전 질문/답변을 함께 전달

테스트: 24.4 데모 질문("왜 ISA보다 청년 자산형성 상품이 먼저인가요?")을 입력했을 때
근거와 출처가 포함된 답변이 나오는지 확인해줘.
```

---

## Phase 11. 시뮬레이션 기능

**목표**: 설계 문서 10장, 15.6, 17.5의 조건 변경 시뮬레이션 구현.

### Phase 11 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 10장(금융 목표 시뮬레이션), 15.6(시뮬레이션 API),
17.5(시뮬레이션 화면)을 참고해서 backend/services/simulation_service.py,
backend/api/simulations.py, frontend/components/simulation/을 구현해줘.

요구사항:
- POST /api/v1/roadmaps/{roadmap_id}/simulate (15.6 Request 스키마):
  monthly_saving, annual_income, life_events 변경을 입력받음
- 변경된 조건으로 Phase 4(Rule)→5(Scoring)→6(Roadmap) 파이프라인을 재실행하여
  10.3에 명시된 항목(상품 자격, 우선순위, 목표 달성 시점, 월별 필요 저축액,
  대출 규모, 적용 정책, 로드맵 단계 변경)을 재계산
- 변경 전/후 비교 결과 반환 (10.2 포맷: "월 저축액 100만원 → 목표달성 2030-06",
  "120만원 → 2029-11", "단축 7개월" 같은 diff)
- ScenarioControls, BeforeAfterSummary, RoadmapDiff 컴포넌트:
  17.5의 입력 컨트롤(연봉/월저축액/목표금액/목표시점/결혼여부/전세·주택계획)과
  결과(달성시점 변화, 로드맵 단계 변화, 추천상품 변화, 혜택 변화) 표시

테스트: 24.5 데모 시나리오(월 저축액 100→120만원, 내년 결혼 예정)를 입력해서
9장/24장에 설명된 것과 유사한 변화(달성시점 단축, 신혼부부 지원 단계 추가,
우선순위 변경)가 나오는지 확인해줘.
```

---

## Phase 12. 통합 테스트 & 데모 데이터 고정

**목표**: 설계 문서 24장 데모 시나리오가 처음부터 끝까지 재현되는지 검증.

### Phase 12 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 24장(데모 시나리오), 25장(평가 지표)을
참고해서 end-to-end 통합 테스트를 작성하고 실행해줘.

요구사항:
1. 24.1 입력값으로 프로필/목표 생성 → 24.2/24.3처럼 진단 결과와 7단계 로드맵이
   나오는지 확인하는 e2e 테스트 (backend, pytest 또는 playwright)
2. 24.4 질문에 대한 챗봇 응답 확인
3. 24.5 시뮬레이션 입력 후 변화 확인
4. 25장 평가지표 중 다음을 자동 체크하는 검증 스크립트 작성:
   - 모든 추천 항목에 출처(sources)가 포함되어 있는가 (RAG 품질)
   - 필수 확인사항(확인 필요 조건)이 누락 없이 표시되는가
   - 로드맵 단계 순서가 12.2 선행관계를 위반하지 않는가
5. 발견된 예외 케이스(빈 데이터, 조건 미충족 등)에 대한 에러 핸들링 보강
6. data/demo_seed.json으로 24장 데모 시나리오를 고정 데이터셋으로 저장해서
   발표 시연 시 항상 동일한 결과가 나오도록 함

테스트 결과와 커버리지를 요약해서 보여줘.
```

---

## Phase 13. 배포 준비 & 발표 자료

**목표**: 설계 문서 21장 배포 스택으로 데모 환경 구축, 29장 핵심 메시지로 발표자료 초안 작성.

### Phase 13 프롬프트

```text
FinPath_AI_금융로드맵_MVP_최종설계문서.md 21장(배포), 29장(발표 핵심 메시지),
30장(최종 MVP 정의)을 참고해서 배포 설정과 발표자료 초안을 만들어줘.

요구사항:
1. GitHub Actions CI 워크플로 작성: backend pytest, frontend build/lint를 PR마다 실행
2. frontend는 Vercel 배포 설정, backend는 Render 또는 Railway 배포 설정
   (Dockerfile은 Phase 0의 docker-compose.yml 기반으로 프로덕션용으로 분리)
3. docs/presentation_outline.md 작성: 29장의 핵심 메시지("정책 추천은 기능이고,
   개인 맞춤 금융 로드맵이 제품이다")를 오프닝으로, 30장 최종 MVP 정의를 요약,
   24장 데모 시나리오를 라이브 데모 스크립트로 구성
4. 26장(안전 및 신뢰 설계)의 고지사항 문구를 프론트엔드 footer/모달에 실제로 삽입
   (금융 자문 아님, 실제 가입/대출승인 보장 안 함, 최종 확인일 표시 등)

완료 후 배포된 URL(또는 로컬 프로덕션 빌드)에서 24장 데모 시나리오가
정상 동작하는지 최종 확인해줘.
```

---

## 부록 A. Phase 요약 표

| Phase | 내용 | 참고 장(설계 문서) |
|---|---|---|
| 0 | 프로젝트 스캐폴딩 | 19, 21 |
| 1 | DB 스키마 | 14 |
| 2 | 정책/상품 시드 데이터 | 7.3, 13 |
| 3 | 프로필·목표 온보딩 API | 7.1, 15.1~15.2 |
| 4 | Rule Engine (자격판별) | 7.4, 11.2 |
| 5 | Scoring Engine (우선순위) | 7.5, 11.3, 15.3 |
| 6 | Roadmap Planning Engine | 8, 12, 15.4~15.5 |
| 7 | 온보딩·진단 화면 | 17.1~17.2, 18 |
| 8 | 로드맵 타임라인 시각화 | 9, 17.3~17.4 |
| 9 | RAG + LLM 설명 | 11.4~11.5, 16.1 |
| 10 | AI 상담 챗봇 | 15.7, 16.2, 17.6 |
| 11 | 시뮬레이션 | 10, 15.6, 17.5 |
| 12 | 통합 테스트 & 데모 고정 | 24, 25 |
| 13 | 배포 & 발표자료 | 21, 29, 30 |

## 부록 B. 팀 역할별 담당 Phase (23장 기준)

- **AI·Backend**: Phase 1, 2, 4, 5, 6, 9
- **Frontend**: Phase 7, 8, 10(UI), 11(UI)
- **Data·Planning**: Phase 2(데이터 검증), 12(테스트 케이스), 13(발표자료)

## 부록 C. 프롬프트 사용 시 공통 주의사항

1. 매 프롬프트 실행 전, 이전 Phase의 코드가 실제로 동작하는 상태인지 확인한다.
2. AI 코딩 도구가 26장(안전 및 신뢰 설계) 원칙을 우회하는 구현(예: LLM이 직접 자격 판정)을
   제안하면 반드시 거부하고 Rule Engine으로 되돌린다.
3. 실제 정책/금리 수치는 해커톤 데모용 예시이며, 실서비스 전환 시 13.3의 공식 데이터 소스로
   교체해야 함을 코드 주석 또는 문서에 남긴다.
