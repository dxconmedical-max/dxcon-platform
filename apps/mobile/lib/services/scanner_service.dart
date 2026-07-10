import 'package:url_launcher/url_launcher.dart';

/// Validates scanned payloads — never auto-executes raw URLs.
class ScannerService {
  const ScannerService();

  ScanValidationResult validate(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty) {
      return const ScanValidationResult(valid: false, reason: 'Empty scan');
    }
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return ScanValidationResult(
        valid: false,
        reason: 'URL scans require confirmation',
        payloadType: ScanPayloadType.url,
        rawPayload: trimmed,
      );
    }
    if (trimmed.startsWith('dxcon://')) {
      return ScanValidationResult(
        valid: true,
        payloadType: ScanPayloadType.deepLink,
        rawPayload: trimmed,
      );
    }
    if (RegExp(r'^[A-Z0-9\-]{4,64}$').hasMatch(trimmed)) {
      return ScanValidationResult(
        valid: true,
        payloadType: ScanPayloadType.barcode,
        rawPayload: trimmed,
      );
    }
    return ScanValidationResult(
      valid: true,
      payloadType: ScanPayloadType.unknown,
      rawPayload: trimmed,
    );
  }

  Future<bool> confirmAndLaunchUrl(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) return false;
    if (!['http', 'https'].contains(uri.scheme)) return false;
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}

enum ScanPayloadType { barcode, deepLink, url, unknown }

class ScanValidationResult {
  const ScanValidationResult({
    required this.valid,
    this.reason,
    this.payloadType = ScanPayloadType.unknown,
    this.rawPayload,
  });

  final bool valid;
  final String? reason;
  final ScanPayloadType payloadType;
  final String? rawPayload;
}
