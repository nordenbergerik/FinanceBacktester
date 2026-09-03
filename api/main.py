from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.backtests import router as backtests_router


app = FastAPI(title="Finance Backtester API", version="0.1.0")
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:4173", "http://127.0.0.1:4173", "http://localhost:5500"],
	allow_credentials=False,
	allow_methods=["GET", "POST"],
	allow_headers=["*"],
)
app.include_router(backtests_router)


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}
