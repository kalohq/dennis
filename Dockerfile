FROM python:3.5-slim
MAINTAINER Yannis Panousis - yannis@lystable.com

ENV SAWYER_TAG 7dfda7cc971274552c327116b124cf8e659a5228

RUN apt-get update
RUN apt-get install -y gcc git
RUN mkdir -p ~/.ssh && ssh-keyscan github.com > ~/.ssh/known_hosts

# Install Sawyer
RUN apt-get -y install vim
RUN git clone https://github.com/lystable/sawyer.git && cd sawyer && git checkout $SAWYER_TAG && python setup.py develop

WORKDIR /dennis
COPY requirements.txt /dennis/requirements.txt
RUN pip install --user -r /dennis/requirements.txt
RUN pip install --user https://github.com/lystable/PyGithub/archive/ca6d43eb3b6ee14637940988fd4ac7eb3c207c79.zip#egg=PyGithub
RUN apt-get -y remove gcc && apt-get autoremove -y

COPY . /dennis
RUN python setup.py develop

WORKDIR /git

RUN git config --global credential.helper cache && \
    git config --global credential.helper 'cache --timeout=3600'

ENTRYPOINT ["/dennis/entrypoint.sh"]
