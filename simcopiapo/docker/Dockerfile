FROM ubuntu:bionic

# Install system programs

RUN apt-get update \
  && apt-get install -y \
  software-properties-common \
  git \
  gfortran \
  python3 \
  python3-pip \
  unzip \
  wget

# Copy ssh private key from host for non-interactive repo access by git

COPY /Auth/id_rsa /root/.ssh/id_rsa

RUN chmod 700 /root/.ssh/id_rsa \
  && echo "Host bitbucket.csiro.au" >> /root/.ssh/config \
  && echo "StrictHostKeyChecking no" >> /root/.ssh/config

# Download source code

RUN mkdir -p /home/source \
  && cd /home/source \
  && git clone -b develop ssh://git@bitbucket.csiro.au:7999/eis/pyticipate.git \
  && git clone -b develop ssh://git@bitbucket.csiro.au:7999/eis/simcopiapo.git

# Install required packages

RUN pip3 install --upgrade pip

RUN pip3 install enum34
RUN pip3 install -Iv xlrd==1.2.0
RUN pip3 install -Iv affine==2.2.1
RUN pip3 install -Iv numpy==1.16.2
RUN pip3 install -Iv pandas==0.24.2
RUN pip3 install -Iv flopy==3.2.10
RUN pip3 install -Iv geopandas==0.4.0
RUN pip3 install -Iv matplotlib==3.0.2
RUN pip3 install -Iv seaborn==0.9.0
RUN pip3 install -Iv python-docx==0.8.10
RUN pip3 install -Iv docxcompose==1.0.0a17
RUN pip3 install -Iv flask==1.0.3
RUN pip3 install flask-headers

# Install GDAL

RUN add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable \
  && apt-get update \
  && apt-get install -y \
  gdal-bin \
  python3-gdal

# Install rasterio

RUN apt-get install -y \
  python3-rasterio

# Install MODFLOW and copy application to source code directory

RUN mkdir -p /home/modflow \
  && cd /home/modflow \
  && wget https://water.usgs.gov/ogw/modflow-nwt/MODFLOW-NWT_1.1.4.zip \
  && unzip MODFLOW-NWT_1.1.4.zip \
  && cd /home \
  && git clone https://github.com/modflowpy/pymake.git \
  && cd pymake \
  && python3 setup.py install \
  && rm /home/source/simcopiapo/model/modflow/bin/* \
  && python3 -m pymake.pymake ../modflow/MODFLOW-NWT_1.1.4/src /home/source/simcopiapo/model/modflow/bin/mfnwt \
  && cd /home \
  && rm -r modflow \
  && rm -r pymake

# Configure system to use gunicorn to host the website when the container is started

RUN apt-get install -y \
  nginx \
  supervisor

# Alter nginx config to support a longer timeout (for run_scenario)

RUN sed '/http {/ a proxy_read_timeout 600;' /etc/nginx/nginx.conf > /home/nginx.conf \
  && mv /home/nginx.conf /etc/nginx/nginx.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

COPY /Files/simcopiapo /etc/nginx/sites-available/simcopiapo

RUN ln -s /etc/nginx/sites-available/simcopiapo /etc/nginx/sites-enabled/simcopiapo

RUN pip3 install gunicorn

RUN cd /home/source/pyticipate \
  && echo "" >> scenario_webapi.py \
  && echo "" >> scenario_webapi.py \
  && echo "application = app" >> scenario_webapi.py \
  && echo "if __name__ == '__main__':" >> scenario_webapi.py \
  && echo "    application.run()" >> scenario_webapi.py

# Hack for flopy (needs to find site-packages in sys.path call)

RUN mkdir /home/source/site-packages

ENV SCENARIO_LANG en-au
ENV SCENARIO_PY /home/source/simcopiapo/scenario_SIMC.py
ENV PYTHONPATH /home/source/pyticipate:/home/source/simcopiapo:/home/source/site-packages

COPY /Files/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5052

WORKDIR /home/source/pyticipate

CMD /usr/bin/supervisord
