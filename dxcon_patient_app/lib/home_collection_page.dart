import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const String apiBase = "http://127.0.0.1:8000/api/v1/mobile";

class HomeCollectionPage extends StatefulWidget {
  final String patientId;

  const HomeCollectionPage({
    super.key,
    required this.patientId,
  });

  @override
  State<HomeCollectionPage> createState() => _HomeCollectionPageState();
}

class _HomeCollectionPageState extends State<HomeCollectionPage> {
  final addressController = TextEditingController();
  final scheduleController = TextEditingController();

  String message = "";
  bool loading = false;

  Future<void> submit() async {
    setState(() {
      loading = true;
      message = "";
    });

    try {
      final response = await http.post(
        Uri.parse("$apiBase/home-collection"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "patient_id": widget.patientId,
          "address": addressController.text.trim(),
          "scheduled_time": scheduleController.text.trim(),
        }),
      );

      final data = jsonDecode(response.body);

      setState(() {
        message = data["success"] == true
            ? "Booking created successfully"
            : "Booking failed";
      });
    } catch (e) {
      setState(() {
        message = "Cannot connect to DxCon API";
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
      appBar: AppBar(
        title: const Text("Home Collection Booking"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                TextField(
                  controller: addressController,
                  decoration: const InputDecoration(
                    labelText: "Address",
                  ),
                ),
                TextField(
                  controller: scheduleController,
                  decoration: const InputDecoration(
                    labelText: "Schedule: YYYY-MM-DD HH:mm",
                  ),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: loading ? null : submit,
                    child: loading
                        ? const CircularProgressIndicator()
                        : const Text("Book Home Collection"),
                  ),
                ),
                const SizedBox(height: 20),
                Text(message),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
