import 'package:flutter_test/flutter_test.dart';

import 'package:dxcon_mobile/core/auth/auth_state.dart';
import 'package:dxcon_mobile/core/navigation/app_router.dart';
import 'package:dxcon_mobile/core/navigation/role_routing.dart';
import 'package:dxcon_mobile/models/auth_models.dart';

void main() {
  group('workspaceHomeFor', () {
    test('routes known workspaces', () {
      expect(workspaceHomeFor('patient'), '/patient/home');
      expect(workspaceHomeFor('collector'), '/collector/home');
      expect(workspaceHomeFor('doctor'), '/doctor/home');
      expect(workspaceHomeFor('lab'), '/lab/incoming');
      expect(workspaceHomeFor('laboratory'), '/lab/incoming');
      expect(workspaceHomeFor('clinic'), '/clinic/home');
      expect(workspaceHomeFor('reception'), '/clinic/home');
      expect(workspaceHomeFor('executive'), '/executive/home');
      expect(workspaceHomeFor('admin'), '/admin/home');
    });

    test('defaults unknown workspace to patient', () {
      expect(workspaceHomeFor('unknown'), '/patient/home');
    });
  });

  group('redirectForAuth', () {
    test('unauthenticated users go to login', () {
      const state = AuthState(status: AuthStatus.unauthenticated);
      expect(redirectForAuth(state, '/patient/home'), '/login');
    });

    test('authenticated users leave login to workspace home', () {
      const state = AuthState(
        status: AuthStatus.authenticated,
        capabilities: AuthCapabilities(
          user: AuthUser(id: '1', email: 'a@b.com', role: 'doctor'),
          workspace: 'doctor',
          defaultWorkspace: 'doctor',
          permissions: [],
          features: [],
        ),
      );
      expect(redirectForAuth(state, '/login'), '/doctor/home');
    });

    test('session expired redirects', () {
      const state = AuthState(status: AuthStatus.sessionExpired);
      expect(redirectForAuth(state, '/doctor/home'), '/session-expired');
    });

    test('requires organization selection', () {
      const state = AuthState(status: AuthStatus.requiresOrganization);
      expect(redirectForAuth(state, '/login'), '/select-organization');
    });
  });
}
