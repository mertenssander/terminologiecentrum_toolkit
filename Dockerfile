FROM python:3.9

RUN pip install pandas tqdm requests xlrd openpyxl

RUN mkdir /scripts
COPY ./ /scripts

WORKDIR /scripts

ENTRYPOINT bash