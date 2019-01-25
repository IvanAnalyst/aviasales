from .models import FlightsInfo, Flights, FlightsInfoXmlParser
from .task import task, t_cached


@t_cached()
@task()
def get_flights_task(*args, **kwargs):
    flights_info = FlightsInfo.get_xml(**kwargs)
    flights = Flights.from_flights_info(flights_info, FlightsInfoXmlParser)
    return flights
