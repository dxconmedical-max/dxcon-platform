# DxCon Logistics & Chain of Custody

## Core Flow

Booking -> Collector -> Sample -> Transport Box -> Shipment -> Lab Receive -> Testing -> AI -> Doctor -> Patient

## Shipment Status

- CREATED
- IN_TRANSIT
- ARRIVED
- RECEIVED
- TESTING
- COMPLETED

## QR Types

- DXCON:SHIPMENT:<shipment_code>
- DXCON:SAMPLE:<sample_code>
- DXCON:BOX:<box_code>

## Evidence

Lab confirmation should capture:
- receiver
- received_at
- note
- photo evidence
- temperature
- GPS

## Audit

Every critical state change must write:
- AuditLog
- EventLog
- ShipmentTimeline
