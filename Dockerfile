FROM python:3.8-slim-buster
COPY . /app
WORKDIR /app
RUN pip install openai && pip install discord && pip install tabulate && pip install bs4
RUN pip install -r requirements.txt
CMD python3 main.py