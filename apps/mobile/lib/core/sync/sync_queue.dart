import 'package:equatable/equatable.dart';

enum SyncOperationStatus {
  pending,
  syncing,
  succeeded,
  failed,
  conflict,
  cancelled,
}

class SyncQueueItem extends Equatable {
  const SyncQueueItem({
    required this.localOperationId,
    required this.organizationId,
    required this.resourceType,
    required this.operationType,
    required this.payload,
    required this.idempotencyKey,
    required this.createdAt,
    this.retryCount = 0,
    this.lastError,
    this.status = SyncOperationStatus.pending,
    this.nextRetryAt,
  });

  final String localOperationId;
  final String organizationId;
  final String resourceType;
  final String operationType;
  final Map<String, dynamic> payload;
  final String idempotencyKey;
  final DateTime createdAt;
  final int retryCount;
  final String? lastError;
  final SyncOperationStatus status;
  final DateTime? nextRetryAt;

  static const maxRetries = 5;

  bool get canRetry =>
      status == SyncOperationStatus.failed && retryCount < maxRetries;

  Duration get backoffDelay =>
      Duration(seconds: (1 << retryCount.clamp(0, 6)).clamp(1, 300));

  SyncQueueItem copyWith({
    SyncOperationStatus? status,
    int? retryCount,
    String? lastError,
    DateTime? nextRetryAt,
  }) {
    return SyncQueueItem(
      localOperationId: localOperationId,
      organizationId: organizationId,
      resourceType: resourceType,
      operationType: operationType,
      payload: payload,
      idempotencyKey: idempotencyKey,
      createdAt: createdAt,
      retryCount: retryCount ?? this.retryCount,
      lastError: lastError ?? this.lastError,
      status: status ?? this.status,
      nextRetryAt: nextRetryAt ?? this.nextRetryAt,
    );
  }

  Map<String, dynamic> toJson() => {
    'local_operation_id': localOperationId,
    'organization_id': organizationId,
    'resource_type': resourceType,
    'operation_type': operationType,
    'payload': payload,
    'idempotency_key': idempotencyKey,
    'created_at': createdAt.toIso8601String(),
    'retry_count': retryCount,
    'last_error': lastError,
    'status': status.name.toUpperCase(),
    'next_retry_at': nextRetryAt?.toIso8601String(),
  };

  factory SyncQueueItem.fromJson(Map<String, dynamic> json) => SyncQueueItem(
    localOperationId: json['local_operation_id']?.toString() ?? '',
    organizationId: json['organization_id']?.toString() ?? '',
    resourceType: json['resource_type']?.toString() ?? '',
    operationType: json['operation_type']?.toString() ?? '',
    payload: Map<String, dynamic>.from(json['payload'] as Map? ?? {}),
    idempotencyKey: json['idempotency_key']?.toString() ?? '',
    createdAt:
        DateTime.tryParse(json['created_at']?.toString() ?? '') ??
        DateTime.now().toUtc(),
    retryCount: json['retry_count'] as int? ?? 0,
    lastError: json['last_error']?.toString(),
    status: SyncOperationStatus.values.firstWhere(
      (s) => s.name == (json['status']?.toString().toLowerCase() ?? 'pending'),
      orElse: () => SyncOperationStatus.pending,
    ),
    nextRetryAt: json['next_retry_at'] != null
        ? DateTime.tryParse(json['next_retry_at'].toString())
        : null,
  );

  @override
  List<Object?> get props => [
    localOperationId,
    organizationId,
    resourceType,
    operationType,
    payload,
    idempotencyKey,
    createdAt,
    retryCount,
    lastError,
    status,
    nextRetryAt,
  ];
}

/// In-memory sync queue with exponential backoff — persisted via Hive in production bootstrap.
class SyncQueue {
  final List<SyncQueueItem> _items = [];

  List<SyncQueueItem> get pendingItems => List.unmodifiable(
    _items.where(
      (i) =>
          i.status == SyncOperationStatus.pending ||
          (i.status == SyncOperationStatus.failed && i.canRetry),
    ),
  );

  List<SyncQueueItem> get all => List.unmodifiable(_items);

  void enqueue(SyncQueueItem item) => _items.add(item);

  void markSyncing(String id) => _update(id, SyncOperationStatus.syncing);

  void markSucceeded(String id) => _update(id, SyncOperationStatus.succeeded);

  void markFailed(String id, String error, {bool permanent = false}) {
    final index = _items.indexWhere((i) => i.localOperationId == id);
    if (index < 0) return;
    final item = _items[index];
    final nextRetry = permanent
        ? null
        : DateTime.now().toUtc().add(item.backoffDelay);
    _items[index] = item.copyWith(
      status: permanent
          ? SyncOperationStatus.cancelled
          : SyncOperationStatus.failed,
      retryCount: item.retryCount + 1,
      lastError: error,
      nextRetryAt: nextRetry,
    );
  }

  void markConflict(String id, String error) {
    final index = _items.indexWhere((i) => i.localOperationId == id);
    if (index < 0) return;
    _items[index] = _items[index].copyWith(
      status: SyncOperationStatus.conflict,
      lastError: error,
    );
  }

  void clearForOrganization(String organizationId) {
    _items.removeWhere((i) => i.organizationId == organizationId);
  }

  void clearAll() => _items.clear();

  void _update(String id, SyncOperationStatus status) {
    final index = _items.indexWhere((i) => i.localOperationId == id);
    if (index < 0) return;
    _items[index] = _items[index].copyWith(status: status);
  }
}
