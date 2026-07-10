import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:dxcon_mobile/app/dxcon_app.dart';
import 'package:dxcon_mobile/bootstrap/app_bootstrap.dart';
import 'package:dxcon_mobile/services/crash_reporting_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final crashReporting = createCrashReportingProvider();
  await crashReporting.init();
  await AppBootstrap.initialize();
  runApp(const ProviderScope(child: DxConApp()));
}
