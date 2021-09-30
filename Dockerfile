FROM lupino/htm.core:python-3.8.5

ADD requirements.txt /app/requirements.txt

RUN apt update && apt install -y git && pip3 install -r /app/requirements.txt

ADD . /app
WORKDIR /app

ENV SYSTEM_PYTHON TRUE

ENTRYPOINT ["python3", "/app/script.py"]

CMD ["htmapp/main.py"]
