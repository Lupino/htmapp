FROM lupino/htm.core:python-3.8.5

ADD requirements.txt /app/requirements.txt

RUN apt install -y git && pip3 install -r /app/requirements.txt

ADD . /app
WORKDIR /app

ENV SYSTEM_PYTHON TRUE

ENTRYPOINT ["/app/run.sh"]

CMD ["htmapp/main.py"]
