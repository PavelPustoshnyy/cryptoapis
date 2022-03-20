FROM python:3.9.9

COPY requirements.in /tmp/requirements.in

RUN pip install pip-tools==6.4.0
RUN pip-compile /tmp/requirements.in --output-file=/tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN pip install python-binance

COPY src /usr/app/src
RUN mkdir /usr/app/log

COPY __main__.py /usr/app/

CMD [ "python3", "/usr/app/__main__.py"]