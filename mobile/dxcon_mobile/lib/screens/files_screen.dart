import 'package:flutter/material.dart';

class FilesScreen extends StatelessWidget {
  const FilesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Result Files")),
      body: const Center(
        child: Text("Result Files API sẽ nối ở sprint kế tiếp"),
      ),
    );
  }
}
