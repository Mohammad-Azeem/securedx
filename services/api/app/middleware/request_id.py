"""SecureDx AI — Request ID Middleware"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

REQUEST_ID_KEY = "X-Request-ID"

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get(REQUEST_ID_KEY, str(uuid.uuid4()))
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers[REQUEST_ID_KEY] = req_id
        return response

def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))
