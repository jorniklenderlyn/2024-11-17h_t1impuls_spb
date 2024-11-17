FROM python:3.11.4

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app 

# Install required system dependencies
RUN apt-get update \
    && apt-get install -y binutils libproj-dev libev-dev

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD [ "python", "manage.py", "runserver"]

# sudo docker run --name backend --expose 8080 --network=gis-app-net gis_app