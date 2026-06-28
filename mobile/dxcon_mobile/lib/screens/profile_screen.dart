import 'package:flutter/material.dart';

class ProfileScreen extends StatelessWidget {
  final String email;
  final String role;

  const ProfileScreen({
    super.key,
    required this.email,
    required this.role,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Profile")),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Card(
          child: ListTile(
            title: Text(email),
            subtitle: Text("Role: $role"),
            leading: const Icon(Icons.person),
          ),
        ),
      ),
    );
  }
}
