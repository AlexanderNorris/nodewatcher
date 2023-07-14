FROM python:3.10

ADD . /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["echo", "hello"]