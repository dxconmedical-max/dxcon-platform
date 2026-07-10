import 'package:dxcon_mobile/core/api/api_client.dart';

class MarketplaceRepository {
  MarketplaceRepository(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> search({
    String? q,
    String? city,
    double? minPrice,
    double? maxPrice,
    bool? homeCollection,
    int page = 1,
  }) async {
    final query = <String, dynamic>{
      if (q != null && q.isNotEmpty) 'q': q,
      if (city != null && city.isNotEmpty) 'city': city,
      if (minPrice != null) 'min_price': minPrice,
      if (maxPrice != null) 'max_price': maxPrice,
      if (homeCollection == true) 'home_collection': 'true',
      'page': page,
      'per_page': 20,
    };
    return _api.get<Map<String, dynamic>>(
      '/api/v1/marketplace/catalog/search',
      queryParameters: query,
    );
  }

  Future<Map<String, dynamic>> providerProfile(String providerId) =>
      _api.get('/api/v1/marketplace/catalog/providers/$providerId');

  Future<Map<String, dynamic>> compare(List<String> listingIds) => _api.post(
        '/api/v1/marketplace/catalog/compare',
        body: {'listing_ids': listingIds},
      );

  Future<Map<String, dynamic>> quote(String listingId, {String? promotionCode, double distanceKm = 0}) =>
      _api.post(
        '/api/v1/marketplace/catalog/quote',
        body: {
          'listing_id': listingId,
          if (promotionCode != null) 'promotion_code': promotionCode,
          'distance_km': distanceKm,
        },
      );

  Future<Map<String, dynamic>> checkServiceability(
    String providerId,
    double lat,
    double lng,
  ) =>
      _api.post(
        '/api/v1/marketplace/catalog/serviceability',
        body: {'provider_id': providerId, 'lat': lat, 'lng': lng},
      );

  Future<Map<String, dynamic>> createBooking(
    Map<String, dynamic> payload, {
    required String idempotencyKey,
  }) =>
      _api.post(
        '/api/v1/marketplace/v2/bookings',
        body: payload,
        idempotencyKey: idempotencyKey,
      );

  Future<Map<String, dynamic>> createQrPayment(String bookingId) => _api.post(
        '/api/v1/marketplace/v2/payments/qr',
        body: {'booking_id': bookingId},
      );

  Future<Map<String, dynamic>> paymentStatus(String paymentReference) =>
      _api.get('/api/v1/marketplace/v2/payments/$paymentReference/status');
}
