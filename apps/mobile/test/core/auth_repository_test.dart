import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:dxcon_mobile/core/api/api_client.dart';
import 'package:dxcon_mobile/core/auth/auth_repository.dart';
import 'package:dxcon_mobile/core/storage/secure_token_storage.dart';

void main() {
  test('login persists tokens in secure storage', () async {
    final storage = SecureTokenStorage(backend: MemorySecureStoreBackend());
    final dio = Dio();
    dio.httpClientAdapter = _JsonAdapter({
      'access_token': 'access-1',
      'refresh_token': 'refresh-1',
      'user': {
        'id': 'u1',
        'email': 'user@dxcon.com',
        'role': 'doctor',
        'is_active': true,
      },
    });
    final repo = AuthRepository(
      apiClient: ApiClient(dio: dio),
      secureStorage: storage,
    );

    final login = await repo.login(email: 'user@dxcon.com', password: 'secret');
    expect(login.accessToken, 'access-1');
    expect(await storage.readAccessToken(), 'access-1');
    expect(await storage.readRefreshToken(), 'refresh-1');
  });

  test('logout clears secure storage even if remote fails', () async {
    final storage = SecureTokenStorage(backend: MemorySecureStoreBackend());
    await storage.saveTokens(
      accessToken: 'access-1',
      refreshToken: 'refresh-1',
    );
    final dio = Dio();
    dio.httpClientAdapter = _ThrowingAdapter();
    final repo = AuthRepository(
      apiClient: ApiClient(dio: dio),
      secureStorage: storage,
    );

    await repo.logout();
    expect(await storage.readAccessToken(), isNull);
    expect(await storage.readRefreshToken(), isNull);
  });
}

class _JsonAdapter implements HttpClientAdapter {
  _JsonAdapter(this.body);
  final Map<String, dynamic> body;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<List<int>>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    return ResponseBody.fromString(
      jsonEncode(body),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }
}

class _ThrowingAdapter implements HttpClientAdapter {
  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<List<int>>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    throw DioException.connectionError(
      requestOptions: options,
      reason: 'offline',
    );
  }
}
