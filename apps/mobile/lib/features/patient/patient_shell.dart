import 'package:flutter/material.dart';

import 'package:dxcon_mobile/features/shared/placeholder_screen.dart';

class PatientShell extends WorkspaceShell {
  const PatientShell({super.key, required super.child});

  @override
  String get workspaceName => 'Bệnh nhân';

  @override
  List<NavigationDestination> get destinations => const [
    NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Trang chủ'),
    NavigationDestination(
      icon: Icon(Icons.storefront_outlined),
      label: 'Dịch vụ',
    ),
    NavigationDestination(
      icon: Icon(Icons.event_note_outlined),
      label: 'Đặt lịch',
    ),
    NavigationDestination(icon: Icon(Icons.science_outlined), label: 'Kết quả'),
    NavigationDestination(icon: Icon(Icons.person_outline), label: 'Hồ sơ'),
  ];

  @override
  List<String> get routes => const [
    '/patient/home',
    '/patient/marketplace',
    '/patient/bookings',
    '/patient/results',
    '/patient/profile',
  ];
}
