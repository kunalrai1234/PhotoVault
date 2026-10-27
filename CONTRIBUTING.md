# Contributing to PhotoVault Local AI

Thank you for your interest in contributing to **PhotoVault Local AI**!

## Core Principles
1. **Privacy First:** Never introduce automatic telemetry or default network requests.
2. **Safety First:** Never allow permanent file deletion without explicit confirmation; always support Windows Recycle Bin (`send2trash`).
3. **CPU Efficiency:** Keep inference lightweight and responsive for standard laptop hardware.

## Development Workflow
1. Fork the repository and clone your fork locally.
2. Create a virtual environment and install backend requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   npm install
   ```
4. Run tests before submitting a Pull Request:
   ```bash
   pytest backend/tests/
   ```
5. Open a descriptive Pull Request targeting the `main` branch.
