from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Same as the default DRF handler, plus a friendly message when someone tries
    to delete a record that other records depend on (for example a plan that
    already has memberships, or a member who has payment history).
    """
    if isinstance(exc, ProtectedError):
        return Response(
            {
                "detail": (
                    "This record is linked to other data (such as payments or memberships) "
                    "and cannot be deleted. Mark it as inactive instead."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
