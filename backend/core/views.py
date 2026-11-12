from django.db import connection
from django.http import JsonResponse


def health(request):
    """Public health check used by Render (and handy for debugging)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ok", "database": "up"})
    except Exception:  # noqa: BLE001 - we only want to report "down"
        return JsonResponse({"status": "error", "database": "down"}, status=503)
