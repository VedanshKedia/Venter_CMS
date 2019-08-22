
FROM tiangolo/uwsgi-nginx:python3.6

ENV NGINX_MAX_UPLOAD 16m
# If you prefer miniconda:
#FROM continuumio/miniconda3


ENV LISTEN_PORT=8000
EXPOSE 8000

ENV DJANGO_SECRET_KEY p!63vi=_4)o5h8k0ep4uy2e6ou^k$9wels#e&&x=^^!=$xa21o

# Indicate where uwsgi.ini lives
ENV UWSGI_INI uwsgi.ini

# Tell nginx where static files live (as typically collected using Django's
# collectstatic command.


WORKDIR /app

COPY requirements.txt /app

# Using pip:
RUN python3 -m pip install -r requirements.txt

ENV STATIC_URL /app/static/
COPY . /app

# Make app folder writable for the sake of db.sqlite3, and make that file also writable
RUN chmod g+w /app
RUN chmod g+w /app/db.sqlite3


# ssh
ENV SSH_PASSWD "root:Docker!"
RUN apt-get update \
        && apt-get install -y --no-install-recommends dialog \
        && apt-get update \
	&& apt-get install -y --no-install-recommends openssh-server \
	&& echo "$SSH_PASSWD" | chpasswd 

COPY sshd_config /etc/ssh/
COPY init.sh /usr/local/bin/
	
RUN chmod u+x /usr/local/bin/init.sh
EXPOSE 8000 2222
CMD ["python", "/app/manage.py", "runserver", "0.0.0.0:8000"]
ENTRYPOINT ["init.sh"]
