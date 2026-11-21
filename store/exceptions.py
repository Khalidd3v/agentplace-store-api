from rest_framework import exceptions, status
from rest_framework.response import Response


def error_response(code, message, status_code):
    return Response({"success": False, "error": {"code": code, "message": message}}, status=status_code)


def custom_exception_handler(exc, context):
    """Return DRF errors (401, 405, ...) in the same JSON shape as the views."""
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        response = error_response(
            "UNAUTHORIZED", "Valid API credentials are required.", status.HTTP_401_UNAUTHORIZED
        )
        response["WWW-Authenticate"] = "Bearer"
        return response

    if isinstance(exc, exceptions.MethodNotAllowed):
        return error_response(
            "METHOD_NOT_ALLOWED", "This endpoint only supports GET.", status.HTTP_405_METHOD_NOT_ALLOWED
        )

    if isinstance(exc, exceptions.APIException):
        return error_response(exc.default_code.upper(), str(exc.default_detail), exc.status_code)

    return None
