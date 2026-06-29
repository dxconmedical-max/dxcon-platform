import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/config/api_config.dart';

class CollectorService {
  static Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse("${ApiConfig.baseUrl}$path").replace(queryParameters: query);
  }

  static Future<List<dynamic>> listShipments({String? collectorId}) async {
    final query = collectorId == null ? null : {"collector_id": collectorId};
    final response = await http.get(_uri("/api/v1/collector/shipments", query));

    final data = jsonDecode(response.body) as Map<String, dynamic>;

    if (response.statusCode != 200) {
      throw Exception(data["error"] ?? "Failed to load shipments");
    }

    return (data["shipments"] as List<dynamic>? ?? []);
  }

  static Future<Map<String, dynamic>> acceptShipment({
    required String shipmentId,
    String? collectorId,
    String? actor,
  }) async {
    final response = await http.post(
      _uri("/api/v1/collector/shipments/$shipmentId/accept"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "collector_id": collectorId,
        "actor": actor,
        "latitude": "0.0",
        "longitude": "0.0",
      }),
    );

    final data = jsonDecode(response.body) as Map<String, dynamic>;

    if (response.statusCode != 200) {
      throw Exception(data["error"] ?? "Accept shipment failed");
    }

    return data;
  }

  static Future<Map<String, dynamic>> startTrip({
    required String shipmentId,
    String? collectorId,
    String? actor,
  }) async {
    final response = await http.post(
      _uri("/api/v1/collector/shipments/$shipmentId/start-trip"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "collector_id": collectorId,
        "actor": actor,
        "latitude": "0.0",
        "longitude": "0.0",
      }),
    );

    final data = jsonDecode(response.body) as Map<String, dynamic>;

    if (response.statusCode != 200) {
      throw Exception(data["error"] ?? "Start trip failed");
    }

    return data;
  }
}
