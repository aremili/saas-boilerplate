from contextvars import ContextVar
from typing import Optional

current_tenant_id: ContextVar[Optional[int]] = ContextVar("current_tenant_id", default=None)
