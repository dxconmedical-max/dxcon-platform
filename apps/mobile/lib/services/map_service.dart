/// Provider-agnostic map abstraction — no hardcoded map vendor.
abstract class MapProvider {
  Future<void> showMap({
    required double latitude,
    required double longitude,
    String? label,
  });

  Future<void> showRoute({
    required double fromLat,
    required double fromLng,
    required double toLat,
    required double toLng,
  });

  Future<void> launchExternalNavigation({
    required double latitude,
    required double longitude,
  });
}

class PlaceholderMapProvider implements MapProvider {
  @override
  Future<void> showMap({
    required double latitude,
    required double longitude,
    String? label,
  }) async {}

  @override
  Future<void> showRoute({
    required double fromLat,
    required double fromLng,
    required double toLat,
    required double toLng,
  }) async {}

  @override
  Future<void> launchExternalNavigation({
    required double latitude,
    required double longitude,
  }) async {}
}
