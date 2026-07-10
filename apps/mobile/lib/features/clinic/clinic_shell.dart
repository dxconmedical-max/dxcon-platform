import 'package:flutter/material.dart';

import 'package:dxcon_mobile/features/shared/placeholder_screen.dart';

class ClinicShell extends WorkspaceShell {
  const ClinicShell({super.key, required super.child});

  @override
  String get workspaceName => 'Phòng khám';

  @override
  List<NavigationDestination> get destinations => const [
    NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Trang chủ'),
  ];

  @override
  List<String> get routes => const ['/clinic/home'];
}

class ExecutiveShell extends WorkspaceShell {
  const ExecutiveShell({super.key, required super.child});

  @override
  String get workspaceName => 'Điều hành';

  @override
  List<NavigationDestination> get destinations => const [
    NavigationDestination(
      icon: Icon(Icons.dashboard_outlined),
      label: 'Tổng quan',
    ),
  ];

  @override
  List<String> get routes => const ['/executive/home'];
}

class AdminShell extends WorkspaceShell {
  const AdminShell({super.key, required super.child});

  @override
  String get workspaceName => 'Quản trị';

  @override
  List<NavigationDestination> get destinations => const [
    NavigationDestination(
      icon: Icon(Icons.admin_panel_settings_outlined),
      label: 'Quản trị',
    ),
  ];

  @override
  List<String> get routes => const ['/admin/home'];
}
