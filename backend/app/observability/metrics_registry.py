METRIC_DEFINITIONS = {
    "http_requests_total": {"type": "counter", "description": "HTTP requests processed"},
    "http_errors_total": {"type": "counter", "description": "HTTP error responses (4xx/5xx)"},
    "api_latency_ms": {"type": "histogram", "description": "API request latency"},
    "database_latency_ms": {"type": "histogram", "description": "Database query latency"},
    "db_health": {"type": "gauge", "description": "Database health (1=OK, 0=DOWN)"},
    "redis_health": {"type": "gauge", "description": "Redis health (1=OK, 0=DOWN)"},
    "queue_depth": {"type": "gauge", "description": "Background/integration queue depth"},
    "notification_delivery_success_total": {"type": "counter", "description": "Notifications delivered"},
    "notification_delivery_failures_total": {"type": "counter", "description": "Notification delivery failures"},
    "webhook_delivery_failures_total": {"type": "counter", "description": "Webhook delivery failures"},
    "webhook_latency_ms": {"type": "histogram", "description": "Webhook delivery latency"},
    "notification_latency_ms": {"type": "gauge", "description": "Notification delivery latency"},
    "background_job_pending": {"type": "gauge", "description": "Pending background jobs"},
    "background_job_failed": {"type": "gauge", "description": "Failed background jobs"},
    "readiness_ok": {"type": "gauge", "description": "Readiness probe status (1=ready, 0=not ready)"},
    "job_execution_ms": {"type": "histogram", "description": "Background job execution time"},
    "authentication_failures_total": {"type": "counter", "description": "Failed authentication attempts"},
    "login_success_rate": {"type": "gauge", "description": "Login success percentage"},
    "orders_created_total": {"type": "counter", "description": "Orders created"},
    "results_approved_total": {"type": "counter", "description": "Results approved"},
    "critical_results_total": {"type": "counter", "description": "Critical laboratory results"},
    "integration_failures_total": {"type": "counter", "description": "Integration failures"},
}


def list_metric_definitions():
    return [
        {"name": name, **meta}
        for name, meta in METRIC_DEFINITIONS.items()
    ]
