import 'package:dxcon_mobile/core/api/api_client.dart';

class CollectorApiRepository {
  CollectorApiRepository(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> dashboard(String collectorId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/collector/dashboard',
      queryParameters: {'collector_id': collectorId},
      parser: (json) => json as Map<String, dynamic>,
    );
    return res['data'] as Map<String, dynamic>? ?? {};
  }

  Future<List<dynamic>> jobs(String collectorId, {String? status}) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/collector/jobs',
      queryParameters: {
        'collector_id': collectorId,
        if (status != null) 'status': status,
      },
      parser: (json) => json as Map<String, dynamic>,
    );
    return res['data'] as List<dynamic>? ?? [];
  }

  Future<Map<String, dynamic>> jobDetail(String collectorId, String assignmentId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/collector/jobs/$assignmentId',
      queryParameters: {'collector_id': collectorId},
      parser: (json) => json as Map<String, dynamic>,
    );
    return res['data'] as Map<String, dynamic>? ?? {};
  }

  Future<void> rejectAssignment(
    String collectorId,
    String assignmentId,
    String reason,
  ) async {
    await _api.post(
      '/api/v1/mobile/collector/assignments/$assignmentId/reject',
      body: {'collector_id': collectorId, 'reason': reason},
    );
  }

  Future<void> acceptAssignment(String assignmentId, String collectorId) async {
    await _api.post(
      '/api/v1/collector-operations/assignments/$assignmentId/accept',
      body: {'collector_id': collectorId},
    );
  }

  Future<void> checkIn(String collectorId, Map<String, dynamic> payload) async {
    await _api.post(
      '/api/v1/collector-operations/collectors/$collectorId/check-in',
      body: payload,
    );
  }

  Future<void> recordPickup(String bookingId, Map<String, dynamic> payload) async {
    await _api.post('/api/v1/collector-operations/bookings/$bookingId/pickup', body: payload);
  }

  Future<void> recordHandover(Map<String, dynamic> payload) async {
    await _api.post('/api/v1/collector-operations/handovers', body: payload);
  }

  Future<void> syncOffline(String collectorId, List<Map<String, dynamic>> events) async {
    await _api.post(
      '/api/v1/collector-operations/collectors/$collectorId/offline/sync',
      body: {'events': events},
    );
  }
}
