from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.common.auth.security import decode_token
from app.core.context import current_tenant_id
from app.core.logging import get_logger

logger = get_logger(__name__)

class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant_id from JWT token and set it in context.
    This runs before database session creation, allowing RLS to work.
    """
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        tenant_id = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # We decode the token to get tenant_id. 
                # Full validation happens in dependencies, but signature check happens here too.
                payload = decode_token(token)
                if payload:
                    # tenant_id might be None for global admins or if not set yet
                    # But we treat it as int if present
                    tid = payload.get("tenant_id")
                    if tid is not None:
                        tenant_id = int(tid)
            except Exception as e:
                logger.debug(f"Failed to extract tenant from token: {e}")
        
        # Set context
        token_ctx = current_tenant_id.set(tenant_id)
        try:
            response = await call_next(request)
            return response
        finally:
            current_tenant_id.reset(token_ctx)
