FROM python:3.13-slim 
WORKDIR /app 
COPY . . 
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 10000
# CMD ["python", "app.py"]
CMD gunicorn --bind 0.0.0.0:${PORT} wsgi:app