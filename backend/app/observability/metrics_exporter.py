from app.observability.metrics_service import MetricsPlatformService


def export_metrics_payload(app):
    return MetricsPlatformService.get_metrics(app)


def export_system_payload(app):
    return MetricsPlatformService.get_system_metrics(app)


def export_business_payload(app):
    return MetricsPlatformService.get_business_metrics(app)
