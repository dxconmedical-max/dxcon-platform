import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Minimal key-value backend used by [SecureTokenStorage].
abstract class SecureStoreBackend {
  Future<void> write({required String key, required String? value});
  Future<String?> read({required String key});
  Future<void> deleteAll();
}

class FlutterSecureStoreBackend implements SecureStoreBackend {
  FlutterSecureStoreBackend({FlutterSecureStorage? storage})
    : _storage =
          storage ??
          const FlutterSecureStorage(
            aOptions: AndroidOptions(encryptedSharedPreferences: true),
            iOptions: IOSOptions(
              accessibility: KeychainAccessibility.first_unlock,
            ),
          );

  final FlutterSecureStorage _storage;

  @override
  Future<void> write({required String key, required String? value}) =>
      _storage.write(key: key, value: value);

  @override
  Future<String?> read({required String key}) => _storage.read(key: key);

  @override
  Future<void> deleteAll() => _storage.deleteAll();
}

/// In-memory backend for unit tests (never used in release).
class MemorySecureStoreBackend implements SecureStoreBackend {
  final Map<String, String> _data = {};

  @override
  Future<void> write({required String key, required String? value}) async {
    if (value == null) {
      _data.remove(key);
    } else {
      _data[key] = value;
    }
  }

  @override
  Future<String?> read({required String key}) async => _data[key];

  @override
  Future<void> deleteAll() async => _data.clear();
}

/// Platform secure storage for tokens and minimal context identifiers.
class SecureTokenStorage {
  SecureTokenStorage({SecureStoreBackend? backend})
    : _backend = backend ?? FlutterSecureStoreBackend();

  static const _accessTokenKey = 'dxcon_access_token';
  static const _refreshTokenKey = 'dxcon_refresh_token';
  static const _tokenExpiryKey = 'dxcon_token_expiry';
  static const _organizationIdKey = 'dxcon_active_org_id';
  static const _workspaceKey = 'dxcon_active_workspace';

  final SecureStoreBackend _backend;

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    String? expiresAt,
  }) async {
    await _backend.write(key: _accessTokenKey, value: accessToken);
    await _backend.write(key: _refreshTokenKey, value: refreshToken);
    if (expiresAt != null) {
      await _backend.write(key: _tokenExpiryKey, value: expiresAt);
    }
  }

  Future<String?> readAccessToken() => _backend.read(key: _accessTokenKey);

  Future<String?> readRefreshToken() => _backend.read(key: _refreshTokenKey);

  Future<String?> readTokenExpiry() => _backend.read(key: _tokenExpiryKey);

  Future<void> saveActiveOrganization(String organizationId) =>
      _backend.write(key: _organizationIdKey, value: organizationId);

  Future<String?> readActiveOrganization() =>
      _backend.read(key: _organizationIdKey);

  Future<void> saveWorkspace(String workspace) =>
      _backend.write(key: _workspaceKey, value: workspace);

  Future<String?> readWorkspace() => _backend.read(key: _workspaceKey);

  Future<void> clearAll() => _backend.deleteAll();
}
