from pathlib import Path

files = {
"lib/core/config/api_config.dart": '''
class ApiConfig {
  static const String baseUrl = "https://dxcon-ap.onrender.com";
}
''',

"lib/core/theme/app_theme.dart": '''
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
''',

"lib/services/auth_service.dart": '''
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config/api_config.dart';

class AuthService {
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final url = Uri.parse("\${ApiConfig.baseUrl}/api/v1/auth/login");

    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "email": email,
        "password": password,
      }),
    );

    if (!response.headers.toString().contains("application/json")) {
      throw Exception("Server returned non-JSON: \${response.statusCode}");
    }

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data["error"] ?? "Login failed");
    }

    return data;
  }
}
''',

"lib/screens/login_screen.dart": '''
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import 'main_shell.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final emailController = TextEditingController(text: "patient@example.com");
  final passwordController = TextEditingController(text: "123456");

  bool loading = false;
  String error = "";

  Future<void> login() async {
    setState(() {
      loading = true;
      error = "";
    });

    try {
      final data = await AuthService.login(
        email: emailController.text.trim(),
        password: passwordController.text.trim(),
      );

      if (!mounted) return;

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => MainShell(
            token: data["token"] ?? data["access_token"] ?? "",
            email: data["email"] ?? emailController.text.trim(),
            role: data["role"] ?? data["user"]?["role"] ?? "PATIENT",
          ),
        ),
      );
    } catch (e) {
      setState(() {
        error = e.toString();
      });
    } finally {
      setState(() {
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Container(
          width: 420,
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                "DxCon Mobile",
                style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: emailController,
                decoration: const InputDecoration(
                  labelText: "Email",
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: passwordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: "Password",
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              if (error.isNotEmpty)
                Text(error, style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: loading ? null : login,
                  child: Text(loading ? "LOGGING IN..." : "LOGIN"),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
''',

"lib/screens/main_shell.dart": '''
import 'package:flutter/material.dart';
import 'home_screen.dart';
import 'orders_screen.dart';
import 'files_screen.dart';
import 'profile_screen.dart';

class MainShell extends StatefulWidget {
  final String token;
  final String email;
  final String role;

  const MainShell({
    super.key,
    required this.token,
    required this.email,
    required this.role,
  });

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int index = 0;

  @override
  Widget build(BuildContext context) {
    final screens = [
      HomeScreen(email: widget.email, role: widget.role),
      const OrdersScreen(),
      const FilesScreen(),
      ProfileScreen(email: widget.email, role: widget.role),
    ];

    return Scaffold(
      body: screens[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => setState(() => index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: "Home"),
          NavigationDestination(icon: Icon(Icons.receipt_long), label: "Orders"),
          NavigationDestination(icon: Icon(Icons.picture_as_pdf), label: "Files"),
          NavigationDestination(icon: Icon(Icons.person), label: "Profile"),
        ],
      ),
    );
  }
}
''',

"lib/screens/home_screen.dart": '''
import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  final String email;
  final String role;

  const HomeScreen({
    super.key,
    required this.email,
    required this.role,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("DxCon Home")),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Xin chào", style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(email),
            Text("Role: $role"),
            const SizedBox(height: 20),
            const Card(child: ListTile(title: Text("My Orders"), leading: Icon(Icons.receipt_long))),
            const Card(child: ListTile(title: Text("Results"), leading: Icon(Icons.science))),
            const Card(child: ListTile(title: Text("Result Files"), leading: Icon(Icons.picture_as_pdf))),
            const Card(child: ListTile(title: Text("Profile"), leading: Icon(Icons.person))),
          ],
        ),
      ),
    );
  }
}
''',

"lib/screens/orders_screen.dart": '''
import 'package:flutter/material.dart';

class OrdersScreen extends StatelessWidget {
  const OrdersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Orders")),
      body: const Center(
        child: Text("Orders API sẽ nối ở sprint kế tiếp"),
      ),
    );
  }
}
''',

"lib/screens/files_screen.dart": '''
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
''',

"lib/screens/profile_screen.dart": '''
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
''',

"lib/main.dart": '''
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
'''
}

for name, content in files.items():
    path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n")
    print("wrote", name)

print("DxCon Mobile V1 structure ready")
