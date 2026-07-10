import 'dart:developer' as developer;

/// Logs safe diagnostic messages — never tokens, passwords, or PHI.
class SafeLogger {
  const SafeLogger(this.tag);

  final String tag;

  void debug(String message, {Map<String, Object?>? context}) {
    developer.log(_sanitize(message), name: tag, error: context);
  }

  void info(String message) {
    developer.log(_sanitize(message), name: tag);
  }

  void warn(String message) {
    developer.log('[WARN] ${_sanitize(message)}', name: tag);
  }

  void error(String message, {Object? error}) {
    developer.log('[ERROR] ${_sanitize(message)}', name: tag, error: error);
  }

  static String _sanitize(String input) {
    return input
        .replaceAll(
          RegExp(r'Bearer\s+\S+', caseSensitive: false),
          'Bearer [REDACTED]',
        )
        .replaceAll(
          RegExp(r'"password"\s*:\s*"[^"]*"'),
          '"password":"[REDACTED]"',
        )
        .replaceAll(
          RegExp(r'"access_token"\s*:\s*"[^"]*"'),
          '"access_token":"[REDACTED]"',
        )
        .replaceAll(
          RegExp(r'"refresh_token"\s*:\s*"[^"]*"'),
          '"refresh_token":"[REDACTED]"',
        );
  }
}
