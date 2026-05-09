# UIBenchKit CLI

Command-line interface for the UIBenchKit image-to-HTML benchmarking API.

The primary command is `uibenchkit`. A compatibility alias `uibenchkit_cli` is also installed.

## Installation

```bash
cd <repo-root>
pip install -e .
```

## Quick Start

```bash
# Set your API key
export UIBENCHKIT_API_KEY="your-api-key"

# Windows PowerShell
$env:UIBENCHKIT_API_KEY = "your-api-key"

# Check API/server capabilities
uibenchkit health

# Submit a run
uibenchkit submit gemini dcgen --dataset design2code

# Watch progress
uibenchkit poll <run_id> --watch

# Fetch a report
uibenchkit get-report <run_id>
```

## Main Commands

- `uibenchkit submit <model> <method> [--dataset ... | --input-dir ...]`
- `uibenchkit run-all <model> [--dataset ... | --input-dir ...]`
- `uibenchkit poll <run_id> [--watch]`
- `uibenchkit list-runs [--model ... --method ... --dataset ...]`
- `uibenchkit get-report <run_id>`
- `uibenchkit delete-run <run_id>`
- `uibenchkit stop-run <run_id>`
- `uibenchkit rerun-evaluation <run_id>`
- `uibenchkit resume-run <run_id>`
- `uibenchkit retry-failed <run_id>`
- `uibenchkit datasets list|info|samples ...`
- `uibenchkit health`
- `uibenchkit get-quotas`
- `uibenchkit gen-api-key <email>`
- `uibenchkit verify-api-key`

## Supported Methods

- `dcgen`
- `direct`
- `latcoder`
- `uicopilot`
- `layoutcoder`

Use `uibenchkit health --models` to see the server's current supported model families and versions.

## Environment Variables

- `UIBENCHKIT_API_KEY`: API key for authentication
- `UIBENCHKIT_API_URL`: API base URL (default: `http://localhost:5000`)
