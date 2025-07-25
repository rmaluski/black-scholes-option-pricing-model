FROM python:3.11-slim

WORKDIR /app

COPY requirements.in ./
RUN pip install pip-tools && pip-compile requirements.in && pip install -r requirements.txt
COPY . .

EXPOSE 8501 8000

CMD ["streamlit", "run", "app.py"]
# To run FastAPI: docker run ... uvicorn api:app --host 0.0.0.0 --port 8000 