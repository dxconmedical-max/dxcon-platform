import 'package:flutter_test/flutter_test.dart';

import 'package:dxcon_mobile/config/environment.dart';
import 'package:dxcon_mobile/core/security/release_guards.dart';
import 'package:dxcon_mobile/core/security/security_service.dart';

void main() {
  test('production defaults disable demo mode', () {
    expect(AppEnvironment.current.demoMode, isFalse);
    expect(const SecurityService().demoModeDisabled, isTrue);
  });

  test('release guards allow safe production env in debug/test', () {
    const env = AppEnvironment(
      name: 'production',
      apiBaseUrl: 'https://api.dxcon.com.vn',
      publicSiteUrl: 'https://dxcon.com.vn',
      webAppUrl: 'https://app.dxcon.com.vn',
      demoMode: false,
    );
    // In test/debug mode assertSafeForRelease is a no-op for mode checks.
    expect(
      () => const ReleaseGuards().assertSafeForRelease(environment: env),
      returnsNormally,
    );
  });

  test('mocksAllowed is false when demo mode off', () {
    expect(const ReleaseGuards().mocksAllowed, isFalse);
  });
}
