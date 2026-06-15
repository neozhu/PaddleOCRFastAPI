FROM python:3.12-slim-bullseye

EXPOSE 8000

WORKDIR /app

ENV PADDLE_PDX_MODEL_SOURCE=BOS \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

COPY requirements.txt /app/requirements.txt

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libgomp1 \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
        ccache && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN python3 -m pip install --upgrade pip && \
    pip3 install -r requirements.txt

COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
