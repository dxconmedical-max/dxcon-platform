import 'package:dxcon_mobile/config/environment.dart';

/// Crash reporting abstraction — no tokens, passwords, or PHI.
abstract class CrashReportingProvider {
  Future<void> init();
  void captureException(Object error, {StackTrace? stackTrace});
  void captureMessage(String message, {String? category});
}

class NoOpCrashReportingProvider implements CrashReportingProvider {
  @override
  Future<void> init() async {}

  @override
  void captureException(Object error, {StackTrace? stackTrace}) {}

  @override
  void captureMessage(String message, {String? category}) {}
}

CrashReportingProvider createCrashReportingProvider() {
  final dsn = AppEnvironment.current.sentryDsn;
  if (dsn.isEmpty) {
    return NoOpCrashReportingProvider();
  }
  // Sentry wiring requires DSN at build time — use no-op until configured.
  return NoOpCrashReportingProvider();
}
