/// Firebase Cloud Messaging foundation.
enum PushNotificationStatus { ready, blockedByConfiguration, permissionDenied }

enum NotificationCategory {
  booking,
  collector,
  payment,
  result,
  report,
  appointment,
  incident,
  system,
}

class NotificationService {
  PushNotificationStatus get status =>
      PushNotificationStatus.blockedByConfiguration;

  Future<String?> registerDeviceToken({required String organizationId}) async {
    // BLOCKED_BY_CONFIGURATION until google-services.json / GoogleService-Info.plist provided.
    return null;
  }

  Future<void> revokeDeviceToken() async {}

  bool validateDeepLinkPayload(Map<String, dynamic> data) {
    final type = data['type']?.toString();
    return type != null &&
        NotificationCategory.values.any((c) => c.name == type);
  }
}
