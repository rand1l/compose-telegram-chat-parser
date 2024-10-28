FROM python:3.13.0-slim

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple telethon sqlalchemy asyncpg minio greenlet
WORKDIR /app

COPY . /app


CMD ["python", "app/__main__.py"]
