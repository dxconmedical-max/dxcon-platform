import 'package:flutter/material.dart';

import 'package:dxcon_mobile/features/shared/placeholder_screen.dart';

class CollectorShell extends WorkspaceShell {
  const CollectorShell({
    super.key,
    required super.child,
    required this.collectorId,
  });

  final String collectorId;

  @override
  String get workspaceName => 'DxCon Collector';

  @override
  List<NavigationDestination> get destinations => const [
    NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Trang chủ'),
    NavigationDestination(icon: Icon(Icons.work_outline), label: 'Công việc'),
    NavigationDestination(icon: Icon(Icons.sync), label: 'Đồng bộ'),
  ];

  @override
  List<String> get routes => const [
    '/collector/home',
    '/collector/jobs',
    '/collector/sync',
  ];
}
