import 'package:flutter/material.dart';

import 'package:dxcon_mobile/design_system/theme.dart';

class DxEmptyState extends StatelessWidget {
  const DxEmptyState({
    super.key,
    required this.title,
    this.subtitle,
    this.icon = Icons.inbox_outlined,
    this.action,
  });

  final String title;
  final String? subtitle;
  final IconData icon;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(DxSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 48, color: DxColors.textSecondary),
            const SizedBox(height: DxSpacing.md),
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            if (subtitle != null) ...[
              const SizedBox(height: DxSpacing.sm),
              Text(
                subtitle!,
                textAlign: TextAlign.center,
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(color: DxColors.textSecondary),
              ),
            ],
            if (action != null) ...[
              const SizedBox(height: DxSpacing.lg),
              action!,
            ],
          ],
        ),
      ),
    );
  }
}

class DxLoadingState extends StatelessWidget {
  const DxLoadingState({super.key, this.message});

  final String? message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          if (message != null) ...[
            const SizedBox(height: DxSpacing.md),
            Text(message!),
          ],
        ],
      ),
    );
  }
}

class DxErrorState extends StatelessWidget {
  const DxErrorState({super.key, required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(DxSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: DxColors.error, size: 48),
            const SizedBox(height: DxSpacing.md),
            Text(message, textAlign: TextAlign.center),
            if (onRetry != null) ...[
              const SizedBox(height: DxSpacing.lg),
              ElevatedButton(onPressed: onRetry, child: const Text('Thử lại')),
            ],
          ],
        ),
      ),
    );
  }
}

class DxStatusChip extends StatelessWidget {
  const DxStatusChip({super.key, required this.label, this.color});

  final String label;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final chipColor = color ?? DxColors.primary;
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: DxSpacing.sm + 2,
        vertical: DxSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: chipColor.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(DxRadius.sm),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: chipColor,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
