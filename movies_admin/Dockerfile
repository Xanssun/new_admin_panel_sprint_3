FROM python:3.11.5

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r ./requirements.txt --no-cache-dir

COPY . .

EXPOSE 8000

RUN echo "#!/bin/bash" >> run.sh
RUN echo "python manage.py collectstatic --noinput" >> run.sh
RUN echo "python manage.py migrate" >> run.sh
RUN echo "gunicorn config.wsgi:application --bind :8000" >> run.sh
RUN chmod +x run.sh

EXPOSE 8000

ENTRYPOINT ["/app/run.sh"]
