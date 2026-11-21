# LTM release policy

Develop and test future changes on `develop` / Beta first. Stable (`main`) is the tested baseline; do not use Stable as the normal test channel.

The owner authorized the consolidated 1.12.19 Stable and matching 1.12.19-beta.1 release on 8 November 2026 and confirmed physical Mac/Windows installation and data preservation. Keep Stable/Beta folders, login cookies and native installer identities separate.

Keep generated release assets immutable. Publish from the exact checked commit only after its required checks pass. Mac-server remains gated on its separate physical Apple Silicon LAN/VPN/restart test; desktop approval does not satisfy that test.

Every Beta/Stable release MUST follow [docs/VERSIONERING.md](docs/VERSIONERING.md). Beta X.Y.Z-beta.N and Stable X.Y.Z share a base; publishing requires the automated policy check in scripts/version_policy.py, a unique immutable tag and verification against the latest Stable/Beta. Do not bypass the gate or publish an untested Stable hotfix directly; sync main into develop before the next Beta.

Never read or modify a real user's territory data to run tests; use temporary fictional fixtures.


# Focused work and limited AI allowance

The owner has a limited shared ChatGPT/Codex allowance. Use the least expensive model and lowest reasoning level adequate for the task. Small text/UI/test changes start on a small model with low reasoning; ordinary implementation starts on a small model with low/medium reasoning. Escalate only for a concrete unresolved problem or meaningful risk to data, authentication, concurrency or release correctness. Do not default to Sol High, Astra, Max/Ultra or fast mode. If the tool cannot change the model, state that limitation rather than claiming a change.

Do not read the whole repository to make a small change. Read applicable AGENTS.md instructions, the task and current diff, then search narrowly with rg in the likely component. Open only relevant functions, direct dependencies and focused tests. Expand scope only when evidence requires it; stop discovery once the change path is understood. There is no requirement to read every source file, document, planning note or previous chat.

Exclude vendor/generated/build output, release bundles, old checkout copies, archived plans and unrelated documentation from routine searches. Do not reload unchanged files or dump whole logs/large files when a bounded excerpt answers the question. Use one canonical checkout and a short continuation note with branch/head, changed files, verification and remaining blockers.

Use at most one implementation chat by default. Parallel work is appropriate only for genuinely independent tasks with distinct files and a clear benefit. Send a compact task prompt with relevant file paths, base branch and acceptance criteria; do not copy the full project/chat history. Do not start extra chats just to review a small safe change.

Run focused checks after an edit. Run the broader required suite once on the final integrated release candidate; repeat only for relevant changes or a newly discovered failure. Preserve all required release checks and data-preservation tests. Monitor with compact status and longer/event-driven waits, avoid repeatedly reading whole chats or logs, and notify the owner only on meaningful progress, completion or a blocker.
