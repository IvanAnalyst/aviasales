from bottle import HTTPError

from .exceptions import FlightsNotFound, UserException, AviasalesException


class ErrorsWrapperPlugin:
    def apply(self, callback, route):
        def wrapper(*a, **ka):
            try:
                return callback(*a, **ka)
            except FlightsNotFound as e:
                raise HTTPError(404, e)
            except UserException as e:
                raise HTTPError(400, e.msg)
            except AviasalesException as e:
                raise HTTPError(500, e.msg)

        return wrapper
