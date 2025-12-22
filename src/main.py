from core.config import config

app = FastAPI(
    lifespan=lifespan,
    title="Publishing Service",
    version=config.version,
    root_path=config.server_path,
    servers=[{"url": config.server_path, "description": "Publishing Service API"}],
)

app.include_router(routers)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
