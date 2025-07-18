"""Vista administrative models"""

from pydantic import Field

from ..base import BaseVistaModel


class Appointment(BaseVistaModel):
    """Appointment information"""

    appointment_ien: str
    patient_ien: str
    patient_name: str
    date_time: str
    clinic_ien: str
    clinic_name: str
    status: str
    provider: dict[str, str] | None = None
    check_in_time: str | None = None
    check_out_time: str | None = None
    type: str | None = None
    length: int | None = None  # minutes


class Provider(BaseVistaModel):
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
