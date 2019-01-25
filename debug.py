from bottle import run

from aviasales.wsgi import app

run(app, host='localhost', port=8080)
