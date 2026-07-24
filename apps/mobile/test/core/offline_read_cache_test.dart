import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';

import 'package:dxcon_mobile/core/errors/api_error.dart';
import 'package:dxcon_mobile/core/offline/offline_read_cache.dart';
import 'package:dxcon_mobile/core/offline/offline_read_state.dart';
import 'package:dxcon_mobile/core/offline/offline_reader.dart';

void main() {
  late Box<dynamic> box;
  late OfflineReadCache cache;

  setUp(() async {
    Hive.init('./.dart_tool/test_hive_offline');
    box = await Hive.openBox<dynamic>(
      'test_offline_cache_${DateTime.now().microsecondsSinceEpoch}',
    );
    cache = OfflineReadCache(box: box, defaultTtl: const Duration(hours: 1));
  });

  tearDown(() async {
    await box.clear();
    await box.close();
  });

  test('cache key never includes secrets', () {
    final key = OfflineReadCache.keyFor(
      resource: 'memberships',
      organizationId: 'org-1',
      query: {'page': '1'},
    );
    expect(key, 'memberships:org-1:page=1');
    expect(key.contains('token'), isFalse);
  });

  test('put and get json with TTL', () async {
    await cache.putJson('k1', {'hello': 'world'});
    final cached = cache.getJson('k1');
    expect(cached, isNotNull);
    expect(cached!.data['hello'], 'world');
    expect(cached.expired, isFalse);
  });

  test('offline reader returns cached payload on network error', () async {
    await cache.putJson('me', {'id': 'u1'});
    final reader = OfflineReader(cache: cache, isOnline: () async => true);
    final state = await reader.readJson(
      cacheKey: 'me',
      fetcher: () async {
        throw const ApiError(
          message: 'Network error',
          statusCode: 0,
          code: 'NETWORK_ERROR',
        );
      },
    );
    expect(state, isA<OfflineReadCached<Map<String, dynamic>>>());
    expect(state.dataOrNull?['id'], 'u1');
  });

  test('offline reader serves cache when offline', () async {
    await cache.putJson('caps', {'workspace': 'lab'});
    final reader = OfflineReader(cache: cache, isOnline: () async => false);
    final state = await reader.readJson(
      cacheKey: 'caps',
      fetcher: () async => throw StateError('should not fetch'),
    );
    expect(state, isA<OfflineReadCached<Map<String, dynamic>>>());
    expect(state.dataOrNull?['workspace'], 'lab');
  });

  test('offline reader success writes cache', () async {
    final reader = OfflineReader(cache: cache, isOnline: () async => true);
    final state = await reader.readJson(
      cacheKey: 'caps',
      fetcher: () async => {'workspace': 'doctor'},
    );
    expect(state, isA<OfflineReadSuccess<Map<String, dynamic>>>());
    expect(cache.getJson('caps')?.data['workspace'], 'doctor');
  });
}
