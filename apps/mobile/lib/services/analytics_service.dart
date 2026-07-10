import 'package:dxcon_mobile/config/environment.dart';

/// Privacy-aware analytics — no PHI or raw identifiers.
abstract class AnalyticsProvider {
  void trackScreen(String name);
  void trackEvent(String category, {Map<String, String>? properties});
}

class NoOpAnalyticsProvider implements AnalyticsProvider {
  @override
  void trackScreen(String name) {}

  @override
  void trackEvent(String category, {Map<String, String>? properties}) {}
}

class ConfigurableAnalyticsProvider implements AnalyticsProvider {
  ConfigurableAnalyticsProvider({AnalyticsProvider? delegate})
    : _delegate = delegate ?? NoOpAnalyticsProvider(),
      _enabled = AppEnvironment.current.analyticsEnabled;

  final AnalyticsProvider _delegate;
  final bool _enabled;

  @override
  void trackScreen(String name) {
    if (!_enabled) return;
    _delegate.trackScreen(name);
  }

  @override
  void trackEvent(String category, {Map<String, String>? properties}) {
    if (!_enabled) return;
    _delegate.trackEvent(category, properties: properties);
  }
}
