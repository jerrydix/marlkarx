FROM python:3.8-slim-buster
COPY . /app
WORKDIR /app
RUN pip install openai
RUN pip install discord
RUN pip install tabulate
RUN pip install bs4
CMD python3 main.py