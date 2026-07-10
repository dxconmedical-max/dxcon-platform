import 'package:hive_flutter/hive_flutter.dart';

/// Application bootstrap — Hive, notifications, Firebase foundation.
class AppBootstrap {
  static bool _initialized = false;

  static Future<void> initialize() async {
    if (_initialized) return;
    await Hive.initFlutter();
    await Hive.openBox<dynamic>('dxcon_sync_queue');
    await Hive.openBox<dynamic>('dxcon_cache');
    // Firebase.initializeApp() — BLOCKED_BY_CONFIGURATION until platform config files exist.
    _initialized = true;
  }
}
