/// In-memory session holder to avoid circular provider dependencies.
class TokenSession {
  String? accessToken;
  String? organizationId;
  Future<String?> Function()? refreshHandler;
}
