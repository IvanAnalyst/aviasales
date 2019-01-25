from bottle import Bottle, request

from .http_errors import ErrorsWrapperPlugin
from .schemas import FlightsGeneralInfoSchema, FlightsSchema
from .tasks import get_flights_task

logic = Bottle()
logic.install(ErrorsWrapperPlugin())


@logic.get('/all')
def all_flights():
    flights = get_flights_task(**request.params).result
    return FlightsSchema().dump(flights)


@logic.get('/general_info')
def flights_general():
    flights = get_flights_task(**request.params).result
    return FlightsGeneralInfoSchema().dump(flights.general_info)


@logic.get('/cheapest')
def cheapest_flights():
    flights = get_flights_task(**request.params).result
    return FlightsSchema().dump({'flights': flights.top()})


@logic.get('/fastest')
def fastest_flights():
    flights = get_flights_task(**request.params).result
    return FlightsSchema().dump({'flights': flights.top(field_name='time')})


@logic.get('/optimal')
def optimal_flights():
    flights = get_flights_task(**request.params).result
    return FlightsSchema().dump({'flights': flights.top(field_name='optimality')})
