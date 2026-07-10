import 'package:go_router/go_router.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:dxcon_mobile/config/environment.dart';
import 'package:dxcon_mobile/core/auth/auth_provider.dart';
import 'package:dxcon_mobile/core/auth/auth_state.dart';
import 'package:dxcon_mobile/features/auth/forbidden_screen.dart';
import 'package:dxcon_mobile/features/auth/login_screen.dart';
import 'package:dxcon_mobile/features/auth/session_expired_screen.dart'
    show SessionExpiredScreen, ServiceUnavailableScreen;
import 'package:dxcon_mobile/features/organization/org_selector_screen.dart';
import 'package:dxcon_mobile/features/patient/patient_shell.dart';
import 'package:dxcon_mobile/features/collector/collector_shell.dart';
import 'package:dxcon_mobile/features/doctor/doctor_shell.dart';
import 'package:dxcon_mobile/features/clinic/clinic_shell.dart';
import 'package:dxcon_mobile/features/lab/lab_shell.dart';
import 'package:dxcon_mobile/features/executive/executive_shell.dart';
import 'package:dxcon_mobile/features/admin/admin_shell.dart';
import 'package:dxcon_mobile/features/shared/placeholder_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authNotifierProvider);
  return GoRouter(
    initialLocation: '/login',
    debugLogDiagnostics: !AppEnvironment.current.isProduction,
    redirect: (context, state) {
      final loc = state.matchedLocation;
      final status = authState.status;
      final publicRoutes = {
        '/login',
        '/session-expired',
        '/service-unavailable',
      };
      if (status == AuthStatus.unknown) return null;
      if (status == AuthStatus.sessionExpired && loc != '/session-expired') {
        return '/session-expired';
      }
      if (status == AuthStatus.serviceUnavailable &&
          loc != '/service-unavailable') {
        return '/service-unavailable';
      }
      if (status == AuthStatus.unauthenticated && !publicRoutes.contains(loc)) {
        return '/login';
      }
      if (status == AuthStatus.requiresOrganization &&
          loc != '/select-organization') {
        return '/select-organization';
      }
      if (status == AuthStatus.authenticated && publicRoutes.contains(loc)) {
        return _workspaceHome(authState.capabilities?.workspace ?? 'patient');
      }
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(
        path: '/session-expired',
        builder: (_, __) => const SessionExpiredScreen(),
      ),
      GoRoute(
        path: '/service-unavailable',
        builder: (_, __) => const ServiceUnavailableScreen(),
      ),
      GoRoute(path: '/forbidden', builder: (_, __) => const ForbiddenScreen()),
      GoRoute(
        path: '/select-organization',
        builder: (_, __) => const OrgSelectorScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => PatientShell(child: child),
        routes: _patientRoutes(),
      ),
      ShellRoute(
        builder: (context, state, child) => CollectorShell(child: child),
        routes: _collectorRoutes(),
      ),
      ShellRoute(
        builder: (context, state, child) => DoctorShell(child: child),
        routes: _doctorRoutes(),
      ),
      ShellRoute(
        builder: (context, state, child) => ClinicShell(child: child),
        routes: _clinicRoutes(),
      ),
      ShellRoute(
        builder: (context, state, child) => LabShell(child: child),
        routes: _labRoutes(),
      ),
      ShellRoute(
        builder: (context, state, child) => ExecutiveShell(child: child),
        routes: _executiveRoutes(),
      ),
      ShellRoute(
        builder: (context, state, child) => AdminShell(child: child),
        routes: _adminRoutes(),
      ),
    ],
  );
});

String _workspaceHome(String workspace) {
  switch (workspace.toLowerCase()) {
    case 'collector':
      return '/collector/jobs';
    case 'doctor':
      return '/doctor/home';
    case 'clinic':
      return '/clinic/home';
    case 'lab':
    case 'laboratory':
      return '/lab/incoming';
    case 'executive':
      return '/executive/home';
    case 'admin':
      return '/admin/home';
    default:
      return '/patient/home';
  }
}

List<RouteBase> _patientRoutes() => [
  GoRoute(
    path: '/patient/home',
    builder: (_, __) => const PlaceholderScreen(title: 'Trang chủ bệnh nhân'),
  ),
  GoRoute(
    path: '/patient/marketplace',
    builder: (_, __) => const PlaceholderScreen(title: 'Marketplace'),
  ),
  GoRoute(
    path: '/patient/bookings',
    builder: (_, __) => const PlaceholderScreen(title: 'Đặt lịch của tôi'),
  ),
  GoRoute(
    path: '/patient/results',
    builder: (_, __) => const PlaceholderScreen(title: 'Kết quả'),
  ),
  GoRoute(
    path: '/patient/payments',
    builder: (_, __) => const PlaceholderScreen(title: 'Thanh toán'),
  ),
  GoRoute(
    path: '/patient/profile',
    builder: (_, __) => const PlaceholderScreen(title: 'Hồ sơ'),
  ),
];

List<RouteBase> _collectorRoutes() => [
  GoRoute(
    path: '/collector/jobs',
    builder: (_, __) => const PlaceholderScreen(title: 'Công việc lấy mẫu'),
  ),
  GoRoute(
    path: '/collector/route',
    builder: (_, __) => const PlaceholderScreen(title: 'Tuyến đường'),
  ),
  GoRoute(
    path: '/collector/job/:id',
    builder: (c, s) => PlaceholderScreen(
      title: 'Chi tiết công việc ${s.pathParameters['id']}',
    ),
  ),
  GoRoute(
    path: '/collector/handover',
    builder: (_, __) => const PlaceholderScreen(title: 'Bàn giao mẫu'),
  ),
];

List<RouteBase> _doctorRoutes() => [
  GoRoute(
    path: '/doctor/home',
    builder: (_, __) => const PlaceholderScreen(title: 'Bác sĩ'),
  ),
  GoRoute(
    path: '/doctor/patients',
    builder: (_, __) => const PlaceholderScreen(title: 'Bệnh nhân'),
  ),
  GoRoute(
    path: '/doctor/reports',
    builder: (_, __) => const PlaceholderScreen(title: 'Báo cáo'),
  ),
  GoRoute(
    path: '/doctor/appointments',
    builder: (_, __) => const PlaceholderScreen(title: 'Lịch hẹn'),
  ),
];

List<RouteBase> _labRoutes() => [
  GoRoute(
    path: '/lab/incoming',
    builder: (_, __) => const PlaceholderScreen(title: 'Mẫu đến'),
  ),
  GoRoute(
    path: '/lab/receive',
    builder: (_, __) => const PlaceholderScreen(title: 'Nhận mẫu'),
  ),
  GoRoute(
    path: '/lab/queue',
    builder: (_, __) => const PlaceholderScreen(title: 'Hàng đợi'),
  ),
  GoRoute(
    path: '/lab/results',
    builder: (_, __) => const PlaceholderScreen(title: 'Kết quả'),
  ),
];

List<RouteBase> _clinicRoutes() => [
  GoRoute(
    path: '/clinic/home',
    builder: (_, __) => const PlaceholderScreen(title: 'Phòng khám'),
  ),
];

List<RouteBase> _executiveRoutes() => [
  GoRoute(
    path: '/executive/home',
    builder: (_, __) => const PlaceholderScreen(title: 'Điều hành'),
  ),
];

List<RouteBase> _adminRoutes() => [
  GoRoute(
    path: '/admin/home',
    builder: (_, __) => const PlaceholderScreen(title: 'Quản trị'),
  ),
];
