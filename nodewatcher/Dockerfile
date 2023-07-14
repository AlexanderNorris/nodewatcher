FROM python:3.4

ADD . /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["echo", "hello"]