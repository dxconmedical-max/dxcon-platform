from app.integrations.base_adapter import DemoAdapter


class HISAdapter(DemoAdapter):
    adapter_type = "HIS"
    vendor_label = "Demo HIS"


class LISAdapter(DemoAdapter):
    adapter_type = "LIS"
    vendor_label = "Demo LIS"


class ERPAdapter(DemoAdapter):
    adapter_type = "ERP"
    vendor_label = "Demo ERP"


class CRMAdapter(DemoAdapter):
    adapter_type = "CRM"
    vendor_label = "Demo CRM"


class InsuranceAdapter(DemoAdapter):
    adapter_type = "INSURANCE"
    vendor_label = "Demo Insurance"


class PaymentAdapter(DemoAdapter):
    adapter_type = "PAYMENT"
    vendor_label = "Demo Payment"


class NotificationAdapter(DemoAdapter):
    adapter_type = "NOTIFICATION"
    vendor_label = "Demo Notification"


class AIAdapter(DemoAdapter):
    adapter_type = "AI"
    vendor_label = "Demo AI"


ADAPTER_CLASSES = {
    "HIS": HISAdapter,
    "LIS": LISAdapter,
    "ERP": ERPAdapter,
    "CRM": CRMAdapter,
    "INSURANCE": InsuranceAdapter,
    "PAYMENT": PaymentAdapter,
    "NOTIFICATION": NotificationAdapter,
    "AI": AIAdapter,
}
