import 'package:dxcon_mobile/core/api/api_client.dart';

class PatientApiRepository {
  PatientApiRepository(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> dashboard() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/patient/dashboard',
      parser: _unwrap,
    );
    return res;
  }

  Future<List<dynamic>> bookings() async {
    final res = await _api.get<dynamic>('/api/v1/mobile/patient/bookings');
    if (res is Map<String, dynamic>) {
      return res['data'] as List<dynamic>? ?? [];
    }
    return [];
  }

  Future<Map<String, dynamic>> bookingDetail(String bookingId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/patient/bookings/$bookingId',
      parser: _unwrap,
    );
    return res['data'] as Map<String, dynamic>? ?? res;
  }

  Future<Map<String, dynamic>> collectorTracking(String bookingId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/patient/bookings/$bookingId/collector-tracking',
      parser: _unwrap,
    );
    return res['data'] as Map<String, dynamic>? ?? res;
  }

  Future<List<dynamic>> releasedResults() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/patient/results',
      parser: (json) => json as Map<String, dynamic>,
    );
    return res['data'] as List<dynamic>? ?? [];
  }

  Future<Map<String, dynamic>> resultDetail(String reportCode) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/patient/results/$reportCode',
      parser: _unwrap,
    );
    return res['data'] as Map<String, dynamic>? ?? res;
  }

  Future<List<dynamic>> notifications() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/patient/notifications',
      parser: (json) => json as Map<String, dynamic>,
    );
    return res['data'] as List<dynamic>? ?? [];
  }

  Future<List<dynamic>> familyProfiles() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/api/v1/mobile/patient/family-profiles',
      parser: (json) => json as Map<String, dynamic>,
    );
    return res['data'] as List<dynamic>? ?? [];
  }

  Map<String, dynamic> _unwrap(dynamic json) {
    if (json is Map<String, dynamic> && json['data'] != null) {
      return json['data'] as Map<String, dynamic>;
    }
    return json as Map<String, dynamic>;
  }
}
