import pytest
import gevent

from aviasales.task import task, t_cached


class NoCacheChecker:
    def __init__(self):
        self.cnt = 0

    @property
    def value(self):
        self.cnt += 1
        return 1


no_cache_checker = NoCacheChecker()


@t_cached()
@task()
def simple_task1(a1, a2, kw1=None, kw2=None, cache_checker=no_cache_checker):
    return cache_checker.value


@t_cached()
@task()
def simple_task2(a1, a2, kw1=None, kw2=None, cache_checker=no_cache_checker):
    return cache_checker.value


@pytest.mark.parametrize("task, args, kwargs, cnt", [
    (simple_task1, (1, 2), {'kw1': 1, 'kw2': 2}, 1),
    (simple_task1, (1, 2), {'kw1': 1, 'kw2': 2}, 1),
    (simple_task1, (1, 1), {'kw1': 1, 'kw2': 2}, 2),
    (simple_task1, (1, 1), {'kw1': 1, 'kw2': 1}, 3),
    (simple_task2, (1, 2), {'kw1': 1, 'kw2': 2}, 4),
    (simple_task2, (1, 2), {'kw1': 1, 'kw2': 2}, 4),
])
def test_task_cache(task, args, kwargs, cnt):
    res = task(*args, **kwargs).result
    assert no_cache_checker.cnt == cnt


def test_task_async_work():
    cache_checker = NoCacheChecker()

    @t_cached()
    @task()
    def long_task(exception=None):
        gevent.sleep(2)
        value = cache_checker.value
        if exception:
            raise exception
        return value

    def do_task(task, **kwargs):
        t = task(**kwargs)
        try:
            return t.result
        except Exception:
            pass

    t1 = gevent.spawn(do_task, long_task)
    t2 = gevent.spawn(do_task, long_task)
    gevent.joinall([t1, t2])

    assert cache_checker.cnt == 1

    t3 = gevent.spawn(do_task, long_task, exception=Exception)
    t3.join()
    assert cache_checker.cnt == 2

    # проверка, что после падения задачи задача вычищается из кэша
    t4 = gevent.spawn(do_task, long_task, exception=Exception)
    t4.join()
    assert cache_checker.cnt == 3
