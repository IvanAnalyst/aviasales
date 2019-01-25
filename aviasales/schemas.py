from marshmallow import Schema, fields


class RoutePartSchema(Schema):
    carrier = fields.Str(required=True)
    flight_number = fields.Str(required=True)
    source = fields.Str(required=True)
    departure_datetime = fields.DateTime(required=True, format='%Y-%m-%dT%H%M')
    arrival_datetime = fields.DateTime(required=True, format='%Y-%m-%dT%H%M')
    destination = fields.Str(required=True)
    class_type = fields.Str(required=True)
    ticket_type = fields.Str(required=True)

    class Meta:
        ordered = True


class RouteSchema(Schema):
    route = fields.List(fields.Nested(RoutePartSchema))

    time = fields.Int(dump_only=True)


class PricingSchema(Schema):
    currency = fields.Str(required=True)
    adult = fields.Decimal(required=True)
    child = fields.Decimal(allow_none=True)
    infant = fields.Decimal(allow_none=True)

    class Meta:
        ordered = True


class FlightSchema(Schema):
    pricing = fields.Nested(PricingSchema, required=True)
    onward_route = fields.List(fields.Nested(RoutePartSchema), required=True)
    return_route = fields.List(fields.Nested(RoutePartSchema), allow_none=True)

    n_transfers = fields.Int(dump_only=True)
    onward_dep_time = fields.DateTime(dump_only=True)
    onward_arr_time = fields.DateTime(dump_only=True)
    return_dep_time = fields.DateTime(dump_only=True)
    return_arr_time = fields.DateTime(dump_only=True)
    transfer_time = fields.Int(dump_only=True)
    airports = fields.List(fields.Str(), dump_only=True)
    carriers = fields.List(fields.Str(), dump_only=True)
    price = fields.Decimal(dump_only=True)

    class Meta:
        ordered = True


class FlightsSchema(Schema):
    flights = fields.List(fields.Nested(FlightSchema))


class FlightsGeneralInfoSchema(Schema):
    quantity = fields.Int()
    price = fields.List(fields.Decimal())
    time = fields.List(fields.Int())
    transfer_time = fields.List(fields.Int())
    onward_dep_time = fields.List(fields.DateTime())
    onward_arr_time = fields.List(fields.DateTime())
    return_dep_time = fields.List(fields.DateTime())
    return_arr_time = fields.List(fields.DateTime())
    airports = fields.List(fields.Str())
    carriers = fields.List(fields.Str())
    n_transfers = fields.List(fields.Int())

    class Meta:
        ordered = True
