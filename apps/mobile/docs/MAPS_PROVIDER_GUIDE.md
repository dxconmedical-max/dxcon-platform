# Maps Provider Guide

DxCon mobile uses a **provider-agnostic** `MapProvider` interface.

## Interface

- `showMap` — display location
- `showRoute` — polyline between points
- `launchExternalNavigation` — open external maps app

## Default

`PlaceholderMapProvider` — no vendor locked in foundation.

## Integration options

- Google Maps Flutter plugin
- Mapbox
- Apple MapKit (iOS)
- OpenStreetMap-based providers

Select provider per deployment region and licensing. Do not hardcode a single vendor in core business modules.
