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

    def get_laboratories(self, **kwargs):
        return self.request('GET', '/api/v1/laboratories', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_laboratories(self, **kwargs):
        return self.request('POST', '/api/v1/laboratories', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_test_catalogs(self, **kwargs):
        return self.request('GET', '/api/v1/test-catalogs', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_test_catalogs(self, **kwargs):
        return self.request('POST', '/api/v1/test-catalogs', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_orders(self, **kwargs):
        return self.request('GET', '/api/v1/orders', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_orders(self, **kwargs):
        return self.request('POST', '/api/v1/orders', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_order_items(self, **kwargs):
        return self.request('GET', '/api/v1/order-items', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_order_items(self, **kwargs):
        return self.request('POST', '/api/v1/order-items', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_sample_collections(self, **kwargs):
        return self.request('GET', '/api/v1/sample-collections', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_sample_collections(self, **kwargs):
        return self.request('POST', '/api/v1/sample-collections', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_test_results(self, **kwargs):
        return self.request('GET', '/api/v1/test-results', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_test_results(self, **kwargs):
        return self.request('POST', '/api/v1/test-results', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_ai_interpret(self, **kwargs):
        return self.request('POST', '/api/v1/ai/interpret', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_ai_risk(self, **kwargs):
        return self.request('POST', '/api/v1/ai/risk', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_ai_recommend(self, **kwargs):
        return self.request('POST', '/api/v1/ai/recommend', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_ai_reference_ranges(self, **kwargs):
        return self.request('GET', '/api/v1/ai/reference-ranges', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_ai_critical_results(self, **kwargs):
        return self.request('POST', '/api/v1/ai/critical-results', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_companies(self, **kwargs):
        return self.request('GET', '/api/v1/companies', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_companies(self, **kwargs):
        return self.request('POST', '/api/v1/companies', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_companies_company_id(self, **kwargs):
        return self.request('GET', '/api/v1/companies/<company_id>', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def put_companies_company_id(self, **kwargs):
        return self.request('PUT', '/api/v1/companies/<company_id>', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def delete_companies_company_id(self, **kwargs):
        return self.request('DELETE', '/api/v1/companies/<company_id>', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_marketplace_search(self, **kwargs):
        return self.request('GET', '/api/v1/marketplace/search', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_marketplace_bookings(self, **kwargs):
        return self.request('GET', '/api/v1/marketplace/bookings', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_marketplace_bookings(self, **kwargs):
        return self.request('POST', '/api/v1/marketplace/bookings', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_marketplace_bookings_booking_id(self, **kwargs):
        return self.request('GET', '/api/v1/marketplace/bookings/<booking_id>', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_marketplace_bookings_booking_id_transition(self, **kwargs):
        return self.request('POST', '/api/v1/marketplace/bookings/<booking_id>/transition', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_marketplace_bookings_booking_id_timeline(self, **kwargs):
        return self.request('GET', '/api/v1/marketplace/bookings/<booking_id>/timeline', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def get_partners(self, **kwargs):
        return self.request('GET', '/api/v1/partners', body=kwargs.get('body'), headers=kwargs.get('headers'))

    def post_partners(self, **kwargs):
        return self.request('POST', '/api/v1/partners', body=kwargs.get('body'), headers=kwargs.get('headers'))

