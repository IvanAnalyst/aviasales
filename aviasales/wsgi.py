from bottle import Bottle

from aviasales.views import logic as api_logic

app = Bottle()
app.mount('/api', api_logic)
