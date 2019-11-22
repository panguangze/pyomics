FROM ubuntu:16.04
RUN apt-get update \
  && apt-get install -y apt-utils tzdata locales python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && python3 -m pip install --upgrade pip \
  && python3 -m pip install pymysql \
  && python3 -m pip install records[pandas] \
  && python3 -m pip install peewee \
  && python3 -m pip install shortuuid \
  && python3 -m pip install pandas \
  && python3 -m pip install psycopg2-binary

# Set the timezone.
ENV HK=Hongkong
RUN ln -snf /usr/share/zoneinfo/$HK /etc/localtime && echo $HK > /etc/timezone
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN useradd -u 1005 -ms /bin/bash platform
USER platform
WORKDIR /home/platform
# COPY pyomics /home/platform/pyomics
