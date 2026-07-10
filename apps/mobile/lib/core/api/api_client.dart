import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

import 'package:dxcon_mobile/config/environment.dart';
import 'package:dxcon_mobile/core/errors/api_error.dart';
import 'package:dxcon_mobile/core/logging/safe_logger.dart';

typedef TokenProvider = String? Function();
typedef RefreshHandler = Future<String?> Function();

/// Typed HTTP client for frozen API v1.
class ApiClient {
  ApiClient({
    Dio? dio,
    this.tokenProvider,
    this.refreshHandler,
    this.organizationIdProvider,
    this.timeoutMs = 30000,
    SafeLogger? logger,
  }) : _logger = logger ?? const SafeLogger('ApiClient'),
       _dio =
           dio ??
           Dio(
             BaseOptions(
               baseUrl: AppEnvironment.current.apiBaseUrl,
               connectTimeout: Duration(milliseconds: timeoutMs),
               receiveTimeout: Duration(milliseconds: timeoutMs),
               headers: {
                 'Accept': 'application/json',
                 'Content-Type': 'application/json',
               },
             ),
           ) {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          if (!options.headers.containsKey('Authorization')) {
            final token = tokenProvider?.call();
            if (token != null && token.isNotEmpty) {
              options.headers['Authorization'] = 'Bearer $token';
            }
          }
          final orgId = organizationIdProvider?.call();
          if (orgId != null && orgId.isNotEmpty) {
            options.headers['X-Organization-ID'] = orgId;
          }
          options.headers['X-Correlation-ID'] ??= const Uuid().v4();
          handler.next(options);
        },
        onError: (error, handler) async {
          final status = error.response?.statusCode ?? 0;
          if (status == 401 && refreshHandler != null) {
            try {
              final newToken = await refreshHandler!();
              if (newToken != null && newToken.isNotEmpty) {
                final opts = error.requestOptions;
                opts.headers['Authorization'] = 'Bearer $newToken';
                final response = await _dio.fetch(opts);
                return handler.resolve(response);
              }
            } catch (_) {
              // fall through to normalized error
            }
          }
          handler.next(error);
        },
      ),
    );
  }

  final Dio _dio;
  final SafeLogger _logger;
  final int timeoutMs;
  final TokenProvider? tokenProvider;
  final RefreshHandler? refreshHandler;
  final String? Function()? organizationIdProvider;

  Future<T> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    T Function(dynamic json)? parser,
  }) => _request('GET', path, queryParameters: queryParameters, parser: parser);

  Future<T> post<T>(
    String path, {
    Object? body,
    Map<String, dynamic>? queryParameters,
    String? idempotencyKey,
    String? bearerOverride,
    T Function(dynamic json)? parser,
  }) => _request(
    'POST',
    path,
    data: body,
    queryParameters: queryParameters,
    idempotencyKey: idempotencyKey,
    bearerOverride: bearerOverride,
    parser: parser,
  );

  Future<T> put<T>(
    String path, {
    Object? body,
    String? idempotencyKey,
    T Function(dynamic json)? parser,
  }) => _request(
    'PUT',
    path,
    data: body,
    idempotencyKey: idempotencyKey,
    parser: parser,
  );

  Future<T> delete<T>(String path, {T Function(dynamic json)? parser}) =>
      _request('DELETE', path, parser: parser);

  Future<T> _request<T>(
    String method,
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    String? idempotencyKey,
    String? bearerOverride,
    T Function(dynamic json)? parser,
  }) async {
    try {
      final headers = <String, dynamic>{};
      if (bearerOverride != null) {
        headers['Authorization'] = 'Bearer $bearerOverride';
      }
      if (idempotencyKey != null) {
        headers['Idempotency-Key'] = idempotencyKey;
      }
      final response = await _dio.request<dynamic>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: Options(method: method, headers: headers),
      );
      final payload = response.data;
      if (parser != null) {
        return parser(payload);
      }
      return payload as T;
    } on DioException catch (e) {
      throw _normalizeError(e);
    }
  }

  ApiError _normalizeError(DioException error) {
    final response = error.response;
    final status = response?.statusCode ?? 0;
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return const ApiError(
        message: 'Request timed out',
        statusCode: 408,
        code: 'TIMEOUT',
      );
    }
    if (error.type == DioExceptionType.connectionError) {
      return const ApiError(
        message: 'Network error — check your connection',
        statusCode: 0,
        code: 'NETWORK_ERROR',
      );
    }
    final data = response?.data;
    String message = 'Request failed ($status)';
    String? code;
    Map<String, dynamic>? details;
    int? retryAfter;
    if (data is Map<String, dynamic>) {
      message =
          data['error']?.toString() ?? data['message']?.toString() ?? message;
      code = data['code']?.toString();
      details = data;
    }
    final retryHeader = response?.headers.value('retry-after');
    if (retryHeader != null) {
      retryAfter = int.tryParse(retryHeader);
    }
    _logger.warn('API error $status $code');
    return ApiError(
      message: message,
      statusCode: status,
      code: code,
      details: details,
      retryAfter: retryAfter,
    );
  }
}
