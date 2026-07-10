import 'package:flutter/material.dart';

import 'package:dxcon_mobile/features/shared/placeholder_screen.dart';

class DoctorShell extends WorkspaceShell {
  const DoctorShell({super.key, required super.child});

  @override
  String get workspaceName => 'Bác sĩ';

  @override
  List<NavigationDestination> get destinations => const [
    NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Trang chủ'),
    NavigationDestination(icon: Icon(Icons.people_outline), label: 'Bệnh nhân'),
    NavigationDestination(
      icon: Icon(Icons.description_outlined),
      label: 'Báo cáo',
    ),
    NavigationDestination(
      icon: Icon(Icons.calendar_today_outlined),
      label: 'Lịch hẹn',
    ),
  ];

  @override
  List<String> get routes => const [
    '/doctor/home',
    '/doctor/patients',
    '/doctor/reports',
    '/doctor/appointments',
  ];
}
