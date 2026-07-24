import 'dart:convert';

import 'package:hive/hive.dart';

/// TTL-backed JSON cache for offline-safe reads (no secrets / tokens).
class OfflineReadCache {
  OfflineReadCache({
    Box<dynamic>? box,
    this.defaultTtl = const Duration(hours: 6),
  }) : _box = box;

  static const boxName = 'dxcon_cache';

  final Box<dynamic>? _box;
  final Duration defaultTtl;

  Box<dynamic> get _cache {
    final box = _box;
    if (box != null) return box;
    return Hive.box<dynamic>(boxName);
  }

  Future<void> putJson(
    String key,
    Map<String, dynamic> value, {
    Duration? ttl,
  }) async {
    final expiresAt = DateTime.now().toUtc().add(ttl ?? defaultTtl);
    await _cache.put(key, {
      'payload': value,
      'cached_at': DateTime.now().toUtc().toIso8601String(),
      'expires_at': expiresAt.toIso8601String(),
    });
  }

  CachedPayload? getJson(String key, {bool allowExpired = true}) {
    final raw = _cache.get(key);
    if (raw is! Map) return null;
    final map = Map<String, dynamic>.from(raw);
    final payload = map['payload'];
    if (payload is! Map) return null;
    final cachedAt =
        DateTime.tryParse(map['cached_at']?.toString() ?? '') ??
        DateTime.fromMillisecondsSinceEpoch(0, isUtc: true);
    final expiresAt =
        DateTime.tryParse(map['expires_at']?.toString() ?? '') ?? cachedAt;
    final expired = DateTime.now().toUtc().isAfter(expiresAt);
    if (expired && !allowExpired) return null;
    return CachedPayload(
      data: Map<String, dynamic>.from(payload),
      cachedAt: cachedAt,
      expired: expired,
    );
  }

  Future<void> putList(
    String key,
    List<Map<String, dynamic>> value, {
    Duration? ttl,
  }) async {
    await putJson(key, {'items': value}, ttl: ttl);
  }

  List<Map<String, dynamic>>? getList(String key, {bool allowExpired = true}) {
    final cached = getJson(key, allowExpired: allowExpired);
    if (cached == null) return null;
    final items = cached.data['items'];
    if (items is! List) return null;
    return items
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList();
  }

  Future<void> invalidate(String key) => _cache.delete(key);

  Future<void> invalidatePrefix(String prefix) async {
    final keys = _cache.keys
        .where((k) => k.toString().startsWith(prefix))
        .toList();
    for (final key in keys) {
      await _cache.delete(key);
    }
  }

  Future<void> clearAll() => _cache.clear();

  /// Stable cache key — never include tokens or passwords.
  static String keyFor({
    required String resource,
    String? organizationId,
    String? id,
    Map<String, String>? query,
  }) {
    final parts = <String>[
      resource,
      if (organizationId != null && organizationId.isNotEmpty) organizationId,
      if (id != null && id.isNotEmpty) id,
    ];
    if (query != null && query.isNotEmpty) {
      final sorted = query.entries.toList()
        ..sort((a, b) => a.key.compareTo(b.key));
      parts.add(sorted.map((e) => '${e.key}=${e.value}').join('&'));
    }
    return parts.join(':');
  }

  /// Encode arbitrary JSON-compatible value for debugging/tests.
  static String encode(Object? value) => jsonEncode(value);
}

class CachedPayload {
  const CachedPayload({
    required this.data,
    required this.cachedAt,
    required this.expired,
  });

  final Map<String, dynamic> data;
  final DateTime cachedAt;
  final bool expired;
}
