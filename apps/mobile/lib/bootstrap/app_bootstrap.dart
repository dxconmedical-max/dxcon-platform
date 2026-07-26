import 'package:hive_flutter/hive_flutter.dart';

import 'package:dxcon_mobile/core/offline/offline_read_cache.dart';
import 'package:dxcon_mobile/core/security/release_guards.dart';

/// Application bootstrap — Hive, notifications, Firebase foundation.
class AppBootstrap {
  static bool _initialized = false;

  static Future<void> initialize() async {
    if (_initialized) return;
    const ReleaseGuards().assertSafeForRelease();
    await Hive.initFlutter();
    await Hive.openBox<dynamic>('dxcon_sync_queue');
    await Hive.openBox<dynamic>(OfflineReadCache.boxName);
    // Firebase.initializeApp() — BLOCKED_BY_CONFIGURATION until platform config files exist.
    // Analytics / Sentry remain no-op until approved DSN / flags are provided via dart-define.
    _initialized = true;
  }
}
