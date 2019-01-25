from functools import wraps

import gevent
from cachetools import TTLCache, cached, keys

from .exceptions import TimeoutException

task_cache = TTLCache(maxsize=100, ttl=300)


class Task:
    TIC_LENGTH = 0.1  # длина тика - 1/10 секунды
    SERVICE_KWARGS_PREFIX = '_service_kwargs_'

    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs

        self._task = None
        self._timeout = None
        self._running = None
        self._result = None
        self.exception = None

    @property
    def _kwargs_without_service_kwargs(self):
        return {k: v for k, v in self._kwargs.items() if self.SERVICE_KWARGS_PREFIX not in k}

    @classmethod
    def service_kwargs(cls, **service_info_kwargs):
        return {k + cls.SERVICE_KWARGS_PREFIX: v for k, v in service_info_kwargs}

    @property
    def task_kwargs(self):
        return self._kwargs

    def run(self, timeout=None):
        if timeout:
            self._timeout = timeout
        self._result = None
        self._task = gevent.spawn(self._func, *self._args, **self._kwargs_without_service_kwargs)
        self._running = True
        try:
            self._task.join(gevent.Timeout(self._timeout, TimeoutException))
            self._result = self._task.value
        except TimeoutException:
            self.exception = TimeoutException
        finally:
            self.exception = self._task.exception
            self._task = None
            self._running = False

    @property
    def running(self):
        return self._running

    def _wait_result(self):
        """Ожидаем окончание выполнения задачи."""
        if self._timeout:
            n_tics = self._timeout / self.TIC_LENGTH
        else:
            n_tics = None

        if n_tics is None:
            is_valid_time = lambda: True
        else:
            is_valid_time = lambda cur_n: cur_n < n_tics

        n = 1
        while self.running and is_valid_time(n):
            gevent.sleep(self.TIC_LENGTH)
            n += 1

    def _wait_starting(self):
        """Ожидаем старта задачи."""
        while self.running is None:
            gevent.sleep(self.TIC_LENGTH)

    @property
    def result(self):
        if self.running is None:
            self._wait_starting()

        if self.running:
            self._wait_result()

        if self.exception:
            raise self.exception
        return self._result


def task(timeout=20):
    """Асинхронная задача."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t = Task(func, *args, **kwargs)
            gevent.spawn(t.run, timeout)
            return t
        return wrapper
    return decorator


def t_cached(cache=task_cache, key=keys.hashkey, lock=None):
    """Кэш для задач.

    Модификация стандартного декоратора `cached` из cachetools. Задачи, упавшие с ошибками, удаляются из кэша для
    возможности их повторного запуска.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            kwargs[Task.SERVICE_KWARGS_PREFIX + 'func_name_for_cache'] = func.__name__
            k = key(*args, **kwargs)
            t = cache.get(k)
            if t and t.running is False and t.exception is not None:
                cache.pop(k)
            return cached(cache, key, lock)(func)(*args, **kwargs)
        return wrapper
    return decorator
