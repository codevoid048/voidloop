from datetime import date
from typing import Optional

from ninja import Router

from _sdk.decorators import require_auth
from stats.schemas import StatsResponseSchema
from stats.services import StatsService

stats_router = Router(tags=["Stats"])


@stats_router.get("", response={200: StatsResponseSchema})
@require_auth
def get_stats(
    request,
    since: Optional[date] = None,
    until: Optional[date] = None,
):
    """
    Dashboard stats for a date range (defaults to last 30 days, max 90).

    Query params:
    - since: YYYY-MM-DD
    - until: YYYY-MM-DD
    """
    return StatsService.get_dashboard(
        request.auth_user,
        since=since,
        until=until,
    )
