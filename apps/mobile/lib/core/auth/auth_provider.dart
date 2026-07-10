import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:dxcon_mobile/core/api/api_client.dart';
import 'package:dxcon_mobile/core/auth/auth_repository.dart';
import 'package:dxcon_mobile/core/auth/auth_state.dart';
import 'package:dxcon_mobile/core/auth/token_session.dart';
import 'package:dxcon_mobile/core/errors/api_error.dart';
import 'package:dxcon_mobile/core/storage/secure_token_storage.dart';

final secureStorageProvider = Provider<SecureTokenStorage>((ref) {
  return SecureTokenStorage();
});

final tokenSessionProvider = Provider<TokenSession>((ref) => TokenSession());

final apiClientProvider = Provider<ApiClient>((ref) {
  final session = ref.watch(tokenSessionProvider);
  return ApiClient(
    tokenProvider: () => session.accessToken,
    refreshHandler: () async => await session.refreshHandler?.call(),
    organizationIdProvider: () => session.organizationId,
  );
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    apiClient: ref.watch(apiClientProvider),
    secureStorage: ref.watch(secureStorageProvider),
  );
});

final authNotifierProvider = StateNotifierProvider<AuthNotifier, AuthState>((
  ref,
) {
  final notifier = AuthNotifier(
    repository: ref.watch(authRepositoryProvider),
    storage: ref.watch(secureStorageProvider),
    session: ref.watch(tokenSessionProvider),
  );
  ref.watch(tokenSessionProvider).refreshHandler = notifier.refreshToken;
  return notifier;
});

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier({
    required AuthRepository repository,
    required SecureTokenStorage storage,
    required TokenSession session,
  }) : _repository = repository,
       _storage = storage,
       _session = session,
       super(const AuthState());

  final AuthRepository _repository;
  final SecureTokenStorage _storage;
  final TokenSession _session;

  Future<void> bootstrap() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final hasSession = await _repository.restoreSession();
      if (!hasSession) {
        state = state.copyWith(
          status: AuthStatus.unauthenticated,
          isLoading: false,
        );
        return;
      }
      _session.accessToken = await _storage.readAccessToken();
      _session.organizationId = await _storage.readActiveOrganization();
      final me = await _repository.fetchMe();
      if (!me.user.isActive) {
        await logout();
        return;
      }
      state = state.copyWith(memberships: me.memberships, isLoading: false);
      if (me.requiresOrganizationSelection ||
          (me.activeOrganizationId == null && me.memberships.length > 1)) {
        state = state.copyWith(status: AuthStatus.requiresOrganization);
        return;
      }
      final caps = await _repository.fetchCapabilities(
        organizationId: me.activeOrganizationId ?? _session.organizationId,
      );
      _session.organizationId =
          caps.organization?.id ?? _session.organizationId;
      state = state.copyWith(
        status: AuthStatus.authenticated,
        capabilities: caps,
      );
    } on ApiError catch (e) {
      await _handleApiError(e);
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final login = await _repository.login(email: email, password: password);
      _session.accessToken = login.accessToken;
      final me = await _repository.fetchMe();
      state = state.copyWith(memberships: me.memberships);
      final activeMemberships = me.memberships
          .where((m) => m.isActiveMembership)
          .toList();
      if (me.requiresOrganizationSelection || activeMemberships.length > 1) {
        state = state.copyWith(
          status: AuthStatus.requiresOrganization,
          isLoading: false,
        );
        return;
      }
      final orgId =
          me.activeOrganizationId ??
          (activeMemberships.isNotEmpty
              ? activeMemberships.first.organizationId
              : null);
      final caps = await _repository.fetchCapabilities(organizationId: orgId);
      _session.organizationId = caps.organization?.id;
      state = state.copyWith(
        status: AuthStatus.authenticated,
        capabilities: caps,
        isLoading: false,
      );
    } on ApiError catch (e) {
      state = state.copyWith(lastError: e, isLoading: false);
      rethrow;
    }
  }

  Future<void> selectOrganization(String organizationId) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final membership = state.memberships.firstWhere(
        (m) => m.organizationId == organizationId,
        orElse: () => throw const ApiError(
          message: 'Invalid membership',
          statusCode: 403,
          code: 'INVALID_MEMBERSHIP',
        ),
      );
      if (!membership.isActiveMembership) {
        throw const ApiError(
          message: 'Membership is disabled',
          statusCode: 403,
          code: 'MEMBERSHIP_DISABLED',
        );
      }
      final caps = await _repository.switchOrganization(organizationId);
      _session.organizationId = organizationId;
      state = state.copyWith(
        status: AuthStatus.authenticated,
        capabilities: caps,
        isLoading: false,
      );
    } on ApiError catch (e) {
      state = state.copyWith(lastError: e, isLoading: false);
      rethrow;
    }
  }

  Future<String?> refreshToken() async {
    try {
      final token = await _repository.refreshAccessToken();
      _session.accessToken = token;
      return token;
    } catch (_) {
      state = state.copyWith(status: AuthStatus.sessionExpired);
      return null;
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    _session.accessToken = null;
    _session.organizationId = null;
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  Future<void> _handleApiError(ApiError e) async {
    if (e.isUnauthorized) {
      await logout();
      state = state.copyWith(
        status: AuthStatus.sessionExpired,
        lastError: e,
        isLoading: false,
      );
      return;
    }
    if (e.isServerError || e.isNetworkError) {
      state = state.copyWith(
        status: AuthStatus.serviceUnavailable,
        lastError: e,
        isLoading: false,
      );
      return;
    }
    state = state.copyWith(
      status: AuthStatus.unauthenticated,
      lastError: e,
      isLoading: false,
    );
  }
}
