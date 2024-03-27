import logging
import time

import colorlog
from decouple import config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routers import router
from app.utils.prisma import prisma

# Create a color formatter including file name and line number
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:\n%(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
    secondary_log_colors={},
    style="%",
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Update basicConfig format to include file name and line number
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:\n%(message)s",
    handlers=[console_handler],
    force=True,
)

logger = logging.getLogger("main")

app = FastAPI(
    title="Superagent",
    docs_url="/",
    description="🥷 Run AI-agents with an API",
    version="0.2.23",
    servers=[{"url": config("SUPERAGENT_API_URL")}],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.debug(f"Total request time: {process_time} secs")
    return response


@app.on_event("startup")
async def startup():
    await prisma.connect()


@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()


app.include_router(router)
