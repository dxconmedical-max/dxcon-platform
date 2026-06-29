import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config/api_config.dart';

class AuthService {
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final url = Uri.parse("${ApiConfig.baseUrl}/api/v1/auth/login");

    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "email": email,
        "password": password,
      }),
    );

    if (!response.headers.toString().contains("application/json")) {
      throw Exception("Server returned non-JSON: ${response.statusCode}");
    }

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data["error"] ?? "Login failed");
    }

    return data;
  }
}
