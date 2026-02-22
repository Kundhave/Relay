import uuid
import httpx
from celery.exceptions import MaxRetriesExceededError
from .celery_app import celery_app
from .database import SessionLocal
from .models import WebhookEvent, EventStatus


@celery_app.task(name="deliver_webhook", bind=True, max_retries=5)
def deliver_webhook(self, event_id: str):
    db = SessionLocal()
    try:
        event = db.query(WebhookEvent).filter(
            WebhookEvent.id == uuid.UUID(event_id)
        ).first()

        if not event:
            print(f"WARNING: Event {event_id} not found")
            return

        try:
            response = httpx.post(
                event.target_url,
                json=event.payload,
                headers={"X-Relay-Event-Id": event_id},
                timeout=10.0,
            )

            if 200 <= response.status_code < 300:
                event.status = EventStatus.SUCCESS
                event.attempts += 1
                db.commit()
                return

            elif 400 <= response.status_code < 500:
                event.status = EventStatus.FAILED
                event.attempts += 1
                db.commit()
                return

            else:
                # 5xx — retry with exponential backoff
                event.attempts += 1
                db.commit()
                try:
                    self.retry(
                        countdown=2 ** self.request.retries,
                        exc=Exception(f"Server error: {response.status_code}"),
                    )
                except MaxRetriesExceededError:
                    event.status = EventStatus.DEAD_LETTER
                    db.commit()
                    return

        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            print(f"Delivery failed for event {event_id}: {e}")
            event.attempts += 1
            db.commit()
            try:
                self.retry(
                    countdown=2 ** self.request.retries,
                    exc=e,
                )
            except MaxRetriesExceededError:
                event.status = EventStatus.DEAD_LETTER
                db.commit()
                return

    finally:
        db.close()
