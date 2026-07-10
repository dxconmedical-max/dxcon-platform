import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:dxcon_mobile/core/api/api_client.dart';
import 'package:dxcon_mobile/core/errors/api_error.dart';

void main() {
  test('normalizes 422 validation error', () async {
    final dio = Dio();
    dio.httpClientAdapter = _MockAdapter(
      statusCode: 422,
      body: {'error': 'Validation failed', 'code': 'VALIDATION_ERROR'},
    );
    final client = ApiClient(dio: dio);
    try {
      await client.get('/test');
      fail('expected ApiError');
    } on ApiError catch (e) {
      expect(e.isValidation, isTrue);
      expect(e.code, 'VALIDATION_ERROR');
    }
  });

  test('normalizes network error', () async {
    final dio = Dio();
    dio.httpClientAdapter = _ThrowingAdapter();
    final client = ApiClient(dio: dio);
    try {
      await client.get('/test');
      fail('expected ApiError');
    } on ApiError catch (e) {
      expect(e.isNetworkError, isTrue);
    }
  });

  test('attaches idempotency key header', () async {
    String? capturedKey;
    final dio = Dio();
    dio.httpClientAdapter = _HeaderCaptureAdapter(
      onRequest: (options) {
        capturedKey = options.headers['Idempotency-Key']?.toString();
      },
    );
    final client = ApiClient(dio: dio);
    await client.post('/test', body: {}, idempotencyKey: 'idem-123');
    expect(capturedKey, 'idem-123');
  });
}

class _MockAdapter implements HttpClientAdapter {
  _MockAdapter({required this.statusCode, required this.body});
  final int statusCode;
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
      '{"error":"${body['error']}","code":"${body['code']}"}',
      statusCode,
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

class _HeaderCaptureAdapter implements HttpClientAdapter {
  _HeaderCaptureAdapter({required this.onRequest});
  final void Function(RequestOptions options) onRequest;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<List<int>>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    onRequest(options);
    return ResponseBody.fromString('{}', 200);
  }
}
