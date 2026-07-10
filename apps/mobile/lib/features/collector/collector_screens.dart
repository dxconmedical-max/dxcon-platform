import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:dxcon_mobile/core/auth/auth_provider.dart';
import 'package:dxcon_mobile/core/api/api_client.dart';
import 'package:dxcon_mobile/design_system/components.dart';
import 'package:dxcon_mobile/features/patient/patient_home_screen.dart';
import 'package:dxcon_mobile/services/collector_api_repository.dart';

final collectorApiProvider = Provider<CollectorApiRepository>((ref) {
  return CollectorApiRepository(ref.watch(apiClientProvider));
});

class CollectorHomeScreen extends ConsumerStatefulWidget {
  const CollectorHomeScreen({super.key, required this.collectorId});
  final String collectorId;

  @override
  ConsumerState<CollectorHomeScreen> createState() => _CollectorHomeScreenState();
}

class _CollectorHomeScreenState extends ConsumerState<CollectorHomeScreen> {
  Map<String, dynamic>? _data;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await ref.read(collectorApiProvider).dashboard(widget.collectorId);
      setState(() {
        _data = data;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) return DxErrorState(message: _error!, onRetry: _load);
    if (_data == null) return const DxLoadingState();
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Hôm nay: ${_data!['today_jobs_count'] ?? 0} công việc'),
          ListTile(
            title: const Text('Đồng bộ'),
            subtitle: Text(_data!['sync_status']?.toString() ?? 'unknown'),
            trailing: TextButton(
              onPressed: () => context.go('/collector/sync'),
              child: const Text('Chi tiết'),
            ),
          ),
          if (_data!['active_job'] != null)
            Card(child: ListTile(title: const Text('Công việc đang hoạt động'))),
        ],
      ),
    );
  }
}

class CollectorJobsScreen extends ConsumerStatefulWidget {
  const CollectorJobsScreen({super.key, required this.collectorId});
  final String collectorId;

  @override
  ConsumerState<CollectorJobsScreen> createState() => _CollectorJobsScreenState();
}

class _CollectorJobsScreenState extends ConsumerState<CollectorJobsScreen> {
  List<dynamic> _jobs = [];
  String? _error;
  String? _filter;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final jobs = await ref.read(collectorApiProvider).jobs(widget.collectorId, status: _filter);
      setState(() {
        _jobs = jobs;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.all(8),
          child: Row(
            children: [
              FilterChip(label: const Text('Tất cả'), selected: _filter == null, onSelected: (_) { setState(() => _filter = null); _load(); }),
              FilterChip(label: const Text('Hôm nay'), selected: _filter == 'ASSIGNED', onSelected: (_) { setState(() => _filter = 'ASSIGNED'); _load(); }),
            ],
          ),
        ),
        if (_error != null) Expanded(child: DxErrorState(message: _error!, onRetry: _load)),
        if (_error == null)
          Expanded(
            child: _jobs.isEmpty
                ? const DxEmptyState(title: 'Không có công việc')
                : ListView.builder(
                    itemCount: _jobs.length,
                    itemBuilder: (context, i) {
                      final job = _jobs[i] as Map<String, dynamic>;
                      final assignment = job['assignment'] as Map<String, dynamic>? ?? {};
                      final booking = job['booking'] as Map<String, dynamic>? ?? {};
                      return ListTile(
                        title: Text(booking['patient_name']?.toString() ?? booking['booking_code']?.toString() ?? 'Công việc'),
                        subtitle: Text(assignment['assignment_status']?.toString() ?? ''),
                        onTap: () => context.go('/collector/job/${assignment['id']}'),
                      );
                    },
                  ),
          ),
      ],
    );
  }
}

class CollectorJobDetailScreen extends ConsumerWidget {
  const CollectorJobDetailScreen({super.key, required this.collectorId, required this.assignmentId});
  final String collectorId;
  final String assignmentId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder<Map<String, dynamic>>(
      future: ref.read(collectorApiProvider).jobDetail(collectorId, assignmentId),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const DxLoadingState();
        if (snapshot.hasError) return DxErrorState(message: snapshot.error.toString());
        final job = snapshot.data!;
        final assignment = job['assignment'] as Map<String, dynamic>? ?? {};
        final booking = job['booking'] as Map<String, dynamic>? ?? {};
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Mã: ${booking['booking_code'] ?? booking['id']}', style: Theme.of(context).textTheme.titleLarge),
            ListTile(title: const Text('Địa chỉ lấy mẫu'), subtitle: Text(booking['pickup_address']?.toString() ?? '—')),
            Row(
              children: [
                ElevatedButton(
                  onPressed: () async {
                    await ref.read(collectorApiProvider).acceptAssignment(assignmentId, collectorId);
                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Đã chấp nhận')));
                  },
                  child: const Text('Chấp nhận'),
                ),
                const SizedBox(width: 8),
                OutlinedButton(
                  onPressed: () async {
                    await ref.read(collectorApiProvider).rejectAssignment(collectorId, assignmentId, 'Không khả dụng');
                    if (context.mounted) Navigator.of(context).pop();
                  },
                  child: const Text('Từ chối'),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}

class CollectorSyncScreen extends ConsumerWidget {
  const CollectorSyncScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return const DxEmptyState(
      title: 'Trung tâm đồng bộ',
      subtitle: 'Các thao tác ngoại tuyến sẽ hiển thị tại đây',
      icon: Icons.sync,
    );
  }
}
