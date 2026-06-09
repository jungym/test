"""SafeCopy Core — 로컬 데이터 방화벽 (local data firewall).

SafeCopy Core detects sensitive information before it leaves the machine
through external paths (AI prompt boxes, clipboard, file uploads, USB) and
masks / substitutes / blocks / logs it locally. It is *not* an antivirus or
EDR: it guards against normal apps and normal users accidentally exporting
sensitive data, not against malware.

The pipeline is:

    detection -> risk -> policy -> masking -> vault + audit

Each stage is a standalone module so it can be tested in isolation and so
platform-specific I/O (clipboard, UI) stays at the edges.
"""

__version__ = "0.1.0"
