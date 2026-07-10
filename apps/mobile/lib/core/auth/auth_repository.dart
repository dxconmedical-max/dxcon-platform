import 'package:dxcon_mobile/core/api/api_client.dart';
import 'package:dxcon_mobile/core/errors/api_error.dart';
import 'package:dxcon_mobile/core/storage/secure_token_storage.dart';
import 'package:dxcon_mobile/models/auth_models.dart';

/// Real authentication against production API v1 — no mock runtime auth.
class AuthRepository {
  AuthRepository({
    required ApiClient apiClient,
    required SecureTokenStorage secureStorage,
  }) : _api = apiClient,
       _storage = secureStorage;

  final ApiClient _api;
  final SecureTokenStorage _storage;

  Future<LoginResponse> login({
    required String email,
    required String password,
  }) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      body: {'email': email, 'password': password},
    );
    final login = LoginResponse.fromJson(response);
    if (!login.user.isActive) {
      throw const ApiError(
        message: 'Account is disabled',
        statusCode: 403,
        code: 'ACCOUNT_DISABLED',
      );
    }
    await _storage.saveTokens(
      accessToken: login.accessToken,
      refreshToken: login.refreshToken,
    );
    return login;
  }

  Future<void> logout() async {
    final refresh = await _storage.readRefreshToken();
    if (refresh != null && refresh.isNotEmpty) {
      try {
        await _api.post<void>(
          '/api/v1/auth/logout',
          body: {},
          bearerOverride: refresh,
          parser: (_) {},
        );
      } catch (_) {
        // Always clear local session even if remote logout fails.
      }
    }
    await _storage.clearAll();
  }

  Future<String?> refreshAccessToken() async {
    final refresh = await _storage.readRefreshToken();
    if (refresh == null || refresh.isEmpty) return null;
    final response = await _api.post<Map<String, dynamic>>(
      '/api/v1/auth/refresh',
      body: {},
    );
    final access = (response['access_token'] ?? response['token'])?.toString();
    if (access == null || access.isEmpty) return null;
    await _storage.saveTokens(accessToken: access, refreshToken: refresh);
    return access;
  }

  Future<MeResponse> fetchMe() async {
    final response = await _api.get<Map<String, dynamic>>(
      '/api/v1/auth/me',
      parser: (json) {
        if (json is Map<String, dynamic> && json['data'] != null) {
          return json['data'] as Map<String, dynamic>;
        }
        return json as Map<String, dynamic>;
      },
    );
    return MeResponse.fromJson(response);
  }

  Future<List<Membership>> fetchMemberships() async {
    final response = await _api.get<dynamic>(
      '/api/v1/auth/memberships',
      parser: (json) {
        if (json is Map<String, dynamic> && json['data'] != null) {
          return json['data'] as List<dynamic>;
        }
        return json as List<dynamic>;
      },
    );
    return response
        .map((e) => Membership.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AuthCapabilities> switchOrganization(String organizationId) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/api/v1/auth/switch-organization',
      body: {'organization_id': organizationId},
    );
    final data = response['data'] as Map<String, dynamic>? ?? response;
    final caps = AuthCapabilities.fromJson(data);
    if (caps.organization != null && !caps.organization!.isActive) {
      throw const ApiError(
        message: 'Organization is suspended',
        statusCode: 403,
        code: 'ORG_SUSPENDED',
      );
    }
    await _storage.saveActiveOrganization(organizationId);
    await _storage.saveWorkspace(caps.workspace);
    return caps;
  }

  Future<AuthCapabilities> fetchCapabilities({String? organizationId}) async {
    final query = organizationId != null
        ? '?organization_id=${Uri.encodeComponent(organizationId)}'
        : '';
    final response = await _api.get<Map<String, dynamic>>(
      '/api/v1/auth/capabilities$query',
      parser: (json) {
        if (json is Map<String, dynamic> && json['data'] != null) {
          return json['data'] as Map<String, dynamic>;
        }
        return json as Map<String, dynamic>;
      },
    );
    return AuthCapabilities.fromJson(response);
  }

  Future<bool> restoreSession() async {
    final access = await _storage.readAccessToken();
    final refresh = await _storage.readRefreshToken();
    return (access != null && access.isNotEmpty) ||
        (refresh != null && refresh.isNotEmpty);
  }
}
