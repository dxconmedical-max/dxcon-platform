enum LocationPermissionState {
  granted,
  denied,
  deniedForever,
  serviceDisabled,
  unknown,
}

/// GPS foundation — collect only when operationally required.
class LocationService {
  const LocationService();

  LocationPermissionState mapPermission(dynamic status) {
    final name = status.toString().toLowerCase();
    if (name.contains('granted')) return LocationPermissionState.granted;
    if (name.contains('deniedforever')) {
      return LocationPermissionState.deniedForever;
    }
    if (name.contains('denied')) return LocationPermissionState.denied;
    return LocationPermissionState.unknown;
  }
}
