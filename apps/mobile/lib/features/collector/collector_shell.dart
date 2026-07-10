import 'package:flutter/material.dart';

import 'package:dxcon_mobile/features/shared/placeholder_screen.dart';

class CollectorShell extends WorkspaceShell {
  const CollectorShell({super.key, required super.child});

  @override
  String get workspaceName => 'Lấy mẫu';

  @override
  List<NavigationDestination> get destinations => const [
    NavigationDestination(icon: Icon(Icons.work_outline), label: 'Công việc'),
    NavigationDestination(icon: Icon(Icons.route_outlined), label: 'Tuyến'),
    NavigationDestination(icon: Icon(Icons.swap_horiz), label: 'Bàn giao'),
  ];

  @override
  List<String> get routes => const [
    '/collector/jobs',
    '/collector/route',
    '/collector/handover',
  ];
}
