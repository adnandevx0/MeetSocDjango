"""
Request ID middleware.
"""
import uuid

from django.utils.deprecation import MiddlewareMixin


class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.request_id = request.META.get("HTTP_X_REQUEST_ID", str(uuid.uuid4()))
