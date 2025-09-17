"""Vista administrative models"""

from pydantic import Field

from ..base import BaseVistaModel


class User(BaseVistaModel):
    """Provider/user information"""

    duz: str = Field(..., description="User DUZ")
    name: str
    title: str | None = None
    service: str | None = None
    phone: str | None = None
    pager: str | None = None
    email: str | None = None
    role: str | None = None
    active: bool = True
    station: str | None = None


class Station(BaseVistaModel):
    """Vista station information"""

    number: str = Field(..., description="Station number")
    name: str
    division: str | None = None
    timezone: str | None = None
    active: bool = True


class RpcParameter(BaseVistaModel):
    """RPC parameter structure"""

    string: str | None = None
    array: list[str] | None = None
    ref: str | None = None
    named_array: dict[str, str] | None = None
