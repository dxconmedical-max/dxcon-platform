import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:dxcon_mobile/core/auth/auth_provider.dart';
import 'package:dxcon_mobile/design_system/components.dart';

class PlaceholderScreen extends StatelessWidget {
  const PlaceholderScreen({super.key, required this.title, this.subtitle});

  final String title;
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    return DxEmptyState(
      title: title,
      subtitle: subtitle ?? 'Chức năng đang được phát triển',
      icon: Icons.construction_outlined,
    );
  }
}

abstract class WorkspaceShell extends ConsumerWidget {
  const WorkspaceShell({super.key, required this.child});

  final Widget child;

  String get workspaceName;
  List<NavigationDestination> get destinations;
  List<String> get routes;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).matchedLocation;
    final selected = _selectedIndex(location);

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: selected.clamp(0, destinations.length - 1),
        onDestinationSelected: (index) => context.go(routes[index]),
        destinations: destinations,
      ),
      appBar: AppBar(
        title: Text(workspaceName),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authNotifierProvider.notifier).logout(),
            tooltip: 'Đăng xuất',
          ),
        ],
      ),
    );
  }

  int _selectedIndex(String location) {
    for (var i = 0; i < routes.length; i++) {
      if (location.startsWith(routes[i])) return i;
    }
    return 0;
  }
}
