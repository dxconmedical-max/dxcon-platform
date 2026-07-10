import 'package:flutter_test/flutter_test.dart';

import 'package:dxcon_mobile/config/environment.dart';
import 'package:dxcon_mobile/core/permissions/capability_helpers.dart';
import 'package:dxcon_mobile/models/auth_models.dart';

void main() {
  test('production environment defaults', () {
    expect(AppEnvironment.current.apiBaseUrl, 'https://api.dxcon.com.vn');
    expect(AppEnvironment.current.demoMode, isFalse);
    expect(AppEnvironment.current.webAppUrl, 'https://app.dxcon.com.vn');
  });

  test('permission helpers respect wildcard', () {
    const caps = AuthCapabilities(
      user: AuthUser(id: '1', email: 'a@b.com', role: 'admin'),
      workspace: 'admin',
      defaultWorkspace: 'admin',
      permissions: ['*'],
      features: ['marketplace'],
    );
    expect(can(caps, 'anything.here'), isTrue);
    expect(hasFeature(caps, 'marketplace'), isTrue);
    expect(isWorkspace(caps, 'admin'), isTrue);
  });

  test('canAny and canAll', () {
    const caps = AuthCapabilities(
      user: AuthUser(id: '1', email: 'a@b.com', role: 'doctor'),
      workspace: 'doctor',
      defaultWorkspace: 'doctor',
      permissions: ['patients.read', 'reports.read'],
      features: [],
    );
    expect(canAny(caps, ['patients.read', 'admin.manage']), isTrue);
    expect(canAll(caps, ['patients.read', 'reports.read']), isTrue);
    expect(canAll(caps, ['patients.read', 'admin.manage']), isFalse);
  });
}
