import 'package:flutter_test/flutter_test.dart';

import 'package:dxcon_mobile/core/permissions/capability_helpers.dart';
import 'package:dxcon_mobile/models/auth_models.dart';

void main() {
  test('workspace helper is case insensitive', () {
    const caps = AuthCapabilities(
      user: AuthUser(id: '1', email: 'a@b.com', role: 'patient'),
      workspace: 'PATIENT',
      defaultWorkspace: 'patient',
      permissions: [],
      features: [],
    );
    expect(isWorkspace(caps, 'patient'), isTrue);
  });
}
