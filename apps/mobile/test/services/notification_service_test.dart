import 'package:flutter_test/flutter_test.dart';

import 'package:dxcon_mobile/services/notification_service.dart';

void main() {
  test('push blocked without firebase configuration', () {
    final service = NotificationService();
    expect(service.status, PushNotificationStatus.blockedByConfiguration);
  });

  test('validates notification deep link payload', () {
    final service = NotificationService();
    expect(
      service.validateDeepLinkPayload({'type': 'booking', 'id': '1'}),
      isTrue,
    );
    expect(service.validateDeepLinkPayload({'type': 'invalid'}), isFalse);
  });
}
