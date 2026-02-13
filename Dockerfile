FROM python:3.12

WORKDIR /app

COPY . .

RUN pip3 install uvicorn[standard] fastapi pyjwt kafka-python pymongo

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--reload"]

