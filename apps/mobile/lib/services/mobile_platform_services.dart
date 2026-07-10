import 'package:dxcon_mobile/config/environment.dart';
import 'package:dxcon_mobile/core/api/api_client.dart';
import 'package:uuid/uuid.dart';

class DeviceRegistrationService {
  DeviceRegistrationService(this._api);

  final ApiClient _api;

  Future<void> register({
    required String platform,
    required String appVersion,
    required String workspace,
    String? notificationToken,
  }) async {
    await _api.post(
      '/api/v1/mobile/devices',
      body: {
        'device_reference': 'dxcon-${const Uuid().v4()}',
        'platform': platform,
        'app_version': appVersion,
        'workspace': workspace,
        if (notificationToken != null) 'notification_token': notificationToken,
      },
    );
  }

  Future<Map<String, dynamic>> appConfig() =>
      _api.get<Map<String, dynamic>>('/api/v1/mobile/app-config');
}

class MobileAuditService {
  MobileAuditService(this._api);

  final ApiClient _api;

  Future<void> recordEvents(List<Map<String, dynamic>> events) async {
    if (events.isEmpty) return;
    await _api.post('/api/v1/mobile/audit/events', body: {'events': events});
  }
}

class RealtimeUpdateService {
  RealtimeUpdateService({this.pollInterval = const Duration(seconds: 30)});

  final Duration pollInterval;
  bool _polling = false;

  void startPolling(Future<void> Function() onTick) {
    if (_polling) return;
    _polling = true;
    Future<void>.microtask(() async {
      while (_polling) {
        try {
          await onTick();
        } catch (_) {}
        await Future<void>.delayed(pollInterval);
      }
    });
  }

  void stop() => _polling = false;
}

bool get isDemoMode => AppEnvironment.current.demoMode;
