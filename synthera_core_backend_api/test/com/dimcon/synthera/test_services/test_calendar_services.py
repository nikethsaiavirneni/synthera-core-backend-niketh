import pytest
from com.dimcon.synthera.routes.req_routes import RequestRouter
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.utilities.log_handler import LoggerManager
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil

class TestCalendarServices:

    def test_get_month_view(self,patch_response_builder,patch_logger,patch_route_request,patch_session_scope):
