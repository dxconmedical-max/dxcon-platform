import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const DxConApp());
}

class DxConApp extends StatelessWidget {
  const DxConApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "DxCon Mobile",
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      home: const LoginScreen(),
    );
  }
}
