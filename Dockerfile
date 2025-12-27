FROM python:3.9-slim-bullseye

# 暴露端口
EXPOSE 8000

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装系统依赖
COPY requirements.txt /app/requirements.txt

# 换源并安装系统依赖
RUN sed -i "s@http://deb.debian.org@http://mirrors.tuna.tsinghua.edu.cn@g" /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libgomp1 \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# apt-get换源并安装依赖（使用阿里云镜像）
RUN sed -i "s@http://deb.debian.org@http://mirrors.aliyun.com@g" /etc/apt/sources.list
RUN cat /etc/apt/sources.list
RUN apt-get update && apt-get install -y libgl1 libgomp1 libglib2.0-0 libsm6 libxrender1 libxext6
# 清理apt-get缓存
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# pip换源并安装python依赖（使用阿里云镜像）
RUN python3 -m pip install -i https://mirrors.aliyun.com/pypi/simple/ --upgrade pip
RUN pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/
RUN pip3 install -r requirements.txt

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--workers", "2", "--log-config", "./log_conf.yaml"]
