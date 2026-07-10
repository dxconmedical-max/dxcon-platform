import 'package:dxcon_mobile/models/auth_models.dart';

bool can(AuthCapabilities? capabilities, String permission) {
  if (capabilities == null) return false;
  final perms = capabilities.permissions;
  if (perms.contains('*')) return true;
  return perms.contains(permission);
}

bool canAny(AuthCapabilities? capabilities, List<String> permissions) {
  return permissions.any((p) => can(capabilities, p));
}

bool canAll(AuthCapabilities? capabilities, List<String> permissions) {
  return permissions.every((p) => can(capabilities, p));
}

bool hasFeature(AuthCapabilities? capabilities, String feature) {
  if (capabilities == null) return false;
  return capabilities.features.contains(feature);
}

bool isWorkspace(AuthCapabilities? capabilities, String workspace) {
  return (capabilities?.workspace ?? '').toLowerCase() ==
      workspace.toLowerCase();
}

bool isOrganizationType(AuthCapabilities? capabilities, String orgType) {
  return (capabilities?.organization?.organizationType ?? '').toUpperCase() ==
      orgType.toUpperCase();
}
