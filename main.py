# -*- coding: utf-8 -*-

# import uvicorn
import os

os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "modelscope")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
import yaml

from models.RestfulModel import *
from routers import ocr, pdf_ocr, table
from utils.ImageHelper import *

app = FastAPI(title="Paddle OCR API",
              description="基于 Paddle OCR 和 FastAPI 的自用接口")


# 跨域设置
origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(ocr.router)
app.include_router(pdf_ocr.router)
app.include_router(table.router)

# uvicorn.run(app=app, host="0.0.0.0", port=8000)
