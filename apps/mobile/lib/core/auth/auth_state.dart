import 'package:equatable/equatable.dart';

import 'package:dxcon_mobile/core/errors/api_error.dart';
import 'package:dxcon_mobile/models/auth_models.dart';

enum AuthStatus {
  unknown,
  unauthenticated,
  authenticated,
  requiresOrganization,
  sessionExpired,
  serviceUnavailable,
}

class AuthState extends Equatable {
  const AuthState({
    this.status = AuthStatus.unknown,
    this.capabilities,
    this.memberships = const [],
    this.lastError,
    this.isLoading = false,
  });

  final AuthStatus status;
  final AuthCapabilities? capabilities;
  final List<Membership> memberships;
  final ApiError? lastError;
  final bool isLoading;

  AuthState copyWith({
    AuthStatus? status,
    AuthCapabilities? capabilities,
    List<Membership>? memberships,
    ApiError? lastError,
    bool? isLoading,
    bool clearError = false,
  }) {
    return AuthState(
      status: status ?? this.status,
      capabilities: capabilities ?? this.capabilities,
      memberships: memberships ?? this.memberships,
      lastError: clearError ? null : (lastError ?? this.lastError),
      isLoading: isLoading ?? this.isLoading,
    );
  }

  @override
  List<Object?> get props => [
    status,
    capabilities,
    memberships,
    lastError,
    isLoading,
  ];
}
