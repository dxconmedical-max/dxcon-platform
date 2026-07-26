import 'package:flutter/foundation.dart';

import 'package:dxcon_mobile/config/environment.dart';

/// Phase 1 release safety — no mocks / demo auth in release builds.
class ReleaseGuards {
  const ReleaseGuards();

  /// Call during bootstrap. Throws in release if unsafe config is present.
  void assertSafeForRelease({AppEnvironment? environment}) {
    final env = environment ?? AppEnvironment.current;
    if (kReleaseMode) {
      if (env.demoMode) {
        throw StateError(
          'DEMO_MODE must be false in release builds (Phase 1 guard)',
        );
      }
      if (env.apiBaseUrl.contains('localhost') ||
          env.apiBaseUrl.contains('127.0.0.1') ||
          env.apiBaseUrl.contains('0.0.0.0')) {
        throw StateError(
          'Release builds must not target localhost API (Phase 1 guard)',
        );
      }
      if (env.apiBaseUrl.trim().isEmpty) {
        throw StateError('API_BASE_URL is required in release builds');
      }
    }
  }

  bool get mocksAllowed => !kReleaseMode && AppEnvironment.current.demoMode;
}
