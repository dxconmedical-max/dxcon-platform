import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'package:dxcon_mobile/core/auth/auth_provider.dart';
import 'package:dxcon_mobile/core/navigation/app_router.dart';
import 'package:dxcon_mobile/design_system/theme.dart';
import 'package:dxcon_mobile/l10n/app_localizations.dart';

class DxConApp extends ConsumerStatefulWidget {
  const DxConApp({super.key});

  @override
  ConsumerState<DxConApp> createState() => _DxConAppState();
}

class _DxConAppState extends ConsumerState<DxConApp> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(authNotifierProvider.notifier).bootstrap());
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'DxCon',
      theme: DxTheme.light(),
      darkTheme: DxTheme.dark(),
      locale: const Locale('vi'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      routerConfig: router,
    );
  }
}
