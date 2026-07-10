import 'package:flutter/material.dart';

import 'package:dxcon_mobile/features/shared/placeholder_screen.dart';

class LabShell extends WorkspaceShell {
  const LabShell({super.key, required super.child});

  @override
  String get workspaceName => 'Phòng xét nghiệm';

  @override
  List<NavigationDestination> get destinations => const [
    NavigationDestination(icon: Icon(Icons.inbox_outlined), label: 'Đến'),
    NavigationDestination(
      icon: Icon(Icons.check_circle_outline),
      label: 'Nhận',
    ),
    NavigationDestination(icon: Icon(Icons.queue_outlined), label: 'Hàng đợi'),
    NavigationDestination(icon: Icon(Icons.biotech_outlined), label: 'Kết quả'),
  ];

  @override
  List<String> get routes => const [
    '/lab/incoming',
    '/lab/receive',
    '/lab/queue',
    '/lab/results',
  ];
}
