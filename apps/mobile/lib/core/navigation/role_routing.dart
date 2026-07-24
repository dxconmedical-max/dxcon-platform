/// Maps capability workspace to Phase 1 shell home route.
String workspaceHomeFor(String workspace) {
  switch (workspace.toLowerCase().trim()) {
    case 'collector':
      return '/collector/home';
    case 'doctor':
      return '/doctor/home';
    case 'lab':
    case 'laboratory':
      return '/lab/incoming';
    case 'clinic':
    case 'clinic_ops':
    case 'reception':
      return '/clinic/home';
    case 'executive':
      return '/executive/home';
    case 'admin':
    case 'platform_admin':
      return '/admin/home';
    case 'patient':
    default:
      return '/patient/home';
  }
}

/// Whether [location] belongs to the given workspace shell.
bool locationMatchesWorkspace(String location, String workspace) {
  final home = workspaceHomeFor(workspace);
  final prefix = home.split('/').take(2).join('/'); // e.g. /patient
  if (prefix.isEmpty || prefix == '/') return false;
  return location == home || location.startsWith('$prefix/');
}
