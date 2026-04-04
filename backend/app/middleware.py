import json
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

CURFEW_PATHS = ("/rules", "/questions")
CURFEW_START = 22
CURFEW_END = 4


class AdabCurfewMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # GET requests always pass through
        if request.method == "GET":
            return await call_next(request)

        # Only enforce curfew on specific paths
        if not any(request.url.path.startswith(p) for p in CURFEW_PATHS):
            return await call_next(request)

        # Check if it's curfew time
        now = datetime.now()
        hour = now.hour
        is_curfew = hour >= CURFEW_START or hour < CURFEW_END

        if not is_curfew:
            return await call_next(request)

        # During curfew: read body to check for emergency override
        body_bytes = await request.body()

        try:
            body_json = json.loads(body_bytes) if body_bytes else {}
        except (json.JSONDecodeError, ValueError):
            body_json = {}

        if body_json.get("emergency_override") is True:
            # Reconstruct the receive callable so downstream can read body again
            async def receive():
                return {"type": "http.request", "body": body_bytes, "more_body": False}

            request = Request(request.scope, receive)
            return await call_next(request)

        return JSONResponse(
            status_code=403,
            content={"detail": "Write access is restricted during curfew hours (10PM–4AM)."},
        )
