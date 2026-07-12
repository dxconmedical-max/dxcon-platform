"""Auto-generated lightweight DxCon Python SDK stub."""

import json
from urllib import request, error


class DxConApiError(Exception):
    def __init__(self, status_code, payload):
        super().__init__(payload.get('error', payload))
        self.status_code = status_code
        self.payload = payload


class DxConClient:
    def __init__(self, base_url='http://localhost:5000', api_key=None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    def _headers(self, extra=None):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        if extra:
            headers.update(extra)
        return headers

    def request(self, method, path, body=None, headers=None):
        url = self.base_url + path
        data = None if body is None else json.dumps(body).encode('utf-8')
        req = request.Request(url, data=data, headers=self._headers(headers), method=method.upper())
        try:
            with request.urlopen(req) as resp:
                raw = resp.read().decode('utf-8')
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            payload = json.loads(exc.read().decode('utf-8') or '{}')
            raise DxConApiError(exc.code, payload) from exc

    def post_auth_register(self, **kwargs):
        return self.request('POST', '/api/v1/auth/register', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_auth_login(self, **kwargs):
        return self.request('POST', '/api/v1/auth/login', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_auth_refresh(self, **kwargs):
        return self.request('POST', '/api/v1/auth/refresh', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_auth_logout(self, **kwargs):
        return self.request('POST', '/api/v1/auth/logout', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_auth_me(self, **kwargs):
        return self.request('GET', '/api/v1/auth/me', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_auth_memberships(self, **kwargs):
        return self.request('GET', '/api/v1/auth/memberships', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_auth_switch_organization(self, **kwargs):
        return self.request('POST', '/api/v1/auth/switch-organization', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_auth_capabilities(self, **kwargs):
        return self.request('GET', '/api/v1/auth/capabilities', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_auth_forgot_password(self, **kwargs):
        return self.request('POST', '/api/v1/auth/forgot-password', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_auth_reset_password(self, **kwargs):
        return self.request('POST', '/api/v1/auth/reset-password', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_admin_users(self, **kwargs):
        return self.request('GET', '/api/v1/admin/users', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_patients(self, **kwargs):
        return self.request('GET', '/api/v1/patients', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_patients(self, **kwargs):
        return self.request('POST', '/api/v1/patients', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_patients_patient_id(self, **kwargs):
        return self.request('GET', '/api/v1/patients/<patient_id>', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def put_patients_patient_id(self, **kwargs):
        return self.request('PUT', '/api/v1/patients/<patient_id>', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def delete_patients_patient_id(self, **kwargs):
        return self.request('DELETE', '/api/v1/patients/<patient_id>', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_reception_dashboard(self, **kwargs):
        return self.request('GET', '/api/v1/reception/dashboard', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_reception_search(self, **kwargs):
        return self.request('GET', '/api/v1/reception/search', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_reception_register_quick(self, **kwargs):
        return self.request('POST', '/api/v1/reception/register/quick', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_reception_register_walk_in(self, **kwargs):
        return self.request('POST', '/api/v1/reception/register/walk-in', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_reception_check_in(self, **kwargs):
        return self.request('POST', '/api/v1/reception/check-in', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_reception_queue_entry_id_check_in(self, **kwargs):
        return self.request('POST', '/api/v1/reception/queue/<entry_id>/check-in', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_reception_queue_entry_id_check_out(self, **kwargs):
        return self.request('POST', '/api/v1/reception/queue/<entry_id>/check-out', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_reception_activity(self, **kwargs):
        return self.request('GET', '/api/v1/reception/activity', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_reception_kpi(self, **kwargs):
        return self.request('GET', '/api/v1/reception/kpi', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_dashboard(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/dashboard', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_health(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/health', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_connectors(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/connectors', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_adapters(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/adapters', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_webhooks(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/webhooks', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_api_keys(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/api-keys', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_retry_queue(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/retry-queue', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_dead_letters(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/dead-letters', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_integration_hub_audit(self, **kwargs):
        return self.request('GET', '/api/v1/integration-hub/audit', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_integration_hub_sandbox_test(self, **kwargs):
        return self.request('POST', '/api/v1/integration-hub/sandbox/test', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_ai_clinical_assistant_policy(self, **kwargs):
        return self.request('GET', '/api/v1/ai-clinical/assistant/policy', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_ai_clinical_assistant_interpret(self, **kwargs):
        return self.request('POST', '/api/v1/ai-clinical/assistant/interpret', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_ai_clinical_assistant_critical_review(self, **kwargs):
        return self.request('POST', '/api/v1/ai-clinical/assistant/critical-review', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_ai_clinical_dashboard(self, **kwargs):
        return self.request('GET', '/api/v1/ai-clinical/dashboard', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_ai_clinical_providers(self, **kwargs):
        return self.request('GET', '/api/v1/ai-clinical/providers', body=kwargs.get('body'), headers=kwargs.get('headers'))

