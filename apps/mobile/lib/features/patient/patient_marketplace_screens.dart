import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:dxcon_mobile/design_system/components.dart';
import 'package:dxcon_mobile/features/patient/patient_home_screen.dart';

class PatientCompareScreen extends ConsumerStatefulWidget {
  const PatientCompareScreen({super.key, this.listingIds = const []});
  final List<String> listingIds;

  @override
  ConsumerState<PatientCompareScreen> createState() => _PatientCompareScreenState();
}

class _PatientCompareScreenState extends ConsumerState<PatientCompareScreen> {
  Map<String, dynamic>? _data;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    if (widget.listingIds.isNotEmpty) _load();
    else _loading = false;
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await ref.read(marketplaceRepoProvider).compare(widget.listingIds);
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.listingIds.isEmpty) {
      return const DxEmptyState(title: 'Chọn dịch vụ để so sánh', icon: Icons.compare);
    }
    if (_loading) return const DxLoadingState();
    if (_error != null) return DxErrorState(message: _error!, onRetry: _load);
    final items = (_data?['comparisons'] as List<dynamic>?) ?? [];
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (context, i) {
        final item = items[i] as Map<String, dynamic>;
        return Card(
          child: ListTile(
            title: Text(item['provider_name']?.toString() ?? 'Nhà cung cấp'),
            subtitle: Text(
              'Giá: ${item['total'] ?? item['base_price']} · Cập nhật: ${item['price_updated_at'] ?? '—'}',
            ),
          ),
        );
      },
    );
  }
}

class PatientProviderScreen extends ConsumerWidget {
  const PatientProviderScreen({super.key, required this.providerId});
  final String providerId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder<Map<String, dynamic>>(
      future: ref.read(marketplaceRepoProvider).providerProfile(providerId),
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const DxLoadingState();
        }
        if (snapshot.hasError) {
          return DxErrorState(message: snapshot.error.toString());
        }
        final p = snapshot.data ?? {};
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(p['provider_name']?.toString() ?? '', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            DxStatusChip(
              label: p['verified'] == true ? 'Đã xác minh' : 'Chưa xác minh',
            ),
            const SizedBox(height: 16),
            Text(p['description']?.toString() ?? ''),
            ListTile(title: const Text('Địa chỉ'), subtitle: Text(p['address']?.toString() ?? '—')),
            ListTile(title: const Text('Đánh giá'), subtitle: Text('${p['rating_avg'] ?? 0} (${p['rating_count'] ?? 0})')),
          ],
        );
      },
    );
  }
}

class PatientPaymentScreen extends ConsumerStatefulWidget {
  const PatientPaymentScreen({super.key, required this.paymentReference});
  final String paymentReference;

  @override
  ConsumerState<PatientPaymentScreen> createState() => _PatientPaymentScreenState();
}

class _PatientPaymentScreenState extends ConsumerState<PatientPaymentScreen> {
  Map<String, dynamic>? _payment;
  Timer? _timer;
  String? _error;

  @override
  void initState() {
    super.initState();
    _poll();
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _poll());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _poll() async {
    try {
      final data = await ref.read(marketplaceRepoProvider).paymentStatus(widget.paymentReference);
      if (!mounted) return;
      setState(() {
        _payment = data;
        _error = null;
      });
      final status = (data['status'] ?? '').toString().toUpperCase();
      if (status == 'SUCCEEDED' || status == 'FAILED' || status == 'EXPIRED') {
        _timer?.cancel();
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_payment == null && _error == null) return const DxLoadingState(message: 'Đang tải thanh toán...');
    if (_error != null) return DxErrorState(message: _error!, onRetry: _poll);
    final status = (_payment!['status'] ?? '').toString();
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Thanh toán QR', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 16),
          Text('Số tiền: ${_payment!['amount']} ${_payment!['currency'] ?? 'VND'}'),
          Text('Mã: ${_payment!['payment_reference']}'),
          Text('Trạng thái: $status'),
          const SizedBox(height: 16),
          if (_payment!['qr_payload'] != null)
            SelectableText(_payment!['qr_payload'].toString()),
          const SizedBox(height: 8),
          const Text('Trạng thái được xác nhận từ máy chủ. Không đánh dấu thành công trên thiết bị.'),
        ],
      ),
    );
  }
}
