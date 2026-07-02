"""Serve the built React SPA.

In production the Vite bundle lives in ``FRONTEND_DIST`` and its hashed assets
are served by WhiteNoise under ``/static/``. This view returns ``index.html`` for
every non-API route so client-side routing (react-router) works on deep links
and page refreshes.
"""
from django.conf import settings
from django.http import HttpResponse


def spa_index(request):
    index_file = settings.FRONTEND_DIST / "index.html"
    if not index_file.exists():
        return HttpResponse(
            "Frontend build not found. Run `npm run build` in ./frontend "
            "(or build the Docker image, which does this for you).",
            status=501,
            content_type="text/plain",
        )
    return HttpResponse(index_file.read_bytes(), content_type="text/html")
