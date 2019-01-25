import pytest
from webtest import TestApp

from aviasales.views import logic


@pytest.mark.parametrize("path, get_params, expected_status", [
    ('/unknown_path', None, 404),
    ('/all', None, 200),
    ('/all', 'one_way&with_child&with_infant', 200),
    ('/all', 'unknown_param', 404),
    ('/general_info', None, 200),
    ('/general_info', 'one_way&with_child&with_infant', 200),
    ('/cheapest', None, 200),
    ('/fastest', None, 200),
    ('/optimal', None, 200),
])
def test_api(path, get_params, expected_status):
    app = TestApp(logic)

    assert app.get(path +'?%s' % (get_params or ''), status=expected_status).status_code == expected_status
