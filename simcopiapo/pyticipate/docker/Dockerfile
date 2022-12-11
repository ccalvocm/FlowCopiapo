FROM ubuntu:bionic

# Install system programs

RUN apt-get update \
  && apt-get install -y \
  software-properties-common \
  git \
  python3 \
  python3-pip

# Copy ssh private key from host for non-interactive repo access by git

COPY /Auth/id_rsa /root/.ssh/id_rsa

RUN chmod 700 /root/.ssh/id_rsa \
  && echo "Host bitbucket.csiro.au" >> /root/.ssh/config \
  && echo "StrictHostKeyChecking no" >> /root/.ssh/config

# Download source code

RUN mkdir -p /home/source \
  && cd /home/source \
  && git clone -b develop ssh://git@bitbucket.csiro.au:7999/eis/pyticipate.git

# Install GDAL

RUN add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable \
  && apt-get update \
  && apt-get install -y \
  gdal-bin \
  python3-gdal

# Install required packages

RUN pip3 install --upgrade pip

RUN pip3 install geopandas==0.4.0
RUN pip3 install flask flask-headers

# Configure system to use gunicorn to host the website when the container is started

RUN apt-get install -y \
  nginx \
  supervisor

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

COPY /Files/demo /etc/nginx/sites-available/demo

RUN ln -s /etc/nginx/sites-available/demo /etc/nginx/sites-enabled/demo

RUN pip3 install gunicorn

RUN cd /home/source/pyticipate \
  && echo "" >> scenario_webapi.py \
  && echo "" >> scenario_webapi.py \
  && echo "application = app" >> scenario_webapi.py \
  && echo "if __name__ == '__main__':" >> scenario_webapi.py \
  && echo "    application.run()" >> scenario_webapi.py

ENV SCENARIO_LANG en-au
ENV SCENARIO_PY /home/source/pyticipate/demo/scenario.py
ENV PYTHONPATH /home/source/pyticipate/demo

COPY /Files/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5051

WORKDIR /home/source/pyticipate

CMD /usr/bin/supervisord
