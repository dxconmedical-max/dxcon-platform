import 'package:flutter/material.dart';

import 'collector_shipments_screen.dart';

class HomeScreen extends StatelessWidget {
  final String email;
  final String role;
  final String? userId;

  const HomeScreen({
    super.key,
    required this.email,
    required this.role,
    this.userId,
  });

  bool get isCollector {
    final normalized = role.toUpperCase();
    return normalized == "COLLECTOR" || normalized == "SUPER_ADMIN";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("DxCon Home")),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Xin chao", style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(email),
            Text("Role: $role"),
            const SizedBox(height: 20),
            if (isCollector)
              Card(
                child: ListTile(
                  title: const Text("Collector Shipments"),
                  subtitle: const Text("Accept shipments and start trips"),
                  leading: const Icon(Icons.local_shipping),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => CollectorShipmentsScreen(
                          email: email,
                          collectorId: userId,
                        ),
                      ),
                    );
                  },
                ),
              ),
            const Card(
              child: ListTile(
                title: Text("My Orders"),
                leading: Icon(Icons.receipt_long),
              ),
            ),
            const Card(
              child: ListTile(
                title: Text("Results"),
                leading: Icon(Icons.science),
              ),
            ),
            const Card(
              child: ListTile(
                title: Text("Result Files"),
                leading: Icon(Icons.picture_as_pdf),
              ),
            ),
            const Card(
              child: ListTile(
                title: Text("Profile"),
                leading: Icon(Icons.person),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
