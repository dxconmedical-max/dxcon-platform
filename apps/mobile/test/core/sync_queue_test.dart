import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

import 'package:dxcon_mobile/core/sync/sync_queue.dart';

void main() {
  test('sync queue exponential backoff', () {
    final item = SyncQueueItem(
      localOperationId: '1',
      organizationId: 'org-1',
      resourceType: 'booking',
      operationType: 'create',
      payload: {},
      idempotencyKey: 'key',
      createdAt: _fixed,
      retryCount: 2,
    );
    expect(item.backoffDelay.inSeconds, 4);
  });

  test('permanent failure cancels retry', () {
    final queue = SyncQueue();
    queue.enqueue(
      SyncQueueItem(
        localOperationId: const Uuid().v4(),
        organizationId: 'org-1',
        resourceType: 'booking',
        operationType: 'create',
        payload: {'x': 1},
        idempotencyKey: 'key',
        createdAt: DateTime.now().toUtc(),
      ),
    );
    final id = queue.all.first.localOperationId;
    queue.markFailed(id, 'validation', permanent: true);
    expect(queue.all.first.status, SyncOperationStatus.cancelled);
  });

  test('clear cache on organization switch', () {
    final queue = SyncQueue();
    queue.enqueue(
      SyncQueueItem(
        localOperationId: 'a',
        organizationId: 'org-1',
        resourceType: 'x',
        operationType: 'create',
        payload: {},
        idempotencyKey: 'k',
        createdAt: DateTime.now().toUtc(),
      ),
    );
    queue.enqueue(
      SyncQueueItem(
        localOperationId: 'b',
        organizationId: 'org-2',
        resourceType: 'x',
        operationType: 'create',
        payload: {},
        idempotencyKey: 'k2',
        createdAt: DateTime.now().toUtc(),
      ),
    );
    queue.clearForOrganization('org-1');
    expect(queue.all.length, 1);
    expect(queue.all.first.organizationId, 'org-2');
  });
}

final _fixed = DateTime.utc(2026, 1, 1);
