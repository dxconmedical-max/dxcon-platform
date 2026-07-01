/** Auto-generated lightweight DxCon TypeScript SDK stub. */

export class DxConApiError extends Error {
  statusCode: number;
  payload: Record<string, unknown>;
  constructor(statusCode: number, payload: Record<string, unknown>) {
    super(JSON.stringify(payload));
    this.statusCode = statusCode;
    this.payload = payload;
  }
}

export class DxConClient {
  baseUrl: string;
  apiKey?: string;

  constructor(baseUrl = 'http://localhost:5000', apiKey?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
  }

  async request(method: string, path: string, body?: unknown, headers: Record<string, string> = {}) {
    const finalHeaders: Record<string, string> = { 'Content-Type': 'application/json', ...headers };
    if (this.apiKey) finalHeaders['X-API-Key'] = this.apiKey;
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: method.toUpperCase(),
      headers: finalHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new DxConApiError(response.status, payload as Record<string, unknown>);
    return payload;
  }

  async post_auth_register(body?: unknown) {
    return this.request('POST', '/api/v1/auth/register', body);
  }

  async post_auth_login(body?: unknown) {
    return this.request('POST', '/api/v1/auth/login', body);
  }

  async post_auth_refresh(body?: unknown) {
    return this.request('POST', '/api/v1/auth/refresh', body);
  }

  async post_auth_logout(body?: unknown) {
    return this.request('POST', '/api/v1/auth/logout', body);
  }

  async get_admin_users(body?: unknown) {
    return this.request('GET', '/api/v1/admin/users', body);
  }

  async get_patients(body?: unknown) {
    return this.request('GET', '/api/v1/patients', body);
  }

  async post_patients(body?: unknown) {
    return this.request('POST', '/api/v1/patients', body);
  }

  async get_patients_patient_id(body?: unknown) {
    return this.request('GET', '/api/v1/patients/<patient_id>', body);
  }

  async put_patients_patient_id(body?: unknown) {
    return this.request('PUT', '/api/v1/patients/<patient_id>', body);
  }

  async delete_patients_patient_id(body?: unknown) {
    return this.request('DELETE', '/api/v1/patients/<patient_id>', body);
  }

  async get_laboratories(body?: unknown) {
    return this.request('GET', '/api/v1/laboratories', body);
  }

  async post_laboratories(body?: unknown) {
    return this.request('POST', '/api/v1/laboratories', body);
  }

  async get_test_catalogs(body?: unknown) {
    return this.request('GET', '/api/v1/test-catalogs', body);
  }

  async post_test_catalogs(body?: unknown) {
    return this.request('POST', '/api/v1/test-catalogs', body);
  }

  async get_orders(body?: unknown) {
    return this.request('GET', '/api/v1/orders', body);
  }

  async post_orders(body?: unknown) {
    return this.request('POST', '/api/v1/orders', body);
  }

  async get_order_items(body?: unknown) {
    return this.request('GET', '/api/v1/order-items', body);
  }

  async post_order_items(body?: unknown) {
    return this.request('POST', '/api/v1/order-items', body);
  }

  async get_sample_collections(body?: unknown) {
    return this.request('GET', '/api/v1/sample-collections', body);
  }

  async post_sample_collections(body?: unknown) {
    return this.request('POST', '/api/v1/sample-collections', body);
  }

  async get_test_results(body?: unknown) {
    return this.request('GET', '/api/v1/test-results', body);
  }

  async post_test_results(body?: unknown) {
    return this.request('POST', '/api/v1/test-results', body);
  }

  async post_ai_interpret(body?: unknown) {
    return this.request('POST', '/api/v1/ai/interpret', body);
  }

  async post_ai_risk(body?: unknown) {
    return this.request('POST', '/api/v1/ai/risk', body);
  }

  async post_ai_recommend(body?: unknown) {
    return this.request('POST', '/api/v1/ai/recommend', body);
  }

  async get_ai_reference_ranges(body?: unknown) {
    return this.request('GET', '/api/v1/ai/reference-ranges', body);
  }

  async post_ai_critical_results(body?: unknown) {
    return this.request('POST', '/api/v1/ai/critical-results', body);
  }

  async get_companies(body?: unknown) {
    return this.request('GET', '/api/v1/companies', body);
  }

  async post_companies(body?: unknown) {
    return this.request('POST', '/api/v1/companies', body);
  }

  async get_companies_company_id(body?: unknown) {
    return this.request('GET', '/api/v1/companies/<company_id>', body);
  }

  async put_companies_company_id(body?: unknown) {
    return this.request('PUT', '/api/v1/companies/<company_id>', body);
  }

  async delete_companies_company_id(body?: unknown) {
    return this.request('DELETE', '/api/v1/companies/<company_id>', body);
  }

  async get_marketplace_search(body?: unknown) {
    return this.request('GET', '/api/v1/marketplace/search', body);
  }

  async get_marketplace_bookings(body?: unknown) {
    return this.request('GET', '/api/v1/marketplace/bookings', body);
  }

  async post_marketplace_bookings(body?: unknown) {
    return this.request('POST', '/api/v1/marketplace/bookings', body);
  }

  async get_marketplace_bookings_booking_id(body?: unknown) {
    return this.request('GET', '/api/v1/marketplace/bookings/<booking_id>', body);
  }

  async post_marketplace_bookings_booking_id_transition(body?: unknown) {
    return this.request('POST', '/api/v1/marketplace/bookings/<booking_id>/transition', body);
  }

  async get_marketplace_bookings_booking_id_timeline(body?: unknown) {
    return this.request('GET', '/api/v1/marketplace/bookings/<booking_id>/timeline', body);
  }

  async get_partners(body?: unknown) {
    return this.request('GET', '/api/v1/partners', body);
  }

  async post_partners(body?: unknown) {
    return this.request('POST', '/api/v1/partners', body);
  }

}
