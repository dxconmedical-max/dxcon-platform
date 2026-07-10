import 'package:flutter/material.dart';

/// DxCon mobile design tokens aligned with web design system naming.
class DxColors {
  static const primary = Color(0xFF0B5FFF);
  static const primaryDark = Color(0xFF0847C7);
  static const secondary = Color(0xFF00A3A3);
  static const surface = Color(0xFFF8FAFC);
  static const surfaceDark = Color(0xFF0F172A);
  static const error = Color(0xFFDC2626);
  static const warning = Color(0xFFF59E0B);
  static const success = Color(0xFF16A34A);
  static const textPrimary = Color(0xFF0F172A);
  static const textSecondary = Color(0xFF64748B);
  static const border = Color(0xFFE2E8F0);
}

class DxSpacing {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
}

class DxRadius {
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
}

class DxTheme {
  static ThemeData light() {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: DxColors.primary,
        brightness: Brightness.light,
        error: DxColors.error,
      ),
      scaffoldBackgroundColor: DxColors.surface,
    );
    return base.copyWith(
      appBarTheme: const AppBarTheme(
        centerTitle: false,
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: DxColors.textPrimary,
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(DxRadius.md),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: DxSpacing.md,
          vertical: DxSpacing.sm + 4,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(88, 48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(DxRadius.md),
          ),
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(DxRadius.lg),
          side: const BorderSide(color: DxColors.border),
        ),
      ),
    );
  }

  static ThemeData dark() {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: DxColors.primary,
        brightness: Brightness.dark,
      ),
      scaffoldBackgroundColor: DxColors.surfaceDark,
    );
  }
}
