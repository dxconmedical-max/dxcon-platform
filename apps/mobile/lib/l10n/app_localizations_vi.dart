// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Vietnamese (`vi`).
class AppLocalizationsVi extends AppLocalizations {
  AppLocalizationsVi([String locale = 'vi']) : super(locale);

  @override
  String get appTitle => 'DxCon';

  @override
  String get loginTitle => 'Đăng nhập';

  @override
  String get emailLabel => 'Email';

  @override
  String get passwordLabel => 'Mật khẩu';

  @override
  String get loginButton => 'Đăng nhập';

  @override
  String get logoutButton => 'Đăng xuất';

  @override
  String get sessionExpired => 'Phiên đăng nhập đã hết hạn';

  @override
  String get serviceUnavailable => 'Dịch vụ tạm thời không khả dụng';

  @override
  String get forbidden => 'Bạn không có quyền truy cập';

  @override
  String get selectOrganization => 'Chọn tổ chức';

  @override
  String get offline => 'Không có kết nối mạng';

  @override
  String get syncPending => 'Đang chờ đồng bộ';

  @override
  String get placeholderNotImplemented => 'Chức năng đang được phát triển';
}
