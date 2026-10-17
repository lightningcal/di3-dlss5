# Project workflow

For continuing DI3 DLSS5 work, read `docs/TROUBLESHOOTING.md` first. It is the canonical experiment log; `docs/PROGRESS.md` is earlier history and may contain superseded instructions.

The user explicitly requires this log to stay updated throughout the session. Before each experiment record its hypothesis, single variable, baseline and rollback. Afterward record observed results, neural status, evidence paths, interpretation and state left installed. Preserve logs before restarts overwrite them. Do not count fallback FPS or standalone evaluation success as actual gameplay performance success.

MSI Afterburner and RTSS must remain available/running. Do not require global shutdown/uninstall to continue. Do not declare them the cause merely because their hook appears in a test process.

Preserve user settings and distinguish current on-disk files from already-loaded code. Read current state rather than reapplying old experimental settings. The target is at least 60 FPS with actual neural rendering active.
