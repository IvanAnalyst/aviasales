class AviasalesException(Exception):
    """Базовое исключение приложения.

    Прочие исключение должны наследоваться от него.
    """
    default_message = ''

    def __init__(self, *args):
        default = self.default_message

        if '%s' in default:
            # Сообщение по шаблону.
            msg = default % args

        else:
            # Сообщение из аргумента.
            try:
                msg = args[0]

            except IndexError:
                msg = None

        self.msg = msg or default

    def __str__(self):
        return self.msg


class UserException(AviasalesException):
    """Клиентские ошибки."""


class FlightsNotFound(UserException):
    """По запрошенным параметрам не было найдено перелетов."""
    default_message = 'Перелеты не найдены'


class TaskError(AviasalesException):
    """Ошибки, связанные с работой с задачами."""
    pass


class TimeoutException(TaskError):
    default_message = 'Задача не успела завершиться'
