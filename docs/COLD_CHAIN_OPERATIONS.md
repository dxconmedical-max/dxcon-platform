# Cold Chain Operations

## Threshold policies

Laboratory or quality personnel configure policies per organization via the service layer (`IoTThresholdPolicy`). Dimensions include specimen type, container type, temperature/humidity bounds, grace duration, and calibration requirements.

Policies require an approver; hardcoded universal clinical thresholds are not used.

## Excursions

States: DETECTED → ACTIVE → ACKNOWLEDGED → INVESTIGATING → RESOLVED, with SAMPLE_HOLD and SAMPLE_REJECTED requiring authorized human workflow.

**Specimens are never automatically released or rejected** based on sensor data alone.

## Alerts

In-app alert queue with deduplication. Email, SMS, push, and webhook channels are foundation-only unless configured.
