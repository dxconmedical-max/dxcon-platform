import 'package:connectivity_plus/connectivity_plus.dart';

import 'package:dxcon_mobile/core/errors/api_error.dart';
import 'package:dxcon_mobile/core/offline/offline_read_cache.dart';
import 'package:dxcon_mobile/core/offline/offline_read_state.dart';

typedef OnlineFetcher = Future<Map<String, dynamic>> Function();
typedef OnlineChecker = Future<bool> Function();

Future<bool> defaultOnlineChecker([Connectivity? connectivity]) async {
  final results = await (connectivity ?? Connectivity()).checkConnectivity();
  if (results.isEmpty) return false;
  return results.any((r) => r != ConnectivityResult.none);
}

/// Performs a network read with offline-safe cache fallback.
class OfflineReader {
  OfflineReader({
    required OfflineReadCache cache,
    OnlineChecker? isOnline,
    Connectivity? connectivity,
  }) : _cache = cache,
       _isOnline = isOnline ?? (() => defaultOnlineChecker(connectivity));

  final OfflineReadCache _cache;
  final OnlineChecker _isOnline;

  Future<bool> get isOnline => _isOnline();

  Future<OfflineReadState<Map<String, dynamic>>> readJson({
    required String cacheKey,
    required OnlineFetcher fetcher,
    Duration? ttl,
    bool preferCacheWhenOffline = true,
  }) async {
    final online = await isOnline;
    if (!online && preferCacheWhenOffline) {
      final cached = _cache.getJson(cacheKey, allowExpired: true);
      if (cached != null) {
        return OfflineReadCached(
          cached.data,
          cachedAt: cached.cachedAt,
          freshness: cached.expired
              ? OfflineFreshness.stale
              : OfflineFreshness.cached,
        );
      }
      return const OfflineReadOfflineEmpty();
    }

    try {
      final data = await fetcher();
      await _cache.putJson(cacheKey, data, ttl: ttl);
      return OfflineReadSuccess(data, fetchedAt: DateTime.now().toUtc());
    } on ApiError catch (e) {
      if (e.isNetworkError || e.isTimeout || e.isServerError) {
        final cached = _cache.getJson(cacheKey, allowExpired: true);
        if (cached != null) {
          return OfflineReadCached(
            cached.data,
            cachedAt: cached.cachedAt,
            freshness: OfflineFreshness.stale,
            reason: e.code ?? 'NETWORK_ERROR',
          );
        }
        if (e.isNetworkError || e.isTimeout) {
          return OfflineReadOfflineEmpty(reason: e.code ?? 'NETWORK_ERROR');
        }
      }
      final cached = _cache.getJson(cacheKey, allowExpired: true);
      return OfflineReadError(
        e.message,
        code: e.code,
        cachedFallback: cached?.data,
      );
    } catch (e) {
      final cached = _cache.getJson(cacheKey, allowExpired: true);
      if (cached != null) {
        return OfflineReadCached(
          cached.data,
          cachedAt: cached.cachedAt,
          freshness: OfflineFreshness.stale,
          reason: 'UNEXPECTED_ERROR',
        );
      }
      return OfflineReadError(e.toString(), code: 'UNEXPECTED_ERROR');
    }
  }
}
