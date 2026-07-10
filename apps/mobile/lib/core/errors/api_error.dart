import 'package:equatable/equatable.dart';

/// Normalized API error aligned with frozen ERROR_CONTRACT.
class ApiError extends Equatable implements Exception {
  const ApiError({
    required this.message,
    required this.statusCode,
    this.code,
    this.details,
    this.retryAfter,
  });

  final String message;
  final int statusCode;
  final String? code;
  final Map<String, dynamic>? details;
  final int? retryAfter;

  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get isNotFound => statusCode == 404;
  bool get isValidation => statusCode == 422;
  bool get isRateLimited => statusCode == 429;
  bool get isServerError => statusCode >= 500;
  bool get isNetworkError => statusCode == 0;
  bool get isTimeout => code == 'TIMEOUT';

  @override
  List<Object?> get props => [message, statusCode, code, details, retryAfter];

  @override
  String toString() => 'ApiError($statusCode, $code, $message)';
}
