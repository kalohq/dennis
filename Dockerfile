FROM python:3.5-slim
MAINTAINER Yannis Panousis - yannis@lystable.com

ENV SAWYER_TAG 7dfda7cc971274552c327116b124cf8e659a5228

RUN apt-get update
RUN apt-get install -y gcc git

# Install Sawyer
RUN apt-get -y install vim
RUN git clone https://github.com/lystable/sawyer.git && cd sawyer && git checkout $SAWYER_TAG && python setup.py develop

WORKDIR /dennis
COPY requirements.txt /dennis/requirements.txt
RUN pip install --user -r /dennis/requirements.txt

COPY . /dennis
RUN python setup.py develop
RUN apt-get -y remove gcc && apt-get autoremove -y

WORKDIR /git

ENTRYPOINT ["/dennis/entrypoint.sh"]
