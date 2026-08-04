# FinPath AI — 사용자 유형별 테스트케이스

> 목적: 온보딩 4단계(프로필/목표/관심사 키워드/미래이벤트) 입력값을 유형별로 미리 준비해두고,
> UI로 직접 입력하거나 API로 바로 호출해서 추천·로드맵 결과가 기대대로 나오는지 확인한다.
> 특히 최근 추가된 소외계층(`special_status`) 팩터가 유형별로 정확히 갈리는지가 핵심 검증 대상.

## 사용법

**UI로 테스트**: 각 케이스의 "온보딩 입력값" 표를 보고 `http://localhost:3000` (로컬) 또는
`https://finpath-ai-kyo7.vercel.app` (배포)에서 그대로 입력.

**API로 빠르게 테스트**: 각 케이스의 curl 스크립트에서 `BASE` 값만 바꿔서 실행.
```bash
# 로컬
BASE="http://localhost:8000/api/v1"
# 배포
BASE="https://finpath-ai-zgh8.onrender.com/api/v1"
```
스크립트는 프로필→목표→(선택)관심사키워드→(선택)미래이벤트→추천/로드맵 생성까지 한 번에 실행하고,
정책 제목과 `eligibility_status`만 뽑아서 보여준다.

## 참고: 입력 가능한 값

- `job_status`: EMPLOYED / SELF_EMPLOYED / UNEMPLOYED / STUDENT
- `marital_status`: SINGLE / MARRIED / ENGAGED
- `housing_type`: MONTHLY_RENT / JEONSE / OWN
- `goal_type`: JEONSE / HOME_PURCHASE / SEED_MONEY / DEBT_REPAYMENT
- `life_event_type`: MARRIAGE / CHILDBIRTH / RELOCATION / JOB_CHANGE
- `special_status`: 국가유공자 / 기초생활수급자 / 차상위계층 / 장애인 / 한부모가족 / 다문화가족 / 자립준비청년 / 북한이탈주민 (다중 선택 가능, 미선택 가능)

---

## 케이스 1. 일반 청년 (기준/대조군 — 소외계층 미선택)

**시나리오**: 소외계층 필드를 아예 선택하지 않는 가장 흔한 사용자. 소외계층 대상 정책이 노출되지 않는지 확인하는 대조군.

| 필드 | 값 |
|---|---|
| 나이 | 27 |
| 거주지역 | 서울 |
| 직업 상태 | EMPLOYED |
| 연 소득 | 38,000,000 |
| 혼인 여부 | SINGLE |
| 주거형태 | MONTHLY_RENT |
| 현금성 자산 | 5,000,000 |
| 총부채 | 0 |
| 월 저축 가능액 | 800,000 |
| 소외계층 | (선택 안 함) |
| 목표 | SEED_MONEY |
| 관심사 키워드 | 사회초년생(첫 직장) |
| 미래 이벤트 | 없음 |

**기대 결과**
- 국가유공자/장애인/한부모가족 등 소외계층 정책 14건 전부 `NOT_ELIGIBLE` (또는 추천 목록에서 순위 밖으로 밀림)
- 일반 청년 정책(청년내일저축계좌, 청년도약계좌 등)만 정상 노출

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":27,"annual_income":38000000,"region":"서울","job_status":"EMPLOYED",
  "marital_status":"SINGLE","housing_type":"MONTHLY_RENT","liquid_assets":5000000,
  "total_debt":0,"monthly_saving":800000
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/goals -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'","goal_type":"SEED_MONEY","priority":1}' > /dev/null
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if any(k in i['category'] for k in ['보훈','장애인','한부모','다문화','자립준비','북한이탈','취약계층'])]"
```

---

## 케이스 2. 신혼부부 예정자

**시나리오**: 결혼을 앞둔 커플. 로드맵에 "신혼부부 지원 검토" 단계가 생기고, 전세자금 단계에서 신혼부부 전용 대출이 우선 노출되는지 확인.

| 필드 | 값 |
|---|---|
| 나이 | 30 |
| 혼인 여부 | ENGAGED (약혼/결혼 예정 — **SINGLE 아님, 주의**) |
| 주거형태 | JEONSE |
| 목표 | JEONSE, 목표금액 200,000,000 |
| 미래 이벤트 | MARRIAGE |

**기대 결과**
- 로드맵에 "신혼부부 지원 검토" 단계 포함, related_items에 "신혼부부 결혼자금 대출이자 지원" 등 3건
- "전세자금 마련 준비" 단계 1순위가 "신혼부부전용 전세자금대출"

**🔧 수정 이력**: 최초 작성 시 혼인 여부를 `SINGLE`로 두고 테스트했더니 신혼부부 정책이 전부 `marital_status: NOT_MET`으로 걸려 후보에서 빠지는 문제를 발견했음. 원인은 두 가지였음 — ① 신혼부부 정책 5건의 `eligibility_rules.marital_status`가 `["MARRIED"]`만 허용하고 `ENGAGED`(약혼)를 안 받았음(기존 "신혼희망타운 특별공급"만 `["MARRIED","ENGAGED"]`로 이미 되어있었음), ② 이 5건을 `["MARRIED","ENGAGED"]`로 맞춤. 프론트엔드에는 "약혼" 선택지가 이미 있었으므로(`ProfileForm.tsx`) UI 변경은 불필요했음. 수정 후 위 표처럼 혼인 여부를 `ENGAGED`로 입력하면 정상적으로 신혼부부 정책이 노출됨을 재검증 완료.

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":30,"annual_income":45000000,"region":"서울","job_status":"EMPLOYED",
  "marital_status":"ENGAGED","housing_type":"JEONSE","liquid_assets":30000000,
  "total_debt":0,"monthly_saving":1200000
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/goals -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'","goal_type":"JEONSE","target_amount":200000000,"priority":1}' > /dev/null
curl -s -X POST $BASE/life-events -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'","event_type":"MARRIAGE"}' > /dev/null
curl -s -X POST $BASE/roadmaps/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(s['title'],'->',[i['title'] for i in (s.get('related_items') or [])]) for s in d['steps']]"
```

---

## 케이스 3. 국가유공자

| 필드 | 값 |
|---|---|
| 나이 | 55 |
| 소외계층 | 국가유공자 |

**기대 결과**: "국가유공자 등 대부지원", "보훈(가족)장학금" → `ELIGIBLE`

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":55,"annual_income":30000000,"region":"서울","job_status":"EMPLOYED",
  "marital_status":"MARRIED","housing_type":"OWN","liquid_assets":15000000,
  "total_debt":0,"monthly_saving":400000,"special_status":["국가유공자"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if '보훈' in i['category']]"
```

---

## 케이스 4. 기초생활수급자

| 필드 | 값 |
|---|---|
| 연 소득 | 12,000,000 (저소득 시나리오) |
| 소외계층 | 기초생활수급자 |

**기대 결과**: "희망저축계좌(자산형성지원사업)", "에너지바우처" → `ELIGIBLE` / "주거급여" → `CONDITIONAL`(무주택 조건은 항상 확인 필요로 처리)

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":35,"annual_income":12000000,"region":"서울","job_status":"UNEMPLOYED",
  "marital_status":"SINGLE","housing_type":"MONTHLY_RENT","liquid_assets":1000000,
  "total_debt":0,"monthly_saving":100000,"special_status":["기초생활수급자"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if i['title'] in ('희망저축계좌(자산형성지원사업)','주거급여','에너지바우처')]"
```

---

## 케이스 5. 차상위계층

| 필드 | 값 |
|---|---|
| 소외계층 | 차상위계층 |

**기대 결과**: "에너지바우처" → `ELIGIBLE` / "주거급여" → `CONDITIONAL`(무주택 조건은 항상 확인 필요로 처리되는 기존 규칙 때문에 ELIGIBLE이 아니라 CONDITIONAL이 정상) / "희망저축계좌"(기초생활수급자 전용) → `NOT_ELIGIBLE` (교차 오염 안 되는지 확인)

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":40,"annual_income":18000000,"region":"서울","job_status":"SELF_EMPLOYED",
  "marital_status":"MARRIED","housing_type":"MONTHLY_RENT","liquid_assets":2000000,
  "total_debt":0,"monthly_saving":200000,"special_status":["차상위계층"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if i['title'] in ('희망저축계좌(자산형성지원사업)','주거급여','에너지바우처')]"
```

---

## 케이스 6. 장애인

| 필드 | 값 |
|---|---|
| 나이 | 40 (19세 이상 조건 확인용) |
| 소외계층 | 장애인 |

**기대 결과**: "장애인 자립자금 대여", "장애인연금" → `ELIGIBLE`

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":40,"annual_income":20000000,"region":"서울","job_status":"UNEMPLOYED",
  "marital_status":"SINGLE","housing_type":"MONTHLY_RENT","liquid_assets":3000000,
  "total_debt":0,"monthly_saving":150000,"special_status":["장애인"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if '장애인' in i['title']]"
```

---

## 케이스 7. 한부모가족 (일반)

| 필드 | 값 |
|---|---|
| 나이 | 33 |
| 소외계층 | 한부모가족 |

**기대 결과**: "한부모가족 아동양육비 지원" → `ELIGIBLE` / "청소년 한부모 자립지원"(만 24세 이하 전용) → `NOT_ELIGIBLE`

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":33,"annual_income":22000000,"region":"서울","job_status":"EMPLOYED",
  "marital_status":"SINGLE","housing_type":"MONTHLY_RENT","liquid_assets":4000000,
  "total_debt":0,"monthly_saving":300000,"special_status":["한부모가족"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if '한부모' in i['title']]"
```

## 케이스 7-1. 청소년 한부모 (연령 경계값 확인)

동일 조건에서 **나이만 22세**로 바꿔서 실행 → 이번엔 "청소년 한부모 자립지원"도 함께 `ELIGIBLE`이어야 함 (age_max=24 경계 검증).

---

## 케이스 8. 다문화가족

| 필드 | 값 |
|---|---|
| 소외계층 | 다문화가족 |

**기대 결과**: "다문화가족 방문교육 및 통번역 지원서비스" → `ELIGIBLE`

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":32,"annual_income":28000000,"region":"경기","job_status":"EMPLOYED",
  "marital_status":"MARRIED","housing_type":"MONTHLY_RENT","liquid_assets":6000000,
  "total_debt":0,"monthly_saving":400000,"special_status":["다문화가족"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if '다문화' in i['title']]"
```

---

## 케이스 9. 자립준비청년

| 필드 | 값 |
|---|---|
| 나이 | 20 |
| 소외계층 | 자립준비청년 |

**기대 결과**: "디딤씨앗통장(아동발달지원계좌)", "자립준비청년 자립수당", "자립준비청년 자립정착금" 3건 모두 `ELIGIBLE`

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":20,"annual_income":15000000,"region":"서울","job_status":"EMPLOYED",
  "marital_status":"SINGLE","housing_type":"MONTHLY_RENT","liquid_assets":1000000,
  "total_debt":0,"monthly_saving":200000,"special_status":["자립준비청년"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if '자립' in i['title'] or '디딤씨앗' in i['title']]"
```

---

## 케이스 10. 북한이탈주민

| 필드 | 값 |
|---|---|
| 소외계층 | 북한이탈주민 |

**기대 결과**: "북한이탈주민 정착지원금" → `ELIGIBLE`

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":29,"annual_income":25000000,"region":"서울","job_status":"EMPLOYED",
  "marital_status":"SINGLE","housing_type":"MONTHLY_RENT","liquid_assets":3000000,
  "total_debt":0,"monthly_saving":300000,"special_status":["북한이탈주민"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if '북한이탈' in i['title']]"
```

---

## 케이스 11. 복수 소외계층 중복 선택 (장애인 + 차상위계층)

**시나리오**: 두 계층에 동시에 해당하는 사용자. 두 카테고리 정책이 서로 간섭 없이 동시에 노출되는지 확인.

| 필드 | 값 |
|---|---|
| 소외계층 | 장애인, 차상위계층 (다중 선택) |

**기대 결과**: "장애인 자립자금 대여", "장애인연금", "에너지바우처" → `ELIGIBLE` / "주거급여" → `CONDITIONAL`(무주택 조건은 항상 확인 필요로 처리)

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":42,"annual_income":16000000,"region":"서울","job_status":"UNEMPLOYED",
  "marital_status":"MARRIED","housing_type":"MONTHLY_RENT","liquid_assets":2000000,
  "total_debt":0,"monthly_saving":100000,"special_status":["장애인","차상위계층"]
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/recommendations/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(i['title'],'|',i['eligibility_status']) for i in d['items'] if i['title'] in ('장애인 자립자금 대여','장애인연금','주거급여','에너지바우처')]"
```

---

## 케이스 12. 고금리 부채 보유자 (기존 로드맵 분기 회귀 확인)

**시나리오**: 소외계층과 무관하게, 기존 로드맵 분기 로직(부채 있을 때만 "고금리 부채 상환" 단계 포함)이 이번 변경으로 깨지지 않았는지 확인하는 회귀 테스트.

| 필드 | 값 |
|---|---|
| 총부채 | 5,000,000 |
| 목표 | DEBT_REPAYMENT |

**기대 결과**: 로드맵에 "고금리 부채 상환" 단계 포함, 소외계층 정책은 전부 `NOT_ELIGIBLE`

```bash
BASE="http://localhost:8000/api/v1"
RESP=$(curl -s -X POST $BASE/profiles -H "Content-Type: application/json" -d '{
  "age":29,"annual_income":32000000,"region":"서울","job_status":"EMPLOYED",
  "marital_status":"SINGLE","housing_type":"MONTHLY_RENT","liquid_assets":2000000,
  "total_debt":5000000,"monthly_saving":500000
}')
USER_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['user_id'])")
curl -s -X POST $BASE/goals -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'","goal_type":"DEBT_REPAYMENT","priority":1}' > /dev/null
curl -s -X POST $BASE/roadmaps/generate -H "Content-Type: application/json" -d '{"user_id":"'"$USER_ID"'"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print([s['title'] for s in d['steps']])"
```

---

## 체크리스트 요약

| # | 유형 | 확인 포인트 |
|---|---|---|
| 1 | 일반 청년 (대조군) | 소외계층 정책 전부 NOT_ELIGIBLE |
| 2 | 신혼부부 예정자 | 혼인여부는 ENGAGED로 입력(SINGLE 아님), 신혼부부 단계 포함·전세대출 우선순위 정상 |
| 3 | 국가유공자 | 대부지원·장학금 ELIGIBLE |
| 4 | 기초생활수급자 | 희망저축계좌·에너지바우처 ELIGIBLE, 주거급여는 CONDITIONAL |
| 5 | 차상위계층 | 에너지바우처 ELIGIBLE, 주거급여 CONDITIONAL(무주택 확인 필요), 희망저축계좌 제외 |
| 6 | 장애인 | 자립자금대여·연금 ELIGIBLE |
| 7 | 한부모가족(일반) | 아동양육비만 ELIGIBLE |
| 7-1 | 한부모가족(청소년) | 청소년 한부모 자립지원도 추가 ELIGIBLE |
| 8 | 다문화가족 | 통번역서비스 ELIGIBLE |
| 9 | 자립준비청년 | 3건 모두 ELIGIBLE |
| 10 | 북한이탈주민 | 정착지원금 ELIGIBLE |
| 11 | 복수 선택 | 두 계층 정책 동시 노출(장애인 계열 ELIGIBLE, 주거급여만 CONDITIONAL), 간섭 없음 |
| 12 | 고금리 부채 (회귀) | 기존 로드맵 분기 로직 정상 |
