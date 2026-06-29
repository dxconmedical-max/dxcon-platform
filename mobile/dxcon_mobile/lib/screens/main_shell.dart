import 'package:flutter/material.dart';
import 'home_screen.dart';
import 'orders_screen.dart';
import 'files_screen.dart';
import 'profile_screen.dart';
import 'collector_shipments_screen.dart';

class MainShell extends StatefulWidget {
  final String token;
  final String email;
  final String role;
  final String? userId;

  const MainShell({
    super.key,
    required this.token,
    required this.email,
    required this.role,
    this.userId,
  });

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int index = 0;

  bool get isCollector {
    final normalized = widget.role.toUpperCase();
    return normalized == "COLLECTOR" || normalized == "SUPER_ADMIN";
  }

  @override
  Widget build(BuildContext context) {
    final screens = isCollector
        ? [
            HomeScreen(
              email: widget.email,
              role: widget.role,
              userId: widget.userId,
            ),
            CollectorShipmentsScreen(
              email: widget.email,
              collectorId: widget.userId,
            ),
            const OrdersScreen(),
            ProfileScreen(email: widget.email, role: widget.role),
          ]
        : [
            HomeScreen(
              email: widget.email,
              role: widget.role,
              userId: widget.userId,
            ),
            const OrdersScreen(),
            const FilesScreen(),
            ProfileScreen(email: widget.email, role: widget.role),
          ];

    final destinations = isCollector
        ? const [
            NavigationDestination(icon: Icon(Icons.home), label: "Home"),
            NavigationDestination(
              icon: Icon(Icons.local_shipping),
              label: "Shipments",
            ),
            NavigationDestination(
              icon: Icon(Icons.receipt_long),
              label: "Orders",
            ),
            NavigationDestination(icon: Icon(Icons.person), label: "Profile"),
          ]
        : const [
            NavigationDestination(icon: Icon(Icons.home), label: "Home"),
            NavigationDestination(
              icon: Icon(Icons.receipt_long),
              label: "Orders",
            ),
            NavigationDestination(
              icon: Icon(Icons.picture_as_pdf),
              label: "Files",
            ),
            NavigationDestination(icon: Icon(Icons.person), label: "Profile"),
          ];

    if (index >= screens.length) {
      index = 0;
    }

    return Scaffold(
      body: screens[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => setState(() => index = i),
        destinations: destinations,
      ),
    );
  }
}
