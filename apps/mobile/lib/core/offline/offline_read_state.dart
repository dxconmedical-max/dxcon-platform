import 'package:equatable/equatable.dart';

/// Offline-safe read status for Phase 1 network reads.
enum OfflineFreshness { live, cached, stale }

/// Result wrapper for reads that may serve cached data when offline.
sealed class OfflineReadState<T> extends Equatable {
  const OfflineReadState();

  bool get isLoading => this is OfflineReadLoading<T>;
  bool get hasData =>
      this is OfflineReadSuccess<T> || this is OfflineReadCached<T>;
  bool get isOffline =>
      this is OfflineReadCached<T> || this is OfflineReadOfflineEmpty<T>;

  T? get dataOrNull => switch (this) {
    OfflineReadSuccess<T>(:final data) => data,
    OfflineReadCached<T>(:final data) => data,
    _ => null,
  };

  @override
  List<Object?> get props => [];
}

class OfflineReadLoading<T> extends OfflineReadState<T> {
  const OfflineReadLoading();
}

class OfflineReadSuccess<T> extends OfflineReadState<T> {
  const OfflineReadSuccess(this.data, {this.fetchedAt});

  final T data;
  final DateTime? fetchedAt;

  @override
  List<Object?> get props => [data, fetchedAt];
}

class OfflineReadCached<T> extends OfflineReadState<T> {
  const OfflineReadCached(
    this.data, {
    required this.cachedAt,
    this.freshness = OfflineFreshness.cached,
    this.reason = 'NETWORK_UNAVAILABLE',
  });

  final T data;
  final DateTime cachedAt;
  final OfflineFreshness freshness;
  final String reason;

  @override
  List<Object?> get props => [data, cachedAt, freshness, reason];
}

class OfflineReadOfflineEmpty<T> extends OfflineReadState<T> {
  const OfflineReadOfflineEmpty({this.reason = 'NETWORK_UNAVAILABLE'});

  final String reason;

  @override
  List<Object?> get props => [reason];
}

class OfflineReadError<T> extends OfflineReadState<T> {
  const OfflineReadError(this.message, {this.code, this.cachedFallback});

  final String message;
  final String? code;
  final T? cachedFallback;

  @override
  List<Object?> get props => [message, code, cachedFallback];
}
