# FinPath AI — UI/UX 가이드

> 원칙 출처: [Figma Resource Library — UI Design Principles](https://www.figma.com/ko-kr/resource-library/ui-design-principles/)
> 시각 자료(색상 스와치, 컴포넌트 실사례 렌더링 포함)는 별도 아티팩트로 게시했다:
> https://claude.ai/code/artifact/8667b181-63dd-4de0-a19f-4202c353f572
>
> 이 문서는 새 값을 발명하지 않고, `frontend/components/` 전체를 grep해 실제로 쓰인
> Tailwind 클래스 빈도를 집계한 뒤 이름을 붙인 것이다. 스택: Next.js 14 · Tailwind CSS 3 ·
> Geist Sans / Geist Mono.

---

## 1. 파운데이션 토큰

### 1.1 색상

| 토큰 | Tailwind | Hex | 용도 |
|---|---|---|---|
| Accent | `blue-600` | `#2563eb` | 주요 버튼, 활성 탭, 진행률 바 |
| Accent / Hover | `blue-700` | `#1d4ed8` | 버튼 hover |
| Text / Primary | `gray-900` | `#111827` | 제목, 핵심 수치 |
| Text / Secondary | `gray-600` | `#4b5563` | 본문 (프로젝트 전체에서 가장 많이 쓰인 색, 37회) |
| Text / Muted | `gray-500` | `#6b7280` | 라벨, 메타 정보 |
| Text / Faint | `gray-400` | `#9ca3af` | STEP 번호 등 눈에 덜 띄어야 하는 텍스트 |
| Surface / Page | `gray-50` | `#f9fafb` | 페이지 배경 (카드와 시각적으로 구분) |
| Surface / Card | `white` | `#ffffff` | 모든 카드 배경 — **테마와 무관하게 항상 고정** (4.2 참고) |
| Surface / Subtle | `gray-100` | `#f3f4f6` | 진행률 바 트랙, 코드 배경 |
| Status / Success | `green-700` on `green-100` | `#15803d` / `#dcfce7` | 신청 가능, 완료 |
| Status / Warning | `yellow-700` on `yellow-100` | `#a16207` / `#fef9c3` | 조건부 가능, 확인 필요 |
| Status / Danger | `red-700` on `red-100` | `#b91c1c` / `#fee2e2` | 신청 어려움, 에러 |

### 1.2 타이포그래피

- **UI/본문**: Geist Sans (가변 폰트 100–900, `app/layout.tsx`에서 로컬 로드)
- **숫자/데이터**: Geist Mono — 날짜·퍼센트·ID처럼 자릿수가 맞아야 하는 값에 권장(현재 앱 본체에는 아직 부분 적용, §4.1 참고)

| 클래스 | 크기/굵기 | 용도 |
|---|---|---|
| `text-2xl font-bold` | 24px / 700 | 페이지 타이틀 (예: "FinPath AI · 진단 결과") |
| `text-lg font-bold` | 18px / 700 | 카드 제목 (예: "비상자금 확보") |
| `text-base font-semibold` | 16px / 600 | 섹션 헤딩 |
| `text-sm` | 14px / 400 | 본문 |
| `text-xs` | 12px / 400, faint 색 | 메타 라벨 (STEP 번호 등) |

카드 안에서 `text-lg font-bold`는 **제목 하나만** 쓴다. 여러 개면 계층이 무너진 것.

### 1.3 간격 · 형태

| 값 | 용도 |
|---|---|
| `gap-2` (8px) | 뱃지 내부 아이콘-텍스트 간격 |
| `gap-4` (16px) | 카드 그리드 사이 간격 |
| `p-5` (20px) | 카드 내부 패딩 (표준값) |
| `p-6` (24px) | 페이지 컨테이너 패딩 |
| `space-y-6` (24px) | 페이지 내 섹션 간 세로 간격 |
| `rounded-lg` (8px) | 카드, 버튼 |
| `rounded-full` | 뱃지, 칩, 진행 표시점 |

여백은 개별 요소의 margin이 아니라 부모의 `gap`/`space-y`로 준다 (마진 중첩 방지).

---

## 2. 7원칙 × FinPath 적용

### 2.1 계층 구조 (Hierarchy)
글꼴 크기·두께, 색상, 간격으로 무엇을 먼저 볼지 정한다.

**적용 사례**: `RoadmapStepCard` — STEP 번호(`text-xs`, faint) → 제목(`text-lg font-bold`) → 날짜(`text-xs`, muted) → 설명(`text-sm`, secondary) 순으로 명확한 굵기 단계.

**규칙**
- 카드 안 굵은 텍스트는 제목 하나만.
- 메타 정보(STEP 번호, 날짜)는 `text-xs` + faint 색.
- 같은 화면에 굵은 텍스트가 3개 이상이면 계층을 다시 점검.

### 2.2 점진적 공개 (Progressive Disclosure)
여러 단계로 안내하고, 지금 어디 있는지·얼마나 남았는지 항상 보여준다.

**적용 사례**: 온보딩 4단계(프로필 → 목표 → 관심사 키워드 → 미래이벤트) — 상단 스테퍼가 현재 단계를 강조. 선택 단계는 제목에 "(선택)" 명시하고 건너뛰기 경로 유지. `EvidencePanel`처럼 무거운 정보는 "자세히 보기" 클릭 후에만 노출.

**규칙**
- 4단계 이상이면 반드시 `1. 라벨 · 2. 라벨` 형태 스테퍼.
- 선택 단계는 스킵 가능하게, 제목에 "(선택)" 명시.
- 상세 정보는 기본 숨김 + 명시적 액션으로 펼침.

### 2.3 일관성 (Consistency)
같은 의미는 어디서나 같은 모양으로.

**적용 사례**: `StatusBadge`/`EligibilityBadge`가 로드맵 화면과 추천 상세 화면 양쪽에서 재사용됨. 모든 카드는 `rounded-lg border border-gray-200 bg-white p-5`로 통일.

**규칙**
- 상태 표현은 `StatusBadge`/`EligibilityBadge`만 사용, 새 컴포넌트에서 직접 색을 칠하지 않는다.
- 같은 의미(경고)에는 같은 색만 — yellow와 amber를 섞지 않는다 (3.1의 실제 수정 사례 참고).

### 2.4 대비 (Contrast)
중요한 것으로 시선을 끈다. 여기엔 "배경 위 텍스트가 실제로 읽히는가"도 포함된다.

**적용 사례 겸 실제 버그**: 진단 화면 `<main>`에 배경색을 지정하지 않아서, 시스템 다크모드에서 카드 안 회색 텍스트가 검정 배경 위에서 거의 안 보였다. 카드를 테마와 무관하게 항상 `bg-white`로 고정해 해결 (Phase 7).

**규칙**
- 주 동작은 화면당 1개만 `bg-blue-600`.
- 새 카드/텍스트 조합은 시스템 다크모드에서도 반드시 확인한다.
- `text-gray-500` 이하 회색 텍스트는 흰 배경 위에서만 사용한다.

### 2.5 접근성 (Accessibility)
대체 텍스트, 키보드 탐색, 충분한 대비, 보조기술 호환.

**적용 사례 (잘한 점)**: 상태는 항상 아이콘 + 색 + 텍스트 라벨 3중으로 인코딩되어 색에만 의존하지 않는다.

**적용 사례 (수정 완료)**: 모든 버튼/링크에 `focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600`를 적용해 키보드 포커스가 항상 명확히 보이도록 함. 탭 버튼에는 `aria-current`, 키워드 칩에는 `aria-pressed`도 추가. 실제 텍스트 없는 아이콘 전용 버튼은 코드 전체에 없음 — 모든 버튼이 이미 텍스트 라벨을 갖고 있어 `aria-label` 문제는 재확인 결과 해당 없음.

### 2.6 근접성 (Proximity)
관련 있는 요소는 붙이고, 없는 요소는 떼어놓는다.

**적용 사례**: 로드맵 각 단계 카드 안에 연결된 추천 상품이 별도 리스트가 아니라 직접 붙어 있다. `ProfileForm`은 "기본정보 / 소득·자산 / 주거·부채" 의미 단위로 `<section>`을 나눈다.

**규칙**
- 뱃지와 그 대상(점수, 제목)은 같은 줄 또는 바로 아래에 배치.
- 필드가 많은 폼은 의미 단위로 섹션을 나눈다.

### 2.7 정렬 (Alignment)
강력한 그리드로 질서와 균형을 만든다.

**적용 사례**: 진단 카드는 `grid gap-4 sm:grid-cols-2`, 컨테이너는 `max-w-3xl`로 고정.

**규칙**
- 입력 위주 화면(온보딩)은 `max-w-xl`, 결과 위주 화면(대시보드)은 `max-w-3xl`로 통일.
- 숫자·날짜가 세로로 늘어서는 리스트는 `tabular-nums` 고려.

---

## 3. 컴포넌트 패턴

| 패턴 | 클래스 레시피 |
|---|---|
| 주 버튼 | `bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2 text-sm font-semibold` |
| 보조 버튼 | `border border-gray-300 bg-white text-gray-600 rounded px-4 py-2 text-sm font-semibold` |
| 상태 뱃지 | `rounded-full px-2.5 py-0.5 text-xs font-medium bg-{color}-100 text-{color}-700` |
| 선택형 칩 | 기본 `rounded-full border border-gray-300 px-3 py-1.5 text-sm`, 선택됨 `bg-blue-600 border-blue-600 text-white` |
| 진행률 바 | 트랙 `h-2 bg-gray-100 rounded`, 채움 `h-2 bg-blue-500 rounded` |
| 에러 배너 | `rounded bg-red-50 p-3 text-sm text-red-600` |

---

## 4. 발견한 이슈

가이드를 만들며 코드를 훑다가 실제로 발견해 그 자리에서 수정한 것 3건, 아직 열려있는 것 1건.

| 상태 | 내용 | 파일 |
|---|---|---|
| ✅ 수정됨 | `StatusBadge.tsx` 안에서 `IN_PROGRESS`는 `amber-*`, `NEEDS_CONFIRMATION`은 `yellow-*`를 써서 같은 의미(경고)가 다른 색으로 보이던 문제. `yellow-*`로 통일. | `components/roadmap/StatusBadge.tsx` |
| ✅ 수정됨 | Geist 폰트가 `layout.tsx`에서 로드만 되고, `globals.css`의 `body { font-family: Arial }`가 그 변수를 참조하지 않아 실제로는 Arial로 렌더링되던 문제. `var(--font-geist-sans)` 참조로 수정. | `app/globals.css` |
| ✅ 수정됨 | 버튼·링크·탭에 커스텀 `focus-visible` 스타일이 없어 브라우저 기본값에 의존하던 문제. 전 컴포넌트에 포커스 링 클래스를 추가하고 실제 키보드 탐색(Tab)으로 렌더링 확인. | `components/**/*.tsx`, `app/page.tsx` |
| ⬜ 미해결 | 다크모드는 "지원"이 아니라 "회피"에 가깝다. 카드를 전부 `bg-white`로 고정해 다크모드 버그를 막은 것뿐, 실제 다크 테마 디자인은 없음. 아티팩트의 다크 토큰이 출발점이 될 수 있음. | — |

---

## 5. 새 화면 만들 때 체크리스트

1. **제목은 하나만 굵게.** 카드 안에 `text-lg font-bold`가 여러 개면 계층이 깨진 것.
2. **상태는 `StatusBadge`/`EligibilityBadge` 재사용.** 새 색을 직접 칠하지 않는다.
3. **카드 배경은 항상 `bg-white` 명시.** 시스템 다크모드에서 실제로 열어보고 확인한다.
4. **4단계 이상 흐름엔 스테퍼.** 지금 몇 번째인지 항상 보이게.
5. **주 동작은 화면당 1개.** `bg-blue-600`은 그 하나에만.
6. **컨테이너 폭 통일.** 입력 화면 `max-w-xl` / 결과 화면 `max-w-3xl`.
7. **관련 요소는 붙이고, 무관한 요소는 `gap`으로 뗀다.** 개별 margin 대신 부모의 `gap`/`space-y`.
