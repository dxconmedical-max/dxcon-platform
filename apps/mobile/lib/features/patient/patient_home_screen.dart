import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:dxcon_mobile/core/auth/auth_provider.dart';
import 'package:dxcon_mobile/design_system/components.dart';
import 'package:dxcon_mobile/services/marketplace_repository.dart';
import 'package:dxcon_mobile/services/patient_api_repository.dart';

final patientApiProvider = Provider<PatientApiRepository>((ref) {
  return PatientApiRepository(ref.watch(apiClientProvider));
});

final marketplaceRepoProvider = Provider<MarketplaceRepository>((ref) {
  return MarketplaceRepository(ref.watch(apiClientProvider));
});

class PatientHomeScreen extends ConsumerStatefulWidget {
  const PatientHomeScreen({super.key});

  @override
  ConsumerState<PatientHomeScreen> createState() => _PatientHomeScreenState();
}

class _PatientHomeScreenState extends ConsumerState<PatientHomeScreen> {
  Map<String, dynamic>? _data;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await ref.read(patientApiProvider).dashboard();
      if (!mounted) return;
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const DxLoadingState(message: 'Đang tải...');
    if (_error != null) return DxErrorState(message: _error!, onRetry: _load);
    final greeting = _data?['greeting_name'] ?? 'Bạn';
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Xin chào, $greeting', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _QuickAction('Đặt xét nghiệm', Icons.science_outlined, () => context.go('/patient/marketplace')),
              _QuickAction('So sánh', Icons.compare_arrows, () => context.go('/patient/compare')),
              _QuickAction('Kết quả', Icons.description_outlined, () => context.go('/patient/results')),
              _QuickAction('Thanh toán', Icons.payment_outlined, () => context.go('/patient/payments')),
            ],
          ),
          const SizedBox(height: 24),
          if (_data?['active_booking'] != null)
            Card(
              child: ListTile(
                title: const Text('Đặt lịch đang hoạt động'),
                subtitle: Text((_data!['active_booking'] as Map)['booking_code']?.toString() ?? ''),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  final id = (_data!['active_booking'] as Map)['id']?.toString();
                  if (id != null) context.go('/patient/booking/$id');
                },
              ),
            ),
          if ((_data?['unread_notifications'] as int? ?? 0) > 0)
            ListTile(
              leading: const Icon(Icons.notifications_outlined),
              title: Text('${_data!['unread_notifications']} thông báo chưa đọc'),
              onTap: () => context.go('/patient/notifications'),
            ),
        ],
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  const _QuickAction(this.label, this.icon, this.onTap);
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      avatar: Icon(icon, size: 18),
      label: Text(label),
      onPressed: onTap,
    );
  }
}

class PatientMarketplaceScreen extends ConsumerStatefulWidget {
  const PatientMarketplaceScreen({super.key});

  @override
  ConsumerState<PatientMarketplaceScreen> createState() => _PatientMarketplaceScreenState();
}

class _PatientMarketplaceScreenState extends ConsumerState<PatientMarketplaceScreen> {
  final _query = TextEditingController();
  List<dynamic> _items = [];
  String? _error;
  bool _loading = false;

  Future<void> _search() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final res = await ref.read(marketplaceRepoProvider).search(q: _query.text);
      setState(() {
        _items = (res['items'] as List<dynamic>?) ?? (res['listings'] as List<dynamic>?) ?? [];
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
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _query,
                  decoration: const InputDecoration(hintText: 'Tìm xét nghiệm, gói, nhà cung cấp...'),
                  onSubmitted: (_) => _search(),
                ),
              ),
              IconButton(onPressed: _search, icon: const Icon(Icons.search)),
            ],
          ),
        ),
        if (_loading) const Expanded(child: DxLoadingState()),
        if (_error != null) Expanded(child: DxErrorState(message: _error!, onRetry: _search)),
        if (!_loading && _error == null)
          Expanded(
            child: _items.isEmpty
                ? const DxEmptyState(title: 'Chưa có kết quả', subtitle: 'Thử từ khóa khác')
                : ListView.builder(
                    itemCount: _items.length,
                    itemBuilder: (context, index) {
                      final item = _items[index] as Map<String, dynamic>;
                      return ListTile(
                        title: Text(item['title']?.toString() ?? item['listing_code']?.toString() ?? 'Dịch vụ'),
                        subtitle: Text('${item['base_price'] ?? ''} ${item['currency'] ?? 'VND'}'),
                        onTap: () {
                          final providerId = item['provider']?['id'] ?? item['provider_id'];
                          if (providerId != null) context.go('/patient/provider/$providerId');
                        },
                      );
                    },
                  ),
          ),
      ],
    );
  }
}
