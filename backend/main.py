from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import goals, interest_keywords, life_events, profiles, recommendations, roadmaps, simulations

app = FastAPI(title="FinPath AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    # Vercel은 배포마다 프리뷰 URL이 바뀌고(finpath-<hash>-kyo7.vercel.app), 프로덕션 별칭도
    # 여러 개(finpath-ai-kyo7.vercel.app 등) 붙는다. 이 프로젝트의 모든 vercel.app 서브도메인을
    # 정규식으로 허용한다. 인증/쿠키가 없는 공개 MVP API라 넓게 허용해도 위험이 낮다.
    allow_origin_regex=r"https://finpath-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(goals.router)
app.include_router(life_events.router)
app.include_router(interest_keywords.router)
app.include_router(recommendations.router)
app.include_router(roadmaps.router)
app.include_router(simulations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
