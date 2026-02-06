# Optimise Test Payloads

This folder contains JSON payloads used by routing tests. The files are grouped by intent to make it easier to find, reuse, and expand test coverage.

## Folders
- `basic/`: Small, fast-running scenarios (sanity checks and core flows).
- `constraints/`: Time windows, blocked time, must-start, and other constraint edge cases.
- `clustered/`: Neighborhood clustering and dispersion scenarios.
- `geo/`: Geolocation-only or coordinate-specific scenarios.
- `large/`: Large or performance-heavy payloads.
- `misc/`: Legacy or uncategorized cases that still have tests.
- `skills/`: Skill matching and priority ordering cases.

## Conventions
- Keep payloads deterministic when possible.
- Prefer coordinates over geocoding for tests that should be stable/offline.
- Add a short note in the test name (or test docstring) when using `large/` payloads to clarify runtime impact.
- Offline deterministic variants are stored alongside originals with the `_offline` suffix.

If you add a new payload, place it in the folder that matches its primary intent and update tests accordingly.
