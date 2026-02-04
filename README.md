# Relay  
### Fault-Tolerant Payment Webhook Orchestrator

Relay is a backend middleware system designed to **reliably deliver payment-related webhook notifications** (such as payment success, failure, refunds, or chargebacks) from internal payment services to external merchant systems.

It ensures that **critical financial events are never lost**, even in the presence of network failures, server crashes, or traffic spikes, while keeping core payment APIs fast and resilient.

---

## 🚀 Why Relay Exists

In payment systems, webhook notifications are **mission-critical**. Merchants rely on them to:

- Confirm successful payments
- Trigger order fulfillment
- Update invoices and ledgers
- Handle refunds or disputes

A naïve implementation sends payment webhooks **synchronously**, waiting for the merchant’s server to respond. This creates serious risks:

- Merchant servers may be slow or temporarily down
- Network failures are unpredictable
- A single slow merchant can block the payment API
- Traffic spikes (flash sales) can overwhelm systems

In payments, **losing a webhook is unacceptable**.

Relay solves this by introducing a **buffered, asynchronous, and fault-tolerant delivery pipeline** that guarantees reliable payment notification delivery without blocking the core payment flow.

---

## 🧠 Core Concepts

- **Asynchronous Processing** – Payment events are recorded instantly and delivered later
- **Loose Coupling** – Merchant system failures do not affect the payment API
- **At-Least-Once Delivery** – Payment notifications are never silently dropped
- **Fault Tolerance** – System survives crashes and partial failures
- **Horizontal Scalability** – Delivery workers scale independently
- **Observability** – Payment delivery health is visible in real time

---

## 🏗️ System Architecture

Payment Service
↓
FastAPI (Relay Ingress API)
↓
PostgreSQL (Source of Truth)
↓
Redis (Message Broker)
↓
Celery Workers
↓
Merchant Webhook Endpoints


---

## 🔄 Execution Flow

1. **Payment Event Ingestion**
   - Internal payment services send events such as `payment_succeeded`, `payment_failed`, or `refund_issued` to Relay.
   - Input is validated and immediately acknowledged with `202 Accepted`.

2. **Durable Persistence**
   - Events are written to PostgreSQL with status `PENDING`.
   - This guarantees durability even if the system crashes mid-flow.

3. **Task Dispatch**
   - The event ID is pushed to Redis, which acts as a message broker.

4. **Asynchronous Delivery**
   - Celery workers consume tasks from Redis.
   - Workers retrieve event data from PostgreSQL and attempt HTTP delivery to merchant webhook URLs.

5. **Success & Failure Handling**
   - `2xx` responses mark the event as `SUCCESS`.
   - `5xx` responses or timeouts trigger retries using exponential backoff.
   - `4xx` errors mark the event as `FAILED` (invalid payload or endpoint).

6. **Dead-Letter Handling**
   - Events that exceed retry limits are moved to `DEAD_LETTER` for manual review, preventing infinite retry loops.

---

## 🔐 Delivery Guarantees

### At-Least-Once Delivery
Relay guarantees that every payment notification is delivered **one or more times**.

This avoids catastrophic failures where a payment succeeds but the merchant is never notified due to transient issues.

### Idempotency
Each webhook includes an **idempotency key** so merchant systems can safely deduplicate repeated notifications and maintain financial correctness.

This mirrors real-world payment systems like Stripe and Razorpay.

---

## 📊 Observability & Monitoring

Relay is instrumented with **Prometheus** to expose metrics such as:

- Payment notification delivery latency
- Celery queue depth
- Retry and failure rates
- HTTP response code distribution per merchant

These metrics allow operators to:
- Detect failing merchant endpoints
- Identify delivery backlogs
- Scale workers proactively
- Ensure SLA compliance

---

## 🧱 Technology Stack

| Layer | Technology |
|-----|-----------|
| API Gateway | FastAPI |
| Database | PostgreSQL (JSONB) |
| Message Broker | Redis |
| Background Workers | Celery |
| Observability | Prometheus |
| Containerization | Docker & Docker Compose |

---

## 🐳 Containerization

Relay is fully containerized to ensure:

- Reproducible development and deployment environments
- Strong service isolation
- Easy local testing of payment flows
- Horizontal scaling of webhook delivery workers

All services (API, Redis, Postgres, Workers, Prometheus) run as independent containers managed via Docker Compose.

---

## 📁 Database Design (Simplified)

**payment_events table**
- `id`
- `event_type` (e.g. payment_succeeded, refund_issued)
- `payload` (JSONB)
- `merchant_webhook_url`
- `status` (PENDING | SUCCESS | FAILED | DEAD_LETTER)
- `retry_count`
- `next_attempt_at`
- `idempotency_key`
- timestamps

PostgreSQL acts as the **source of truth** for all payment event state.

---

## ⚠️ Failure Scenarios Handled

- Merchant webhook downtime
- Network timeouts during delivery
- Worker crashes mid-notification
- Flash-sale traffic spikes (thundering herd)
- Duplicate webhook deliveries
- Redis restarts
- Partial system failures

---

## 📈 Scalability

- Payment ingestion API remains stateless and fast
- Delivery workers scale horizontally based on traffic
- Redis buffers sudden spikes in payment events
- PostgreSQL maintains strong consistency via ACID guarantees

---

## 🎯 What This Project Demonstrates

- Payment system reliability design
- Distributed systems thinking
- Fault-tolerant architectures
- Asynchronous event processing
- Eventual consistency in financial systems
- Production-grade backend engineering trade-offs

---

## 🛣️ Future Improvements

- Circuit breakers per merchant
- Per-merchant rate limiting
- SLA-based priority queues
- Persistent retry scheduler
- Multi-region webhook delivery
- Admin dashboard for payment event inspection

---

## 📌 Summary

Relay is not just a webhook sender.

It is a **reliability layer for payment notifications**, ensuring that critical financial events are delivered safely, consistently, and observably — even when the external world is unreliable.

---
