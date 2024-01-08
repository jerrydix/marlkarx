FROM python:3.11-slim-buster
COPY . /app
WORKDIR /app
RUN apt update && apt install libffi-dev libnacl-dev ffmpeg -y
RUN pip install -r requirements.txt
RUN yt-dlp -U
ENV MUSIC_MAX_DURATION_MINS=20
ENV MUSIC_QUEUE_PER_PAGE=10
CMD ["python3", "main.py"]
