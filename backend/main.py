from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import goals, life_events, profiles, recommendations, roadmaps, simulations

app = FastAPI(title="FinPath AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(goals.router)
app.include_router(life_events.router)
app.include_router(recommendations.router)
app.include_router(roadmaps.router)
app.include_router(simulations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
