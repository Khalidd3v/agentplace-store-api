from rest_framework import exceptions, status
from rest_framework.response import Response


class InvalidId(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "INVALID_ID"
    default_detail = "The ID must be a valid UUID."


class ProductNotFound(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "PRODUCT_NOT_FOUND"
    default_detail = "Product was not found."


class OrderNotFound(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "ORDER_NOT_FOUND"
    default_detail = "Order was not found."


def error_body(code, message):
    return {"success": False, "error": {"code": code, "message": message}}


def api_exception_handler(exc, context):
    """Render every API error in the same `{success, error}` shape.

    Exceptions that are not APIExceptions return None, so Django produces a 500
    through `store.views.json_server_error` without leaking details.
    """
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        response = Response(
            error_body("UNAUTHORIZED", "Valid API credentials are required."),
            status=status.HTTP_401_UNAUTHORIZED,
        )
        response["WWW-Authenticate"] = "Bearer"
        return response

    if isinstance(exc, exceptions.MethodNotAllowed):
        return Response(
            error_body("METHOD_NOT_ALLOWED", "This endpoint only supports GET."),
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    if isinstance(exc, exceptions.APIException):
        code = exc.default_code.upper()
        message = exc.detail if isinstance(exc.detail, str) else str(exc.default_detail)
        return Response(error_body(code, str(message)), status=exc.status_code)

    return None
