import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:dxcon_mobile/core/auth/auth_provider.dart';
import 'package:dxcon_mobile/core/auth/auth_state.dart';
import 'package:dxcon_mobile/features/auth/forbidden_screen.dart';
import 'package:dxcon_mobile/features/auth/login_screen.dart';
import 'package:dxcon_mobile/features/auth/session_expired_screen.dart'
    show SessionExpiredScreen, ServiceUnavailableScreen;
import 'package:dxcon_mobile/features/organization/org_selector_screen.dart';
import 'package:dxcon_mobile/features/patient/patient_home_screen.dart';
import 'package:dxcon_mobile/features/patient/patient_marketplace_screens.dart';
import 'package:dxcon_mobile/features/patient/patient_bookings_screens.dart';
import 'package:dxcon_mobile/features/collector/collector_screens.dart';
import 'package:dxcon_mobile/features/patient/patient_shell.dart';
import 'package:dxcon_mobile/features/collector/collector_shell.dart';
import 'package:dxcon_mobile/features/doctor/doctor_shell.dart';
import 'package:dxcon_mobile/features/clinic/clinic_shell.dart';
import 'package:dxcon_mobile/features/lab/lab_shell.dart';
import 'package:dxcon_mobile/features/executive/executive_shell.dart';
import 'package:dxcon_mobile/features/admin/admin_shell.dart';
import 'package:dxcon_mobile/features/shared/placeholder_screen.dart';
import 'package:dxcon_mobile/config/environment.dart';

/// Collector profile id — resolved from capabilities metadata or user context.
final collectorIdProvider = Provider<String>((ref) {
  final caps = ref.watch(authNotifierProvider).capabilities;
  return caps?.user.id ?? 'collector-unset';
});

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authNotifierProvider);
  final collectorId = ref.watch(collectorIdProvider);
  return GoRouter(
    initialLocation: '/login',
    debugLogDiagnostics: !AppEnvironment.current.isProduction,
    redirect: (context, state) => _redirect(authState, state.matchedLocation),
    routes: [
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/session-expired', builder: (_, __) => const SessionExpiredScreen()),
      GoRoute(path: '/service-unavailable', builder: (_, __) => const ServiceUnavailableScreen()),
      GoRoute(path: '/forbidden', builder: (_, __) => const ForbiddenScreen()),
      GoRoute(path: '/select-organization', builder: (_, __) => const OrgSelectorScreen()),
      ShellRoute(
        builder: (_, __, child) => PatientShell(child: child),
        routes: [
          GoRoute(path: '/patient/home', builder: (_, __) => const PatientHomeScreen()),
          GoRoute(path: '/patient/marketplace', builder: (_, __) => const PatientMarketplaceScreen()),
          GoRoute(path: '/patient/marketplace/tests', builder: (_, __) => const PatientMarketplaceScreen()),
          GoRoute(path: '/patient/marketplace/packages', builder: (_, __) => const PatientMarketplaceScreen()),
          GoRoute(path: '/patient/marketplace/providers', builder: (_, __) => const PatientMarketplaceScreen()),
          GoRoute(
            path: '/patient/compare',
            builder: (c, s) => PatientCompareScreen(
              listingIds: s.uri.queryParameters['ids']?.split(',').where((e) => e.isNotEmpty).toList() ?? [],
            ),
          ),
          GoRoute(
            path: '/patient/provider/:id',
            builder: (c, s) => PatientProviderScreen(providerId: s.pathParameters['id']!),
          ),
          GoRoute(path: '/patient/bookings', builder: (_, __) => const PatientBookingsScreen()),
          GoRoute(
            path: '/patient/booking/:id',
            builder: (c, s) => PatientBookingDetailScreen(bookingId: s.pathParameters['id']!),
          ),
          GoRoute(
            path: '/patient/payment/:id',
            builder: (c, s) => PatientPaymentScreen(paymentReference: s.pathParameters['id']!),
          ),
          GoRoute(path: '/patient/results', builder: (_, __) => const PatientResultsScreen()),
          GoRoute(
            path: '/patient/result/:id',
            builder: (c, s) => PatientResultDetailScreen(reportCode: s.pathParameters['id']!),
          ),
          GoRoute(path: '/patient/payments', builder: (_, __) => const PatientPaymentsScreen()),
          GoRoute(path: '/patient/invoices', builder: (_, __) => const PatientInvoicesScreen()),
          GoRoute(path: '/patient/consultations', builder: (_, __) => const PatientConsultationsScreen()),
          GoRoute(path: '/patient/notifications', builder: (_, __) => const PatientNotificationsScreen()),
          GoRoute(path: '/patient/profile', builder: (_, __) => const PatientProfileScreen()),
        ],
      ),
      ShellRoute(
        builder: (_, __, child) => CollectorShell(child: child, collectorId: collectorId),
        routes: [
          GoRoute(path: '/collector/home', builder: (_, __) => CollectorHomeScreen(collectorId: collectorId)),
          GoRoute(path: '/collector/jobs', builder: (_, __) => CollectorJobsScreen(collectorId: collectorId)),
          GoRoute(
            path: '/collector/job/:id',
            builder: (c, s) => CollectorJobDetailScreen(
              collectorId: collectorId,
              assignmentId: s.pathParameters['id']!,
            ),
          ),
          GoRoute(path: '/collector/sync', builder: (_, __) => const CollectorSyncScreen()),
          GoRoute(path: '/collector/incidents', builder: (_, __) => const PlaceholderScreen(title: 'Sự cố')),
          GoRoute(path: '/collector/route', builder: (_, __) => const PlaceholderScreen(title: 'Tuyến đường')),
          GoRoute(path: '/collector/handover', builder: (_, __) => const PlaceholderScreen(title: 'Bàn giao')),
        ],
      ),
      ShellRoute(builder: (_, __, child) => DoctorShell(child: child), routes: _doctorRoutes()),
      ShellRoute(builder: (_, __, child) => LabShell(child: child), routes: _labRoutes()),
      ShellRoute(builder: (_, __, child) => ClinicShell(child: child), routes: _clinicRoutes()),
      ShellRoute(builder: (_, __, child) => ExecutiveShell(child: child), routes: _executiveRoutes()),
      ShellRoute(builder: (_, __, child) => AdminShell(child: child), routes: _adminRoutes()),
    ],
  );
});

String? _redirect(AuthState authState, String loc) {
  final status = authState.status;
  const publicRoutes = {'/login', '/session-expired', '/service-unavailable'};
  if (status == AuthStatus.unknown) return null;
  if (status == AuthStatus.sessionExpired && loc != '/session-expired') return '/session-expired';
  if (status == AuthStatus.serviceUnavailable && loc != '/service-unavailable') return '/service-unavailable';
  if (status == AuthStatus.unauthenticated && !publicRoutes.contains(loc)) return '/login';
  if (status == AuthStatus.requiresOrganization && loc != '/select-organization') return '/select-organization';
  if (status == AuthStatus.authenticated && publicRoutes.contains(loc)) {
    return _workspaceHome(authState.capabilities?.workspace ?? 'patient');
  }
  return null;
}

String _workspaceHome(String workspace) {
  switch (workspace.toLowerCase()) {
    case 'collector':
      return '/collector/home';
    case 'doctor':
      return '/doctor/home';
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

List<RouteBase> _doctorRoutes() => [
      GoRoute(path: '/doctor/home', builder: (_, __) => const PlaceholderScreen(title: 'Bác sĩ')),
    ];

List<RouteBase> _labRoutes() => [
      GoRoute(path: '/lab/incoming', builder: (_, __) => const PlaceholderScreen(title: 'Mẫu đến')),
    ];

List<RouteBase> _clinicRoutes() => [
      GoRoute(path: '/clinic/home', builder: (_, __) => const PlaceholderScreen(title: 'Phòng khám')),
    ];

List<RouteBase> _executiveRoutes() => [
      GoRoute(path: '/executive/home', builder: (_, __) => const PlaceholderScreen(title: 'Điều hành')),
    ];

List<RouteBase> _adminRoutes() => [
      GoRoute(path: '/admin/home', builder: (_, __) => const PlaceholderScreen(title: 'Quản trị')),
    ];
