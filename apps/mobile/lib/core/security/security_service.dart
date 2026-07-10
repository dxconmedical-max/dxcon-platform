import 'package:dxcon_mobile/config/environment.dart';

/// App security foundation — limitations documented in MOBILE_SECURITY.md.
class SecurityService {
  const SecurityService();

  bool get demoModeDisabled => !AppEnvironment.current.demoMode;

  bool isDeepLinkAllowed(String uri) {
    if (uri.startsWith('dxcon://')) return true;
    if (uri.startsWith('${AppEnvironment.current.webAppUrl}/')) return true;
    return false;
  }

  bool isOpenRedirect(String target) {
    if (target.startsWith('dxcon://')) return false;
    if (target.startsWith(AppEnvironment.current.webAppUrl)) return false;
    if (target.startsWith('/')) return false;
    return target.startsWith('http');
  }
}
