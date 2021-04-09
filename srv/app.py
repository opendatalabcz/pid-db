from flask import Flask
from celery import init_celery

app = Flask(__name__)
init_celery(app)

@app.route('/')
def hello():
    return "Hello World!"

if __name__ == '__main__':
        app.run()