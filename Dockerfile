FROM python:3.9-slim

WORKDIR /app

# Git 설치 (필수)
RUN apt-get update && apt-get install -y git && apt-get clean

# 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]