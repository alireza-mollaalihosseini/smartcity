# Smart Kitchen Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port (for dashboard)
EXPOSE 8501

CMD ["python", "main.py"]