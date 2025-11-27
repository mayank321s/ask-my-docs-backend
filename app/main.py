"""
Here you should do all needed actions. Standart configuration of docker container
will run your application with this file.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import logging

logging.basicConfig(level="DEBUG")

from app.config import openapi_config
from app.initializer import init

app = FastAPI(
    title=openapi_config.name,
    version=openapi_config.version,
    description=openapi_config.description,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

logger.info("Starting application initialization...")
init(app)
logger.success("Successfully initialized!")
