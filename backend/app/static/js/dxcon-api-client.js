/**
 * DxCon production web API client — Sprint 011.
 * Reads API_BASE_URL from window.__DXCON_CONFIG__ (injected by Flask templates).
 */
(function (global) {
  "use strict";

  const STORAGE_ACCESS = "dxcon_access_token";
  const STORAGE_REFRESH = "dxcon_refresh_token";

  function config() {
    return global.__DXCON_CONFIG__ || {};
  }

  function apiBaseUrl() {
    const cfg = config();
    if (cfg.apiBaseUrl) return cfg.apiBaseUrl.replace(/\/$/, "");
    if (global.location && global.location.origin) return global.location.origin;
    return "";
  }

  function getAccessToken() {
    try {
      return sessionStorage.getItem(STORAGE_ACCESS) || localStorage.getItem(STORAGE_ACCESS) || "";
    } catch (_e) {
      return "";
    }
  }

  function setTokens(access, refresh, remember) {
    const store = remember ? localStorage : sessionStorage;
    try {
      if (access) store.setItem(STORAGE_ACCESS, access);
      if (refresh) store.setItem(STORAGE_REFRESH, refresh);
    } catch (_e) {
      /* ignore quota errors */
    }
  }

  function clearTokens() {
    try {
      sessionStorage.removeItem(STORAGE_ACCESS);
      sessionStorage.removeItem(STORAGE_REFRESH);
      localStorage.removeItem(STORAGE_ACCESS);
      localStorage.removeItem(STORAGE_REFRESH);
    } catch (_e) {
      /* ignore */
    }
  }

  function normalizeError(status, payload) {
    if (payload && payload.error) {
      if (typeof payload.error === "string") return payload.error;
      if (payload.error.message) return payload.error.message;
      if (payload.error.code) return payload.error.code;
    }
    if (payload && payload.message) return payload.message;
    return status ? "HTTP " + status : "Network error";
  }

  async function request(path, options) {
    options = options || {};
    const url = apiBaseUrl() + path;
    const headers = Object.assign({"Content-Type": "application/json"}, options.headers || {});
    const token = getAccessToken();
    if (token) headers.Authorization = "Bearer " + token;

    let response;
    try {
      response = await fetch(url, Object.assign({}, options, {headers: headers}));
    } catch (err) {
      return {ok: false, status: 0, error: err.message || "Network error", data: null};
    }

    let payload = null;
    const text = await response.text();
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (_e) {
        payload = {raw: text};
      }
    }

    if (response.status === 401) {
      clearTokens();
      if (global.location && !global.location.pathname.startsWith("/login")) {
        global.location.href = "/login?expired=1";
      }
      return {ok: false, status: 401, error: "Session expired", data: payload};
    }

    const ok = response.ok;
    return {
      ok: ok,
      status: response.status,
      error: ok ? null : normalizeError(response.status, payload),
      data: payload,
    };
  }

  async function login(email, password, remember) {
    const result = await request("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({email: email, password: password}),
    });
    if (result.ok && result.data) {
      const access = result.data.access_token || result.data.token;
      const refresh = result.data.refresh_token;
      if (access) setTokens(access, refresh, remember);
    }
    return result;
  }

  async function healthCheck() {
    return request("/health", {method: "GET"});
  }

  async function logout() {
    clearTokens();
    if (global.location) global.location.href = "/logout";
  }

  global.DxConApiClient = {
    apiBaseUrl: apiBaseUrl,
    getAccessToken: getAccessToken,
    setTokens: setTokens,
    clearTokens: clearTokens,
    request: request,
    login: login,
    healthCheck: healthCheck,
    logout: logout,
  };
})(typeof window !== "undefined" ? window : globalThis);
