FROM python:3.7

# Prepare Python's venv
COPY requirements.txt /srv
COPY Makefile /srv
WORKDIR /srv

# Copy app source
COPY ./srv /srv

RUN  make setup && chmod +x ./run_web.sh && useradd flask && chown -R flask ./instance
USER flask

# Run target
EXPOSE 5000
CMD ["./run_web.sh"]