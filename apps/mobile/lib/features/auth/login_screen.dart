import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:dxcon_mobile/config/environment.dart';
import 'package:dxcon_mobile/core/auth/auth_provider.dart';
import 'package:dxcon_mobile/core/auth/auth_state.dart';
import 'package:dxcon_mobile/core/errors/api_error.dart';
import 'package:dxcon_mobile/design_system/theme.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _error = null);
    try {
      await ref
          .read(authNotifierProvider.notifier)
          .login(_emailController.text.trim(), _passwordController.text);
      if (!mounted) return;
      final state = ref.read(authNotifierProvider);
      if (state.status == AuthStatus.requiresOrganization) {
        context.go('/select-organization');
      }
    } on ApiError catch (e) {
      setState(() => _error = e.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authNotifierProvider);
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(DxSpacing.lg),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'DxCon',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      color: DxColors.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: DxSpacing.sm),
                  Text(
                    'Đăng nhập',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: DxSpacing.lg),
                  TextField(
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.email],
                    decoration: const InputDecoration(labelText: 'Email'),
                  ),
                  const SizedBox(height: DxSpacing.md),
                  TextField(
                    controller: _passwordController,
                    obscureText: true,
                    autofillHints: const [AutofillHints.password],
                    decoration: const InputDecoration(labelText: 'Mật khẩu'),
                    onSubmitted: (_) => _submit(),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: DxSpacing.md),
                    Text(
                      _error!,
                      style: const TextStyle(color: DxColors.error),
                    ),
                  ],
                  const SizedBox(height: DxSpacing.lg),
                  ElevatedButton(
                    onPressed: auth.isLoading ? null : _submit,
                    child: auth.isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Đăng nhập'),
                  ),
                  if (!AppEnvironment.current.isProduction) ...[
                    const SizedBox(height: DxSpacing.md),
                    Text(
                      'Env: ${AppEnvironment.current.name}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
