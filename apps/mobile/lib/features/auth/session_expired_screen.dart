import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:dxcon_mobile/core/auth/auth_provider.dart';

class SessionExpiredScreen extends ConsumerWidget {
  const SessionExpiredScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Phiên hết hạn')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => context.go('/login'),
              child: const Text('Đăng nhập'),
            ),
          ],
        ),
      ),
    );
  }
}

class ServiceUnavailableScreen extends ConsumerWidget {
  const ServiceUnavailableScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final error = ref.watch(authNotifierProvider).lastError?.message;
    return Scaffold(
      appBar: AppBar(title: const Text('Dịch vụ không khả dụng')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(error ?? 'Dịch vụ tạm thời không khả dụng'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () =>
                  ref.read(authNotifierProvider.notifier).bootstrap(),
              child: const Text('Thử lại'),
            ),
          ],
        ),
      ),
    );
  }
}
