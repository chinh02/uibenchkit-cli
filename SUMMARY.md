# UIBenchKit CLI Repository Summary

## Overview

This repository contains a Typer-based CLI for interacting with the UIBenchKit API server (`UIBenchKit/api.py`).

- Package: `uibenchkit_cli`
- Primary executable: `uibenchkit`
- Alias executable: `uibenchkit_cli`
- Transport: HTTP requests to `UIBENCHKIT_API_URL` (default `http://localhost:5000`)

## Key Capabilities

- Submit and monitor image-to-HTML benchmark runs
- Retrieve reports with evaluation metrics and cost summary
- Manage runs (`list-runs`, `delete-run`, `stop-run`, `resume-run`, `retry-failed`, `rerun-evaluation`)
- Inspect server health, dataset metadata, and quota info
- Manage API keys (`gen-api-key`, `verify-api-key`)

## Supported Generation Methods

- `dcgen`
- `direct`
- `latcoder`
- `uicopilot`
- `layoutcoder`

## Notes

- The CLI method enum is aligned with `UIBenchKit/api.py` supported methods.
- The docs under `docs/` are UIBenchKit-focused and use `uibenchkit` commands.
