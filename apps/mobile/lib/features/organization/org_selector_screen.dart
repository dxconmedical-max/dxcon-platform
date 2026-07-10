import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:dxcon_mobile/core/auth/auth_provider.dart';
import 'package:dxcon_mobile/core/errors/api_error.dart';
import 'package:dxcon_mobile/design_system/components.dart';

class OrgSelectorScreen extends ConsumerWidget {
  const OrgSelectorScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authNotifierProvider);
    final memberships = auth.memberships
        .where((m) => m.isActiveMembership)
        .toList();

    if (auth.isLoading) {
      return const Scaffold(body: DxLoadingState());
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Chọn tổ chức')),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: memberships.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final m = memberships[index];
          return Card(
            child: ListTile(
              title: Text(m.organizationName),
              subtitle: Text('${m.organizationType} · ${m.roleCode}'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () async {
                try {
                  await ref
                      .read(authNotifierProvider.notifier)
                      .selectOrganization(m.organizationId);
                  if (!context.mounted) return;
                  context.go('/patient/home');
                } on ApiError catch (e) {
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(
                    context,
                  ).showSnackBar(SnackBar(content: Text(e.message)));
                }
              },
            ),
          );
        },
      ),
    );
  }
}
