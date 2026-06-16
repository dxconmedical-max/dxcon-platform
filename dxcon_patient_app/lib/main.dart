import 'dart:convert';
import 'dart:html' as html;

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'home_collection_page.dart';

const String apiBase = "http://127.0.0.1:8000/api/v1/mobile";
const String webBase = "http://127.0.0.1:8000";

void main() {
  runApp(const DxConPatientApp());
}

class DxConPatientApp extends StatelessWidget {
  const DxConPatientApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DxCon Patient',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(primarySwatch: Colors.teal),
      home: const LoginPage(),
    );
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final emailController = TextEditingController(text: "patient@example.com");
  final passwordController = TextEditingController(text: "123456");

  String error = "";
  bool loading = false;

  Future<void> login() async {
    setState(() {
      loading = true;
      error = "";
    });

    try {
      final response = await http.post(
        Uri.parse("$apiBase/login"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "email": emailController.text.trim(),
          "password": passwordController.text.trim(),
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data["success"] == true) {
        if (!mounted) return;

        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => HomePage(
              patientId: data["patient_id"],
            ),
          ),
        );
      } else {
        setState(() {
          error = data["error"] ?? "Login failed";
        });
      }
    } catch (e) {
      setState(() {
        error = "Cannot connect to DxCon API";
      });
    }

    setState(() {
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xfff1f5f9),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      "DxCon Patient",
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 24),
                    TextField(
                      controller: emailController,
                      decoration: const InputDecoration(
                        labelText: "Email",
                      ),
                    ),
                    TextField(
                      controller: passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: "Password",
                      ),
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: loading ? null : login,
                        child: loading
                            ? const CircularProgressIndicator()
                            : const Text("Login"),
                      ),
                    ),
                    if (error.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 16),
                        child: Text(
                          error,
                          style: const TextStyle(color: Colors.red),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HomePage extends StatefulWidget {
  final String patientId;

  const HomePage({
    super.key,
    required this.patientId,
  });

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  Map profile = {};
  List orders = [];
  List results = [];
  List summaries = [];
  List tracking = [];
  List homeCollections = [];

  bool loading = true;
  String error = "";

  @override
  void initState() {
    super.initState();
    loadAll();
  }

  Future<void> loadAll() async {
    try {
      final p = await http.get(
        Uri.parse("$apiBase/profile/${widget.patientId}"),
      );

      final o = await http.get(
        Uri.parse("$apiBase/orders/${widget.patientId}"),
      );

      final r = await http.get(
        Uri.parse("$apiBase/results/${widget.patientId}"),
      );

      final s = await http.get(
        Uri.parse("$apiBase/clinical-summary/${widget.patientId}"),
      );

      final t = await http.get(
        Uri.parse("$apiBase/tracking/${widget.patientId}"),
      );

      final h = await http.get(
        Uri.parse("$apiBase/home-collections/${widget.patientId}"),
      );

      setState(() {
        profile = jsonDecode(p.body);
        orders = jsonDecode(o.body)["orders"] ?? [];
        results = jsonDecode(r.body)["results"] ?? [];
        summaries = jsonDecode(s.body)["clinical_summaries"] ?? [];
        tracking = jsonDecode(t.body)["tracking"] ?? [];
        homeCollections = jsonDecode(h.body)["home_collections"] ?? [];
        loading = false;
      });
    } catch (e) {
      setState(() {
        error = "Cannot load patient data";
        loading = false;
      });
    }
  }

  Widget metricCard(String title, String value, Color color) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            children: [
              Text(
                title,
                style: const TextStyle(fontSize: 13),
              ),
              const SizedBox(height: 8),
              Text(
                value,
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget section(String title, Widget child) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }

  Widget emptyText(String text) {
    return Text(
      text,
      style: const TextStyle(color: Colors.grey),
    );
  }

  void openPdf(Map o) {
    final orderId = o["id"];

    if (orderId == null || orderId.toString().isEmpty) {
      html.window.alert("Order ID not found");
      return;
    }

    final pdfUrl = "$webBase/results/report/$orderId/pdf";
    html.window.open(pdfUrl, "_blank");
  }

  void openReport(Map o) {
    final orderId = o["id"];

    if (orderId == null || orderId.toString().isEmpty) {
      html.window.alert("Order ID not found");
      return;
    }

    final reportUrl = "$webBase/results/report/$orderId";
    html.window.open(reportUrl, "_blank");
  }

  Color statusColor(String status) {
    if (status == "CHECKED_IN") return Colors.green;
    if (status == "IN_TRANSIT") return Colors.orange;
    if (status == "RECEIVED") return Colors.purple;
    if (status == "COMPLETED") return Colors.teal;
    if (status == "PENDING") return Colors.orange;

    return Colors.blue;
  }

  @override
  Widget build(BuildContext context) {
    final patientName = profile["full_name"] ?? "";

    return Scaffold(
      backgroundColor: const Color(0xfff1f5f9),
      appBar: AppBar(
        title: const Text("DxCon Patient Portal"),
        actions: [
          IconButton(
            onPressed: loadAll,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error.isNotEmpty
              ? Center(child: Text(error))
              : RefreshIndicator(
                  onRefresh: loadAll,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      Text(
                        "Hello, $patientName",
                        style: const TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          metricCard(
                            "Orders",
                            orders.length.toString(),
                            Colors.teal,
                          ),
                          metricCard(
                            "Results",
                            results.length.toString(),
                            Colors.blue,
                          ),
                          metricCard(
                            "Bookings",
                            homeCollections.length.toString(),
                            Colors.purple,
                          ),
                        ],
                      ),
                      section(
                        "Patient Information",
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("Code: ${profile["patient_code"] ?? ""}"),
                            Text("Name: ${profile["full_name"] ?? ""}"),
                            Text("Phone: ${profile["phone"] ?? ""}"),
                            Text("Email: ${profile["email"] ?? ""}"),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              icon: const Icon(Icons.home),
                              label: const Text("Book Home Collection"),
                              onPressed: () async {
                                await Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => HomeCollectionPage(
                                      patientId: widget.patientId,
                                    ),
                                  ),
                                );

                                loadAll();
                              },
                            ),
                          ],
                        ),
                      ),
                      section(
                        "Home Collection Bookings",
                        homeCollections.isEmpty
                            ? emptyText("No booking")
                            : Column(
                                children: homeCollections.map((h) {
                                  final status = h["status"] ?? "";
                                  final color = statusColor(status);

                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 12),
                                    padding: const EdgeInsets.all(14),
                                    decoration: BoxDecoration(
                                      color: const Color(0xfff8fafc),
                                      border: Border(
                                        left: BorderSide(
                                          color: color,
                                          width: 6,
                                        ),
                                      ),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(
                                          Icons.home_work,
                                          color: color,
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                h["address"] ?? "",
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.bold,
                                                ),
                                              ),
                                              Text(
                                                "Schedule: ${h["scheduled_time"] ?? ""}",
                                              ),
                                              Text("Status: $status"),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                }).toList(),
                              ),
                      ),
                      section(
                        "Orders",
                        orders.isEmpty
                            ? emptyText("No orders")
                            : Column(
                                children: orders.map((o) {
                                  return Card(
                                    margin: const EdgeInsets.only(bottom: 10),
                                    child: ListTile(
                                      leading: const Icon(Icons.receipt_long),
                                      title: Text(o["order_code"] ?? ""),
                                      subtitle: Text(
                                        "Status: ${o["status"]}",
                                      ),
                                      trailing: Wrap(
                                        spacing: 8,
                                        crossAxisAlignment:
                                            WrapCrossAlignment.center,
                                        children: [
                                          Text(
                                            "${o["total_amount"] ?? 0} VND",
                                          ),
                                          IconButton(
                                            tooltip: "View Report",
                                            icon: const Icon(Icons.open_in_new),
                                            onPressed: () => openReport(o),
                                          ),
                                          IconButton(
                                            tooltip: "PDF",
                                            icon: const Icon(
                                              Icons.picture_as_pdf,
                                            ),
                                            onPressed: () => openPdf(o),
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                }).toList(),
                              ),
                      ),
                      section(
                        "Test Results",
                        results.isEmpty
                            ? emptyText("No results")
                            : Column(
                                children: results.map((r) {
                                  final flag = r["flag"] ?? "";
                                  final abnormal =
                                      flag != "" && flag != "NORMAL";

                                  return ListTile(
                                    leading: Icon(
                                      abnormal
                                          ? Icons.warning
                                          : Icons.check_circle,
                                      color: abnormal
                                          ? Colors.red
                                          : Colors.green,
                                    ),
                                    title: Text(r["test_name"] ?? ""),
                                    subtitle: Text(
                                      "Result: ${r["result_value"]} ${r["unit"] ?? ""}",
                                    ),
                                    trailing: Text(flag),
                                  );
                                }).toList(),
                              ),
                      ),
                      section(
                        "Clinical Summary",
                        summaries.isEmpty
                            ? emptyText("No clinical summary")
                            : Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: summaries.map((s) {
                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 12),
                                    padding: const EdgeInsets.all(14),
                                    decoration: BoxDecoration(
                                      color: const Color(0xfff8fafc),
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: Text(
                                      "Risk: ${s["risk_level"]}\n\n"
                                      "Findings:\n${s["findings"]}\n\n"
                                      "Recommendations:\n${s["recommendations"]}",
                                    ),
                                  );
                                }).toList(),
                              ),
                      ),
                      section(
                        "Sample Tracking Timeline",
                        tracking.isEmpty
                            ? emptyText("No tracking")
                            : Column(
                                children: tracking.take(20).map((t) {
                                  final status = t["status"] ?? "";
                                  final color = statusColor(status);

                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 12),
                                    padding: const EdgeInsets.all(14),
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      border: Border(
                                        left: BorderSide(
                                          color: color,
                                          width: 6,
                                        ),
                                      ),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(
                                          Icons.local_shipping,
                                          color: color,
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                t["sample_code"] ?? "",
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.bold,
                                                ),
                                              ),
                                              Text("Status: $status"),
                                              if (t["updated_at"] != null)
                                                Text(
                                                  "Updated: ${t["updated_at"]}",
                                                  style: const TextStyle(
                                                    fontSize: 12,
                                                    color: Colors.grey,
                                                  ),
                                                ),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                }).toList(),
                              ),
                      ),
                    ],
                  ),
                ),
    );
  }
}
