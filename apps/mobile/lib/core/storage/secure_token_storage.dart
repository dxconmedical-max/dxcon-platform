import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Platform secure storage for tokens and minimal context identifiers.
class SecureTokenStorage {
  SecureTokenStorage({FlutterSecureStorage? storage})
    : _storage =
          storage ??
          const FlutterSecureStorage(
            aOptions: AndroidOptions(encryptedSharedPreferences: true),
            iOptions: IOSOptions(
              accessibility: KeychainAccessibility.first_unlock,
            ),
          );

  static const _accessTokenKey = 'dxcon_access_token';
  static const _refreshTokenKey = 'dxcon_refresh_token';
  static const _tokenExpiryKey = 'dxcon_token_expiry';
  static const _organizationIdKey = 'dxcon_active_org_id';
  static const _workspaceKey = 'dxcon_active_workspace';

  final FlutterSecureStorage _storage;

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    String? expiresAt,
  }) async {
    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
    if (expiresAt != null) {
      await _storage.write(key: _tokenExpiryKey, value: expiresAt);
    }
  }

  Future<String?> readAccessToken() => _storage.read(key: _accessTokenKey);

  Future<String?> readRefreshToken() => _storage.read(key: _refreshTokenKey);

  Future<String?> readTokenExpiry() => _storage.read(key: _tokenExpiryKey);

  Future<void> saveActiveOrganization(String organizationId) =>
      _storage.write(key: _organizationIdKey, value: organizationId);

  Future<String?> readActiveOrganization() =>
      _storage.read(key: _organizationIdKey);

  Future<void> saveWorkspace(String workspace) =>
      _storage.write(key: _workspaceKey, value: workspace);

  Future<String?> readWorkspace() => _storage.read(key: _workspaceKey);

  Future<void> clearAll() => _storage.deleteAll();
}
