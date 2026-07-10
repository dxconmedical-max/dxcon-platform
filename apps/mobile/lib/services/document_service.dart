/// Secure document handling — clinical PDFs expire from cache by default.
class DocumentService {
  static const defaultCacheTtl = Duration(hours: 24);

  bool isExpired(DateTime downloadedAt, {Duration? ttl}) {
    return DateTime.now().toUtc().isAfter(
      downloadedAt.add(ttl ?? defaultCacheTtl),
    );
  }
}
