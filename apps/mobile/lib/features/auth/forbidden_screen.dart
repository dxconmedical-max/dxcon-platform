import 'package:flutter/material.dart';

class ForbiddenScreen extends StatelessWidget {
  const ForbiddenScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Không có quyền')),
      body: const Center(
        child: Text('Bạn không có quyền truy cập tính năng này.'),
      ),
    );
  }
}
