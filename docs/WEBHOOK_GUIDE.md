# Webhook Guide

Create subscriptions: `POST /api/v1/integration/webhooks`

Requirements:
- HTTPS endpoints in production
- HMAC-SHA256 signatures with timestamp
- Replay protection (5-minute window)

Events: `order.created`, `sample.received`, `result.validated`, `report.released`, `payment.confirmed`

Delivery history: `GET /api/v1/integration/webhooks/{id}/deliveries`
