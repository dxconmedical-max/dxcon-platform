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

  async get_auth_me(body?: unknown) {
    return this.request('GET', '/api/v1/auth/me', body);
  }

  async get_auth_memberships(body?: unknown) {
    return this.request('GET', '/api/v1/auth/memberships', body);
  }

  async post_auth_switch_organization(body?: unknown) {
    return this.request('POST', '/api/v1/auth/switch-organization', body);
  }

  async get_auth_capabilities(body?: unknown) {
    return this.request('GET', '/api/v1/auth/capabilities', body);
  }

  async post_auth_forgot_password(body?: unknown) {
    return this.request('POST', '/api/v1/auth/forgot-password', body);
  }

  async post_auth_reset_password(body?: unknown) {
    return this.request('POST', '/api/v1/auth/reset-password', body);
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

  async get_reception_dashboard(body?: unknown) {
    return this.request('GET', '/api/v1/reception/dashboard', body);
  }

  async get_reception_search(body?: unknown) {
    return this.request('GET', '/api/v1/reception/search', body);
  }

  async post_reception_register_quick(body?: unknown) {
    return this.request('POST', '/api/v1/reception/register/quick', body);
  }

  async post_reception_register_walk_in(body?: unknown) {
    return this.request('POST', '/api/v1/reception/register/walk-in', body);
  }

  async post_reception_check_in(body?: unknown) {
    return this.request('POST', '/api/v1/reception/check-in', body);
  }

  async post_reception_queue_entry_id_check_in(body?: unknown) {
    return this.request('POST', '/api/v1/reception/queue/<entry_id>/check-in', body);
  }

  async post_reception_queue_entry_id_check_out(body?: unknown) {
    return this.request('POST', '/api/v1/reception/queue/<entry_id>/check-out', body);
  }

  async get_reception_activity(body?: unknown) {
    return this.request('GET', '/api/v1/reception/activity', body);
  }

  async get_reception_kpi(body?: unknown) {
    return this.request('GET', '/api/v1/reception/kpi', body);
  }

  async get_integration_hub_dashboard(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/dashboard', body);
  }

  async get_integration_hub_health(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/health', body);
  }

  async get_integration_hub_connectors(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/connectors', body);
  }

  async get_integration_hub_adapters(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/adapters', body);
  }

  async get_integration_hub_webhooks(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/webhooks', body);
  }

  async get_integration_hub_api_keys(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/api-keys', body);
  }

  async get_integration_hub_retry_queue(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/retry-queue', body);
  }

  async get_integration_hub_dead_letters(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/dead-letters', body);
  }

  async get_integration_hub_audit(body?: unknown) {
    return this.request('GET', '/api/v1/integration-hub/audit', body);
  }

  async post_integration_hub_sandbox_test(body?: unknown) {
    return this.request('POST', '/api/v1/integration-hub/sandbox/test', body);
  }

  async get_ai_clinical_assistant_policy(body?: unknown) {
    return this.request('GET', '/api/v1/ai-clinical/assistant/policy', body);
  }

  async post_ai_clinical_assistant_interpret(body?: unknown) {
    return this.request('POST', '/api/v1/ai-clinical/assistant/interpret', body);
  }

  async post_ai_clinical_assistant_critical_review(body?: unknown) {
    return this.request('POST', '/api/v1/ai-clinical/assistant/critical-review', body);
  }

  async get_ai_clinical_dashboard(body?: unknown) {
    return this.request('GET', '/api/v1/ai-clinical/dashboard', body);
  }

  async get_ai_clinical_providers(body?: unknown) {
    return this.request('GET', '/api/v1/ai-clinical/providers', body);
  }

}
