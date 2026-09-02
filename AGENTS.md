# AVAJ agent entry point

Before making changes in this repository, read these documents in order:

1. [`CURRENT_STATE.md`](CURRENT_STATE.md) — current verified implementation,
   runtime state, safety boundary and next work.
2. [`AGENTS (1).md`](AGENTS%20(1).md) — binding target architecture and
   implementation rules.
3. [`DEVELOPMENT_PLAN.md — AVAJ RC-Car.md`](DEVELOPMENT_PLAN.md%20%E2%80%94%20AVAJ%20RC-Car.md)
   — dependency-ordered development plan and physical test gates.
4. [`HANDOFF.md`](HANDOFF.md) and [`README.md`](README.md) — operational history
   and user commands.

The working tree contains important uncommitted work. Inspect `git status`
before editing and do not discard, reset or overwrite existing changes.

The repository is not currently cleared for powered actuator or autonomous
real-vehicle tests. The ESP32 final safety authority, independent command
watchdog, encoder odometry and physical emergency stop have not been verified.

