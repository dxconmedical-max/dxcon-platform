import 'dart:convert';
import 'dart:io';

import 'package:dxcon_mobile/config/environment.dart';
import 'package:dxcon_mobile/core/navigation/role_routing.dart';
import 'package:dxcon_mobile/core/security/security_service.dart';

/// Phase 1 foundation verification — architecture, env, auth, routing, offline.
void main() {
  final root = Directory.current;
  if (!File('${root.path}/pubspec.yaml').existsSync()) {
    stderr.writeln('Run from apps/mobile directory');
    exit(1);
  }

  final checks = <String, bool>{};
  final warnings = <String>[];

  final requiredPaths = [
    'lib/main.dart',
    'lib/config/environment.dart',
    'lib/core/api/api_client.dart',
    'lib/core/auth/auth_repository.dart',
    'lib/core/auth/auth_provider.dart',
    'lib/core/storage/secure_token_storage.dart',
    'lib/core/navigation/app_router.dart',
    'lib/core/navigation/role_routing.dart',
    'lib/core/errors/api_error.dart',
    'lib/core/offline/offline_read_cache.dart',
    'lib/core/offline/offline_reader.dart',
    'lib/core/offline/offline_read_state.dart',
    'lib/core/security/release_guards.dart',
    'lib/bootstrap/app_bootstrap.dart',
    'lib/features/auth/login_screen.dart',
    'config/production.env.json',
    'config/staging.env.json',
    'config/development.env.json',
    'docs/PHASE_1_FOUNDATION.md',
    'docs/ENVIRONMENT_SETUP.md',
    'docs/MOBILE_TOKEN_SECURITY.md',
    'docs/ANDROID_RELEASE.md',
    'docs/IOS_RELEASE.md',
    '../../.github/workflows/mobile-ci.yml',
    'test/core/auth_repository_test.dart',
    'test/core/role_routing_test.dart',
    'test/core/offline_read_cache_test.dart',
    'test/core/release_guards_test.dart',
  ];

  for (final path in requiredPaths) {
    checks['file:$path'] = File('${root.path}/$path').existsSync();
  }

  checks['api_url_production'] =
      AppEnvironment.current.apiBaseUrl == 'https://api.dxcon.com.vn';
  checks['demo_mode_disabled'] = const SecurityService().demoModeDisabled;
  checks['clinic_role_routing'] = workspaceHomeFor('clinic') == '/clinic/home';
  checks['lab_role_routing'] = workspaceHomeFor('lab') == '/lab/incoming';

  final prodEnv =
      jsonDecode(
            File('${root.path}/config/production.env.json').readAsStringSync(),
          )
          as Map<String, dynamic>;
  checks['prod_env_demo_false'] = prodEnv['DEMO_MODE']?.toString() == 'false';
  checks['prod_env_no_sentry_secret'] =
      (prodEnv['SENTRY_DSN']?.toString() ?? '').isEmpty;

  final gradle = File(
    '${root.path}/android/app/build.gradle.kts',
  ).readAsStringSync();
  checks['android_flavors'] =
      gradle.contains('development') &&
      gradle.contains('staging') &&
      gradle.contains('production');

  final androidSdk =
      Platform.environment['ANDROID_HOME'] ??
      Platform.environment['ANDROID_SDK_ROOT'];
  if (androidSdk == null || !Directory(androidSdk).existsSync()) {
    warnings.add('android_sdk_not_configured');
    checks['android_sdk'] = false;
  } else {
    checks['android_sdk'] = true;
  }

  if (!Platform.isMacOS) {
    warnings.add('ios_build_not_run_non_macos');
  }

  final critical = checks.entries
      .where((e) => !e.value && e.key != 'android_sdk')
      .map((e) => e.key)
      .toList();

  final status = critical.isEmpty
      ? (warnings.isEmpty ? 'PASS' : 'PASS_WITH_WARNINGS')
      : 'FAIL';

  final now = DateTime.now().toUtc().toIso8601String();
  final report = {
    'generated_at': now,
    'phase': 1,
    'status': status,
    'gate': 'STOP_AFTER_PHASE_1_AWAIT_PRODUCTION_VERIFICATION',
    'web_go_live_commit': 'f5d2f45',
    'checks': checks,
    'warnings': warnings,
    'critical': critical,
    'scope': [
      'mobile_architecture',
      'environment_configuration',
      'secure_token_session_storage',
      'login_logout',
      'role_routing',
      'api_client',
      'error_handling',
      'offline_safe_read_states',
    ],
    'out_of_scope': ['phase_2_patient_portal', 'phase_3_collector'],
    'phase_2_blockers': [
      'production_device_auth_verification',
      'firebase_push_configuration',
      'android_release_signing_secrets',
      'ios_provisioning_profiles',
      'mobile_device_token_api',
    ],
  };

  _write('generated-release/MOBILE_PHASE_1_REPORT.json', report);
  _write('generated-release/MOBILE_FOUNDATION_REPORT.json', {
    ...report,
    'legacy_alias': 'MOBILE_PHASE_1_REPORT',
  });

  stdout.writeln('Mobile Phase 1 Verify: $status');
  stdout.writeln(
    'STOP after Phase 1 — await production verification before Phase 2',
  );
  if (critical.isNotEmpty) {
    for (final c in critical) {
      stderr.writeln('CRITICAL: $c');
    }
    exit(1);
  }
}

void _write(String path, Map<String, dynamic> data) {
  final file = File(path);
  file.parent.createSync(recursive: true);
  file.writeAsStringSync(const JsonEncoder.withIndent('  ').convert(data));
}
