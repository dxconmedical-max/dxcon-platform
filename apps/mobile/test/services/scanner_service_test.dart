import 'package:flutter_test/flutter_test.dart';

import 'package:dxcon_mobile/core/security/security_service.dart';
import 'package:dxcon_mobile/services/scanner_service.dart';

void main() {
  test('rejects open redirect targets', () {
    const security = SecurityService();
    expect(security.isOpenRedirect('https://evil.com/phish'), isTrue);
    expect(security.isOpenRedirect('/patient/home'), isFalse);
    expect(security.isOpenRedirect('dxcon://booking/1'), isFalse);
  });

  test('QR validation blocks raw URLs without confirmation path', () {
    const scanner = ScannerService();
    final result = scanner.validate('https://example.com');
    expect(result.valid, isFalse);
    expect(result.payloadType, ScanPayloadType.url);
  });

  test('accepts dxcon deep links and barcodes', () {
    const scanner = ScannerService();
    expect(scanner.validate('dxcon://booking/abc').valid, isTrue);
    expect(scanner.validate('ORD-12345').valid, isTrue);
  });
}
