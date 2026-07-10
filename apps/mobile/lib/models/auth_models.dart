import 'package:equatable/equatable.dart';

class AuthUser extends Equatable {
  const AuthUser({
    required this.id,
    required this.email,
    required this.role,
    this.phone,
    this.organizationId,
    this.isActive = true,
  });

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
    id: json['id']?.toString() ?? '',
    email: json['email']?.toString() ?? '',
    role: json['role']?.toString() ?? '',
    phone: json['phone']?.toString(),
    organizationId: json['organization_id']?.toString(),
    isActive: json['is_active'] as bool? ?? true,
  );

  final String id;
  final String email;
  final String role;
  final String? phone;
  final String? organizationId;
  final bool isActive;

  @override
  List<Object?> get props => [id, email, role, phone, organizationId, isActive];
}

class Organization extends Equatable {
  const Organization({
    required this.id,
    required this.organizationCode,
    required this.organizationName,
    required this.organizationType,
    required this.status,
  });

  factory Organization.fromJson(Map<String, dynamic> json) => Organization(
    id: json['id']?.toString() ?? '',
    organizationCode: json['organization_code']?.toString() ?? '',
    organizationName: json['organization_name']?.toString() ?? '',
    organizationType: json['organization_type']?.toString() ?? '',
    status: json['status']?.toString() ?? '',
  );

  final String id;
  final String organizationCode;
  final String organizationName;
  final String organizationType;
  final String status;

  bool get isActive => status.toUpperCase() == 'ACTIVE';

  @override
  List<Object?> get props => [
    id,
    organizationCode,
    organizationName,
    organizationType,
    status,
  ];
}

class Membership extends Equatable {
  const Membership({
    required this.organizationId,
    required this.organizationName,
    required this.organizationType,
    required this.organizationCode,
    required this.organizationStatus,
    required this.roleCode,
    required this.membershipStatus,
    required this.defaultWorkspace,
    this.membershipId,
    this.departmentId,
    this.teamId,
  });

  factory Membership.fromJson(Map<String, dynamic> json) => Membership(
    membershipId: json['membership_id']?.toString(),
    organizationId: json['organization_id']?.toString() ?? '',
    organizationName: json['organization_name']?.toString() ?? '',
    organizationType: json['organization_type']?.toString() ?? '',
    organizationCode: json['organization_code']?.toString() ?? '',
    organizationStatus: json['organization_status']?.toString() ?? '',
    roleCode: json['role_code']?.toString() ?? '',
    membershipStatus: json['membership_status']?.toString() ?? '',
    defaultWorkspace: json['default_workspace']?.toString() ?? 'patient',
    departmentId: json['department_id']?.toString(),
    teamId: json['team_id']?.toString(),
  );

  final String? membershipId;
  final String organizationId;
  final String organizationName;
  final String organizationType;
  final String organizationCode;
  final String organizationStatus;
  final String roleCode;
  final String membershipStatus;
  final String defaultWorkspace;
  final String? departmentId;
  final String? teamId;

  bool get isActiveMembership =>
      membershipStatus.toUpperCase() == 'ACTIVE' &&
      organizationStatus.toUpperCase() == 'ACTIVE';

  @override
  List<Object?> get props => [
    membershipId,
    organizationId,
    organizationName,
    organizationType,
    organizationCode,
    organizationStatus,
    roleCode,
    membershipStatus,
    defaultWorkspace,
  ];
}

class AuthCapabilities extends Equatable {
  const AuthCapabilities({
    required this.user,
    this.organization,
    required this.workspace,
    required this.defaultWorkspace,
    required this.permissions,
    required this.features,
    this.membershipId,
    this.membershipStatus,
    this.roleCode,
    this.tokenExpiresAt,
  });

  factory AuthCapabilities.fromJson(Map<String, dynamic> json) {
    final membership = json['membership'] as Map<String, dynamic>? ?? {};
    return AuthCapabilities(
      user: AuthUser.fromJson(json['user'] as Map<String, dynamic>? ?? {}),
      organization: json['organization'] != null
          ? Organization.fromJson(json['organization'] as Map<String, dynamic>)
          : null,
      workspace: json['workspace']?.toString() ?? 'patient',
      defaultWorkspace: json['default_workspace']?.toString() ?? 'patient',
      permissions: (json['permissions'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      features: (json['features'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      membershipId: membership['membership_id']?.toString(),
      membershipStatus: membership['membership_status']?.toString(),
      roleCode: membership['role_code']?.toString(),
      tokenExpiresAt: json['token_expires_at']?.toString(),
    );
  }

  final AuthUser user;
  final Organization? organization;
  final String workspace;
  final String defaultWorkspace;
  final List<String> permissions;
  final List<String> features;
  final String? membershipId;
  final String? membershipStatus;
  final String? roleCode;
  final String? tokenExpiresAt;

  @override
  List<Object?> get props => [
    user,
    organization,
    workspace,
    defaultWorkspace,
    permissions,
    features,
    membershipId,
    membershipStatus,
    roleCode,
    tokenExpiresAt,
  ];
}

class LoginResponse extends Equatable {
  const LoginResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.user,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) => LoginResponse(
    accessToken: (json['access_token'] ?? json['token'])?.toString() ?? '',
    refreshToken: json['refresh_token']?.toString() ?? '',
    user: AuthUser.fromJson(json['user'] as Map<String, dynamic>? ?? json),
  );

  final String accessToken;
  final String refreshToken;
  final AuthUser user;

  @override
  List<Object?> get props => [accessToken, refreshToken, user];
}

class MeResponse extends Equatable {
  const MeResponse({
    required this.user,
    required this.memberships,
    this.activeOrganizationId,
    this.requiresOrganizationSelection = false,
  });

  factory MeResponse.fromJson(Map<String, dynamic> json) => MeResponse(
    user: AuthUser.fromJson(json['user'] as Map<String, dynamic>? ?? {}),
    activeOrganizationId: json['active_organization_id']?.toString(),
    requiresOrganizationSelection:
        json['requires_organization_selection'] as bool? ?? false,
    memberships: (json['memberships'] as List<dynamic>? ?? [])
        .map((e) => Membership.fromJson(e as Map<String, dynamic>))
        .toList(),
  );

  final AuthUser user;
  final String? activeOrganizationId;
  final bool requiresOrganizationSelection;
  final List<Membership> memberships;

  @override
  List<Object?> get props => [
    user,
    activeOrganizationId,
    requiresOrganizationSelection,
    memberships,
  ];
}
