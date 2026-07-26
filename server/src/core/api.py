from ninja import NinjaAPI
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.http import Http404

from _sdk.exceptions import TrackerException
from _sdk.ninja_handlers import (
    tracker_exception_handler,
    validation_error_handler,
    http_error_handler,
    permission_denied_handler,
    object_not_found_handler,
    generic_error_handler,
)

from users.api import auth_router, invites_router
from habits.api import habits_router
from tasks.api import tasks_router
from notes.api import notes_router
from stats.api import stats_router

api = NinjaAPI(
    title="Void Loop API",
    version="1.0.0",
    description="Backend API for Void Loop — habits, tasks, notes, and stats",
    docs_url="/docs",  # Accessible at /api/v1/docs
)

# Register exception handlers (order matters - most specific first)
api.add_exception_handler(TrackerException, tracker_exception_handler)
api.add_exception_handler(ValidationError, validation_error_handler)
api.add_exception_handler(Http404, http_error_handler)
api.add_exception_handler(PermissionDenied, permission_denied_handler)
api.add_exception_handler(ObjectDoesNotExist, object_not_found_handler)
api.add_exception_handler(Exception, generic_error_handler)  # Catch-all


@api.get("/health")
def health_check(request):
    return {"status": "ok", "message": "Void Loop API running smoothly."}


# Register app routers
api.add_router("/auth", auth_router)
api.add_router("/invites", invites_router)
api.add_router("/habits", habits_router)
api.add_router("/tasks", tasks_router)
api.add_router("/notes", notes_router)
api.add_router("/stats", stats_router)
