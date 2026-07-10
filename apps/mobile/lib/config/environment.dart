/// Compile-time environment configuration via --dart-define.
class AppEnvironment {
  const AppEnvironment({
    required this.name,
    required this.apiBaseUrl,
    required this.publicSiteUrl,
    required this.webAppUrl,
    required this.demoMode,
    this.sentryDsn = '',
    this.analyticsEnabled = false,
    this.apiCompatibilityVersion = 'v1',
  });

  final String name;
  final String apiBaseUrl;
  final String publicSiteUrl;
  final String webAppUrl;
  final bool demoMode;
  final String sentryDsn;
  final bool analyticsEnabled;
  final String apiCompatibilityVersion;

  bool get isProduction => name == 'production';

  static const AppEnvironment current = AppEnvironment(
    name: String.fromEnvironment('APP_ENV', defaultValue: 'production'),
    apiBaseUrl: String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'https://api.dxcon.com.vn',
    ),
    publicSiteUrl: String.fromEnvironment(
      'PUBLIC_SITE_URL',
      defaultValue: 'https://dxcon.com.vn',
    ),
    webAppUrl: String.fromEnvironment(
      'WEB_APP_URL',
      defaultValue: 'https://app.dxcon.com.vn',
    ),
    demoMode: bool.fromEnvironment('DEMO_MODE', defaultValue: false),
    sentryDsn: String.fromEnvironment('SENTRY_DSN', defaultValue: ''),
    analyticsEnabled: bool.fromEnvironment(
      'ANALYTICS_ENABLED',
      defaultValue: false,
    ),
    apiCompatibilityVersion: String.fromEnvironment(
      'API_COMPAT_VERSION',
      defaultValue: 'v1',
    ),
  );
}
