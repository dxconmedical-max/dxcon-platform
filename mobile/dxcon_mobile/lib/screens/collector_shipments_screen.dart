import 'package:flutter/material.dart';

import '../services/collector_service.dart';

class CollectorShipmentsScreen extends StatefulWidget {
  final String email;
  final String? collectorId;

  const CollectorShipmentsScreen({
    super.key,
    required this.email,
    this.collectorId,
  });

  @override
  State<CollectorShipmentsScreen> createState() =>
      _CollectorShipmentsScreenState();
}

class _CollectorShipmentsScreenState extends State<CollectorShipmentsScreen> {
  bool loading = true;
  String error = "";
  List<dynamic> shipments = [];
  final Set<String> busyIds = {};

  @override
  void initState() {
    super.initState();
    loadShipments();
  }

  Future<void> loadShipments() async {
    setState(() {
      loading = true;
      error = "";
    });

    try {
      final items = await CollectorService.listShipments(
        collectorId: widget.collectorId,
      );

      if (!mounted) return;

      setState(() {
        shipments = items;
      });
    } catch (e) {
      setState(() {
        error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          loading = false;
        });
      }
    }
  }

  Future<void> _runAction({
    required String shipmentId,
    required Future<Map<String, dynamic>> Function() action,
  }) async {
    setState(() {
      busyIds.add(shipmentId);
    });

    try {
      await action();
      await loadShipments();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    } finally {
      if (mounted) {
        setState(() {
          busyIds.remove(shipmentId);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Collector Shipments"),
        actions: [
          IconButton(
            onPressed: loading ? null : loadShipments,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error.isNotEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(error, textAlign: TextAlign.center),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: loadShipments,
                          child: const Text("Retry"),
                        ),
                      ],
                    ),
                  ),
                )
              : shipments.isEmpty
                  ? const Center(child: Text("No shipments assigned."))
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: shipments.length,
                      separatorBuilder: (_, _) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final shipment =
                            shipments[index] as Map<String, dynamic>;
                        final id = shipment["id"]?.toString() ?? "";
                        final status = shipment["status"]?.toString() ?? "";
                        final busy = busyIds.contains(id);

                        return Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  shipment["shipment_code"]?.toString() ??
                                      "Shipment",
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleMedium,
                                ),
                                const SizedBox(height: 8),
                                Text("Status: $status"),
                                Text(
                                  "Lab: ${shipment["lab_name"] ?? "-"}",
                                ),
                                Text(
                                  "GPS: ${shipment["gps_location"] ?? "0.0,0.0"}",
                                ),
                                const SizedBox(height: 12),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    if (status == "CREATED")
                                      ElevatedButton(
                                        onPressed: busy
                                            ? null
                                            : () => _runAction(
                                                  shipmentId: id,
                                                  action: () =>
                                                      CollectorService
                                                          .acceptShipment(
                                                    shipmentId: id,
                                                    collectorId:
                                                        widget.collectorId,
                                                    actor: widget.email,
                                                  ),
                                                ),
                                        child: Text(
                                          busy ? "Working..." : "Accept",
                                        ),
                                      ),
                                    if (status == "ACCEPTED")
                                      ElevatedButton(
                                        onPressed: busy
                                            ? null
                                            : () => _runAction(
                                                  shipmentId: id,
                                                  action: () =>
                                                      CollectorService
                                                          .startTrip(
                                                    shipmentId: id,
                                                    collectorId:
                                                        widget.collectorId,
                                                    actor: widget.email,
                                                  ),
                                                ),
                                        child: Text(
                                          busy ? "Working..." : "Start Trip",
                                        ),
                                      ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
    );
  }
}
