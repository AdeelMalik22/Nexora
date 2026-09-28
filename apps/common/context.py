from contextvars import ContextVar
from uuid import UUID


_current_shop_id: ContextVar[UUID | None] = ContextVar("current_shop_id", default=None)
_current_branch_id: ContextVar[UUID | None] = ContextVar("current_branch_id", default=None)


def set_tenant_context(shop_id: UUID, branch_id: UUID | None = None):
    return _current_shop_id.set(shop_id), _current_branch_id.set(branch_id)


def clear_tenant_context(tokens):
    shop_token, branch_token = tokens
    _current_shop_id.reset(shop_token)
    _current_branch_id.reset(branch_token)


def current_shop_id():
    return _current_shop_id.get()


def current_branch_id():
    return _current_branch_id.get()
