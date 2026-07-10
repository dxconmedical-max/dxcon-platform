// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'DxCon';

  @override
  String get loginTitle => 'Sign in';

  @override
  String get emailLabel => 'Email';

  @override
  String get passwordLabel => 'Password';

  @override
  String get loginButton => 'Sign in';

  @override
  String get logoutButton => 'Sign out';

  @override
  String get sessionExpired => 'Session expired';

  @override
  String get serviceUnavailable => 'Service temporarily unavailable';

  @override
  String get forbidden => 'Access denied';

  @override
  String get selectOrganization => 'Select organization';

  @override
  String get offline => 'No network connection';

  @override
  String get syncPending => 'Sync pending';

  @override
  String get placeholderNotImplemented => 'Feature in development';
}
