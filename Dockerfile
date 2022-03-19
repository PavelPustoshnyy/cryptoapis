FROM python:3.6.8

RUN pip install python-binance

RUN python3 __main__.py