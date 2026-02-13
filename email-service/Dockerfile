FROM python:3.12

WORKDIR /app

COPY . .

RUN pip3 install kafka-python

EXPOSE 9092

CMD ["python3", "main.py"]

