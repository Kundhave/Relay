from pydantic import BaseModel


class EventRequest(BaseModel):
    merchant_id: str
    event_type: str  # e.g. "payment_succeeded", "payment_failed", "refund_issued"
    payload: dict
    target_url: str


class EventResponse(BaseModel):
    id: str
    status: str
    message: str
