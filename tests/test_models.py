from os.path import abspath, join, dirname

import pytest

from aviasales.exceptions import FlightsNotFound
from aviasales.models import FlightsInfo, FlightsInfoXmlParser, Flights
from aviasales.settings import FLIGHTS_INFO_DIR_PATH


def one_way_with_child_and_infant_flights():
    dir_path = abspath(join(dirname(__file__), 'fixtures'))
    path_to_file = dir_path + '/one_way_with_child_and_infant.xml'
    return Flights.from_flights_info(path_to_file, FlightsInfoXmlParser)


def round_trip_adult_flights():
    dir_path = abspath(join(dirname(__file__), 'fixtures'))
    path_to_file = dir_path + '/round_trip_adult.xml'
    return Flights.from_flights_info(path_to_file, FlightsInfoXmlParser)


def test_flights_info_get_xml():
    params = {}
    assert FlightsInfo.get_xml(**params) == FLIGHTS_INFO_DIR_PATH + '/round_trip_adult.xml'

    params = {'with_child': 1, 'with_infant': 1, 'one_way': True}
    assert FlightsInfo.get_xml(**params) == FLIGHTS_INFO_DIR_PATH + '/one_way_with_child_and_infant.xml'

    params = {'with_child': 1}
    with pytest.raises(FlightsNotFound):
        FlightsInfo.get_xml(**params)


def test_collection_creating():
    with pytest.raises(AssertionError) as exc_info:
        Flights(None)

    assert 'must be iterable' in str(exc_info.value)

    fs = round_trip_adult_flights()

    # проверка __getitem__
    assert fs[0].pricing.currency == 'SGD'

    # проверка __iter__
    assert sum(1 for _ in fs) == 1

    # проверка __len__
    assert len(fs) == 1


def test_route():
    fs = round_trip_adult_flights()
    route = fs[0].onward_route

    assert route.n_transfers == 1
    assert route.source == 'DXB'
    assert route.destination == 'BKK'
