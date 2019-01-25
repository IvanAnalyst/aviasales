from abc import abstractmethod, ABC
from collections import Iterable
from decimal import Decimal

from lxml import etree

from .exceptions import FlightsNotFound
from .settings import FLIGHTS_INFO_DIR_PATH
from .schemas import PricingSchema, RoutePartSchema


class FlightsInfo:
    """Информация о перелетах (от партнера)."""
    @staticmethod
    def is_round_trip_adult_flight(**params):
        """Является ли билетом в обе стороны только для взрослого пассажира."""
        return not params

    @staticmethod
    def is_one_way_with_child_and_infant_flight(**params):
        """Является ли билетом в одну сторону для взрослого, ребенка и младенца."""
        return 'with_child' in params and 'with_infant' in params and 'one_way' in params

    @classmethod
    def get_xml(cls, **params):
        """Возвращает путь к xml файлу с информацией о перелетах."""
        if cls.is_round_trip_adult_flight(**params):
            return FLIGHTS_INFO_DIR_PATH + 'round_trip_adult.xml'

        if cls.is_one_way_with_child_and_infant_flight(**params):
            return FLIGHTS_INFO_DIR_PATH + 'one_way_with_child_and_infant.xml'

        raise FlightsNotFound


class FlightsInfoXmlParser:
    tag_field_mapping = {
        'Carrier': 'carrier',
        'FlightNumber': 'flight_number',
        'Source': 'source',
        'Destination': 'destination',
        'DepartureTimeStamp': 'departure_datetime',
        'ArrivalTimeStamp': 'arrival_datetime',
        'Class': 'class_type',
        'TicketType': 'ticket_type',
        'SingleAdult': 'adult',
        'SingleChild': 'child',
        'SingleInfant': 'infant',
    }

    @classmethod
    def _route_parts(cls, route_info):
        for route_part in route_info:
            route_part_params = {}
            for detail in route_part:
                field_name = cls.tag_field_mapping.get(detail.tag)
                if field_name:
                    route_part_params[field_name] = detail.text
            yield RoutePart(**RoutePartSchema().load(route_part_params))

    @classmethod
    def _get_route_from_xml_element(cls, xml_element, xpath):
        route_parts_info = xml_element.xpath(xpath)
        if not route_parts_info:
            return None
        return Route(cls._route_parts(route_parts_info), with_validate=False)

    @classmethod
    def _get_pricing_from_xml_element(cls, xml_element, xpath):
        pricing_info = xml_element.xpath(xpath)[0]
        pricing_params = dict(currency=pricing_info.get('currency'))

        for price in pricing_info:
            details = price.attrib
            if details.get('ChargeType') == 'TotalAmount':
                p_type = details.get('type')
                field_name = cls.tag_field_mapping[p_type]
                pricing_params[field_name] = price.text

        return Pricing(**PricingSchema().load(pricing_params))

    @classmethod
    def _get_flight_from_xml_element(cls, xml_element):
        pricing = cls._get_pricing_from_xml_element(xml_element, 'Pricing')
        onward_route = cls._get_route_from_xml_element(xml_element, 'OnwardPricedItinerary/Flights/Flight')
        return_route = cls._get_route_from_xml_element(xml_element, 'ReturnPricedItinerary/Flights/Flight')

        return Flight(pricing, onward_route, return_route)

    @classmethod
    def _flight_elements(cls, path_to_file):
        level = 0
        for event, element in etree.iterparse(path_to_file, events=('start', 'end'), tag=('Flights',)):
            if event == 'start':
                level += 1
            elif event == 'end':
                level -= 1

            if level != 0:
                continue

            yield element

            element.clear()

    @classmethod
    def flights(cls, path_to_file):
        """Возвращает объекты типа Flight."""
        for element in cls._flight_elements(path_to_file):
            yield cls._get_flight_from_xml_element(element)


class Collection(ABC):
    def __init__(self, elements, with_validate=True):
        assert isinstance(elements, Iterable), '{} elements must be iterable object'
        self._elements = list(elements)
        if with_validate:
            self._validate()

    def __getitem__(self, ind):
        return self._elements[ind]

    def __iter__(self):
        return iter(self._elements)

    def __len__(self):
        return len(self._elements)

    @property
    def _class_name(self):
        return type(self).__name__

    @property
    @abstractmethod
    def element_type(self):
        pass

    def _validate(self):
        assert len(self._elements), '{} must have one element at least'.format(self._class_name)
        for element in self._elements:
            assert isinstance(element, self.element_type), \
                '{} elements must be {} type'.format(self._class_name, self.element_type)


class Pricing:
    """Цены на билеты."""
    def __init__(self, currency, adult, child=None, infant=None):
        self.currency = currency
        self.adult = adult
        self.child = child
        self.infant = infant

    @property
    def full(self):
        def to_float(price):
            return price if price is not None else 0

        return sum(to_float(field) for field in (self.adult, self.child, self.infant))


class RoutePart:
    """Минимальная составная единица маршрута Route (перелет из source в destination)."""
    def __init__(self, carrier, flight_number,
                 source, destination,
                 departure_datetime, arrival_datetime,
                 class_type, ticket_type):
        self.carrier = carrier
        self.flight_number = flight_number
        self.source = source
        self.destination = destination
        self.departure_datetime = departure_datetime
        self.arrival_datetime = arrival_datetime
        self.class_type = class_type
        self.ticket_type = ticket_type


class Route(Collection):
    """Маршрут целиком, хранящий части маршрута типа RoutePart."""
    element_type = RoutePart

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.route = self._elements

    @property
    def n_transfers(self):
        """Число пересадок."""
        return len(self) - 1

    @property
    def transfer_time(self):
        """Время самой продолжительной пересадки."""
        if not self.n_transfers:
            return 0
        return max((self[i+1].departure_datetime - self[i].arrival_datetime).seconds for i in range(len(self) - 1))

    @property
    def source(self):
        """Откуда."""
        return self[0].source

    @property
    def destination(self):
        """Куда."""
        return self[-1].destination

    @property
    def time(self):
        """Время полета в секундах."""
        return (self[-1].arrival_datetime - self[0].departure_datetime).seconds

    @property
    def departure_datetime(self):
        return self[0].departure_datetime

    @property
    def arrival_datetime(self):
        return self[-1].arrival_datetime

    @property
    def carriers(self):
        return {rp.carrier for rp in self}

    @property
    def airports(self):
        return {airport for rp in self for airport in (rp.source, rp.destination)}


class NoRoute:
    """Заглушка для маршрута."""
    def __getattr__(self, item):
        return None


class Flight:
    """Информация о перелете."""
    def __init__(self, pricing, onward_route, return_route=None):
        self.pricing = pricing
        self.onward_route = onward_route
        self.return_route = return_route or NoRoute()

    @property
    def price(self):
        return self.pricing.full

    @property
    def time(self):
        return self.onward_route.time + (self.return_route.time or 0)

    def optimality(self, min_price, max_price, min_time, max_time):
        """Оптимальность полета (чем меньше, тем лучше)."""
        price = (self.price - min_price) / (max_price - min_price) if max_price != min_price else 1
        time = (self.time - min_time) / (max_time - min_time) if max_time != min_time else 1

        return Decimal(0.7) * price + Decimal(0.3 * time)

    @staticmethod
    def without_none(*iterable):
        return filter(lambda i: i is not None, iterable)

    @staticmethod
    def concat_to_unique_list(iterable_or_none1, iterable_or_none2):
        res = set(iterable_or_none1 or [])
        res.update(set(iterable_or_none2 or []))
        return list(res)

    @property
    def n_transfers(self):
        """Максимальное число пересадок среди маршрутов туда и обратно."""
        return max(self.without_none(self.onward_route.n_transfers, self.return_route.n_transfers))

    @property
    def transfer_time(self):
        """Максимальное время пересадки среди маршрутов туда и обратно."""
        return max(self.without_none(self.onward_route.transfer_time, self.return_route.transfer_time))

    @property
    def carriers(self):
        return self.concat_to_unique_list(self.onward_route.carriers, self.return_route.carriers)

    @property
    def airports(self):
        return self.concat_to_unique_list(self.onward_route.airports, self.return_route.airports)

    @property
    def onward_dep_time(self):
        return self.onward_route.departure_datetime

    @property
    def onward_arr_time(self):
        return self.onward_route.arrival_datetime

    @property
    def return_dep_time(self):
        return self.return_route.departure_datetime

    @property
    def return_arr_time(self):
        return self.return_route.arrival_datetime


class Flights(Collection):
    """Список перелетов Flight."""
    element_type = Flight

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flights = self._elements
        self._calculate_general_info()

    def _calculate_general_info(self):
        self.general_info = dict()
        self.general_info['quantity'] = len(self)

        # да, это неоптимально по количеству проходов по Flights, но лень делать оптимально :)
        for f_name in ('price', 'time', 'transfer_time', 'onward_dep_time', 'onward_arr_time',
                       'return_dep_time', 'return_arr_time'):
            self.general_info[f_name] = self._calculate_field_borders(f_name)

        for f_name in ('airports', 'carriers'):
            self.general_info[f_name] = list(set(elem for f in self for elem in getattr(f, f_name)))

        f_name = 'n_transfers'
        self.general_info[f_name] = list(set(getattr(f, f_name) for f in self))

    def _calculate_field_borders(self, field_name):
        values = {getattr(f, field_name) for f in self}
        if not values or None in values:
            return None
        return min(values), max(values)

    @classmethod
    def from_flights_info(cls, flights_info, info_parser):
        return cls(info_parser.flights(flights_info), with_validate=False)

    def top(self, field_name='price', number=10, reverse=False):
        assert field_name in ('price', 'time', 'optimality')

        if field_name == 'optimality':
            key = lambda f: f.optimality(*self.general_info['price'], *self.general_info['time'])
        else:
            key = lambda x: getattr(x, field_name)

        return sorted(self, key=key, reverse=reverse)[:number]
