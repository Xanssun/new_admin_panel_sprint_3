FROM python:3.10-slim-buster

WORKDIR /sqlite_to_es

COPY ./requirements.txt ./
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . ./

EXPOSE 9000

CMD python main.py