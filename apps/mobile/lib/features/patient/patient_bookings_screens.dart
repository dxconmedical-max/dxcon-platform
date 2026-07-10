import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:dxcon_mobile/design_system/components.dart';
import 'package:dxcon_mobile/features/patient/patient_home_screen.dart';

class PatientBookingsScreen extends ConsumerStatefulWidget {
  const PatientBookingsScreen({super.key});

  @override
  ConsumerState<PatientBookingsScreen> createState() => _PatientBookingsScreenState();
}

class _PatientBookingsScreenState extends ConsumerState<PatientBookingsScreen> {
  List<dynamic> _bookings = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final res = await ref.read(patientApiProvider).bookings();
      setState(() {
        _bookings = res;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) return DxErrorState(message: _error!, onRetry: _load);
    if (_bookings.isEmpty) return const DxEmptyState(title: 'Chưa có đặt lịch');
    return ListView.builder(
      itemCount: _bookings.length,
      itemBuilder: (context, i) {
        final b = _bookings[i] as Map<String, dynamic>;
        return ListTile(
          title: Text(b['booking_code']?.toString() ?? ''),
          subtitle: Text(b['booking_status']?.toString() ?? ''),
          onTap: () => context.go('/patient/booking/${b['id']}'),
        );
      },
    );
  }
}

class PatientBookingDetailScreen extends ConsumerWidget {
  const PatientBookingDetailScreen({super.key, required this.bookingId});
  final String bookingId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder<Map<String, dynamic>>(
      future: ref.read(patientApiProvider).bookingDetail(bookingId),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const DxLoadingState();
        if (snapshot.hasError) return DxErrorState(message: snapshot.error.toString());
        final data = snapshot.data!;
        final booking = data['booking'] as Map<String, dynamic>? ?? {};
        final timeline = data['timeline'] as List<dynamic>? ?? [];
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(booking['booking_code']?.toString() ?? '', style: Theme.of(context).textTheme.titleLarge),
            DxStatusChip(label: booking['booking_status']?.toString() ?? ''),
            const SizedBox(height: 16),
            const Text('Tiến trình'),
            ...timeline.map((e) {
              final ev = e as Map<String, dynamic>;
              return ListTile(
                dense: true,
                title: Text(ev['event']?.toString() ?? ''),
                subtitle: Text(ev['at']?.toString() ?? ''),
              );
            }),
          ],
        );
      },
    );
  }
}

class PatientResultsScreen extends ConsumerStatefulWidget {
  const PatientResultsScreen({super.key});

  @override
  ConsumerState<PatientResultsScreen> createState() => _PatientResultsScreenState();
}

class _PatientResultsScreenState extends ConsumerState<PatientResultsScreen> {
  List<dynamic> _results = [];

  @override
  void initState() {
    super.initState();
    ref.read(patientApiProvider).releasedResults().then((r) {
      if (mounted) setState(() => _results = r);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_results.isEmpty) {
      return const DxEmptyState(title: 'Chưa có kết quả đã phát hành');
    }
    return ListView.builder(
      itemCount: _results.length,
      itemBuilder: (context, i) {
        final r = _results[i] as Map<String, dynamic>;
        return ListTile(
          title: Text(r['report_code']?.toString() ?? 'Báo cáo'),
          subtitle: Text(r['released_at']?.toString() ?? ''),
          onTap: () => context.go('/patient/result/${r['report_code']}'),
        );
      },
    );
  }
}

class PatientResultDetailScreen extends ConsumerWidget {
  const PatientResultDetailScreen({super.key, required this.reportCode});
  final String reportCode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder<Map<String, dynamic>>(
      future: ref.read(patientApiProvider).resultDetail(reportCode),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const DxLoadingState();
        if (snapshot.hasError) return DxErrorState(message: snapshot.error.toString());
        final r = snapshot.data!;
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(r['report_code']?.toString() ?? '', style: Theme.of(context).textTheme.titleLarge),
            Text('Phiên bản: ${r['version'] ?? 1}'),
            Text('Phát hành: ${r['released_at'] ?? '—'}'),
          ],
        );
      },
    );
  }
}

class PatientPaymentsScreen extends StatelessWidget {
  const PatientPaymentsScreen({super.key});
  @override
  Widget build(BuildContext context) => const DxEmptyState(title: 'Lịch sử thanh toán', icon: Icons.payment);
}

class PatientInvoicesScreen extends StatelessWidget {
  const PatientInvoicesScreen({super.key});
  @override
  Widget build(BuildContext context) => const DxEmptyState(title: 'Hóa đơn', icon: Icons.receipt_long);
}

class PatientConsultationsScreen extends StatelessWidget {
  const PatientConsultationsScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return const DxEmptyState(
      title: 'Tư vấn',
      subtitle: 'Không phải cấp cứu. Gọi 115 nếu cần hỗ trợ khẩn cấp.',
      icon: Icons.medical_services_outlined,
    );
  }
}

class PatientNotificationsScreen extends ConsumerStatefulWidget {
  const PatientNotificationsScreen({super.key});

  @override
  ConsumerState<PatientNotificationsScreen> createState() => _PatientNotificationsScreenState();
}

class _PatientNotificationsScreenState extends ConsumerState<PatientNotificationsScreen> {
  List<dynamic> _items = [];

  @override
  void initState() {
    super.initState();
    ref.read(patientApiProvider).notifications().then((n) {
      if (mounted) setState(() => _items = n);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_items.isEmpty) return const DxEmptyState(title: 'Không có thông báo');
    return ListView.builder(
      itemCount: _items.length,
      itemBuilder: (context, i) {
        final n = _items[i] as Map<String, dynamic>;
        return ListTile(
          title: Text(n['title']?.toString() ?? ''),
          subtitle: Text(n['body']?.toString() ?? ''),
        );
      },
    );
  }
}

class PatientProfileScreen extends StatelessWidget {
  const PatientProfileScreen({super.key});
  @override
  Widget build(BuildContext context) => const DxEmptyState(title: 'Hồ sơ bệnh nhân', icon: Icons.person_outline);
}
