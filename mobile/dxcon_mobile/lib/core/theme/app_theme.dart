import 'package:flutter/material.dart';

class AppTheme {
  static const Color primary = Color(0xff0A4B5C);
  static const Color accent = Color(0xff0D6EFD);
  static const Color success = Color(0xff198754);

  static ThemeData light() {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: primary),
      useMaterial3: true,
      scaffoldBackgroundColor: const Color(0xfff1f5f9),
      appBarTheme: const AppBarTheme(
        backgroundColor: primary,
        foregroundColor: Colors.white,
      ),
    );
  }
}
