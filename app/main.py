import time
import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from . import models  # noqa: F401 — must import to register models with Base.metadata
from .models import WebhookEvent, EventStatus
from .schemas import EventRequest, EventResponse
from .tasks import deliver_webhook

app = FastAPI()

@app.on_event("startup")
def startup_event():
    # Simple retry loop to wait for database to be ready
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as e:
            print(f"Database connection failed, retrying... ({retries} left)")
            retries -= 1
            time.sleep(5)
    else:
        print("Could not connect to database. Exiting.")
        raise Exception("Database connection failed after retries")

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "relay"}

@app.post("/events", response_model=EventResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(event: EventRequest, db: Session = Depends(get_db)):
    db_event = WebhookEvent(
        merchant_id=event.merchant_id,
        event_type=event.event_type,
        payload=event.payload,
        target_url=event.target_url,
        status=EventStatus.PENDING,
        attempts=0,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    deliver_webhook.delay(str(db_event.id))
    return EventResponse(
        id=str(db_event.id),
        status="PENDING",
        message="Event received and queued for delivery",
    )

@app.get("/events/{event_id}")
async def get_event_status(event_id: str, db: Session = Depends(get_db)):
    event = db.query(WebhookEvent).filter(
        WebhookEvent.id == uuid.UUID(event_id)
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "id": str(event.id),
        "merchant_id": event.merchant_id,
        "event_type": event.event_type,
        "status": event.status.value,
        "attempts": event.attempts,
        "target_url": event.target_url,
        "created_at": event.created_at.isoformat(),
        "updated_at": event.updated_at.isoformat(),
    }
