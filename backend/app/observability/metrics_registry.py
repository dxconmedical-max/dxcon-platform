METRIC_DEFINITIONS = {
    "http_requests_total": {"type": "counter", "description": "HTTP requests processed"},
    "api_latency_ms": {"type": "histogram", "description": "API request latency"},
    "database_latency_ms": {"type": "histogram", "description": "Database query latency"},
    "queue_depth": {"type": "gauge", "description": "Background/integration queue depth"},
    "webhook_latency_ms": {"type": "histogram", "description": "Webhook delivery latency"},
    "notification_latency_ms": {"type": "histogram", "description": "Notification delivery latency"},
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
