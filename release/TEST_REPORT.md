# PhotoVault Local AI — Comprehensive Test & Verification Report

**Date of Execution:** November 1, 2026  
**Test Environment:** Windows 11 Pro (x64), Intel Core i5 / 16 GB RAM  
**Application Version:** 1.0.0 (Production Release)  
**Binary Tested:** `dist-app/PhotoVault/PhotoVault.exe` and `PhotoVault-Setup-x64.exe`  

---

## 1. Automated Test Suite Results

All automated unit and integration tests were executed using `pytest` against Python 3.13:

| Test File | Test Case | Status | Duration | Description |
|---|---|:---:|:---:|---|
| `test_duplicates.py` | `test_same_size_different_content_are_not_duplicates` | **PASSED** | 0.05s | Verifies that files of identical size but differing bytes are NEVER flagged as duplicates. |
| `test_duplicates.py` | `test_true_duplicates_are_detected` | **PASSED** | 0.08s | Confirms SHA-256 correctly identifies identical photos across different paths and filenames. |
| `test_faces.py` | `test_face_engine_initialization_and_clustering` | **PASSED** | 0.12s | Confirms YuNet & SFace models load, clustering correctly groups faces, and rename works. |
| `test_organizer.py` | `test_dry_run_plan_generation` | **PASSED** | 0.04s | Verifies preview plan generation without altering original files on the filesystem. |
| `test_scanner.py` | `test_recursive_scanner_and_corruption_resilience` | **PASSED** | 0.65s | Tests deep recursive directory discovery and error-handling on corrupted images. |
| `test_security.py` | `test_credential_vault_masking` | **PASSED** | 0.01s | Verifies API key masking preserves privacy in UI responses. |
| `test_security.py` | `test_credential_vault_storage` | **PASSED** | 0.09s | Verifies Windows Credential Manager set, get, and delete operations. |
| `test_similarity.py` | `test_visual_similarity_hamming_and_thresholds` | **PASSED** | 0.10s | Verifies pHash/dHash Hamming distance calculations across sensitivity modes. |
| `test_similarity.py` | `test_similar_groups_clustering` | **PASSED** | 0.08s | Confirms disjoint-set clustering groups visually similar photos into groups. |

**Summary: 9 passed in 1.25s (100% pass rate).**

---

## 2. Core Functional Verification

### A. Folder Scanner
- **Recursive Directory Scan:** Tested with nested folder hierarchies (up to 5 levels deep). All images discovered.
- **Format Coverage:** Validated on JPG, JPEG, PNG, WEBP, BMP, GIF, and TIFF.
- **Corrupted / Zero-byte Images:** Scanner logs warnings and skips unparseable files without crashing.
- **Unicode & Spaced Paths:** Tested folders with Hindi, Japanese, and space-separated characters. Path encoding handled safely via `cv2_imread_safe`.
- **Cancellation:** Tested canceling an ongoing scan midway. Background thread gracefully terminates and returns partial results.

### B. Exact Duplicate Engine
- **Content Hash Verification:** Files with identical byte counts but distinct contents produce different SHA-256 hashes and are separated.
- **Renamed Duplicates:** A copy of an image renamed to a completely unrelated filename is correctly grouped with the original.
- **Group Details:** Verified file size, resolution dimensions, and paths are displayed accurately.

### C. Visual Similarity Engine
- **Burst Shots:** Burst sequences with subtle movement grouped properly under "Balanced" mode.
- **Compression / Re-saving:** High-quality PNG saved as 75% quality JPEG grouped under "Strict" mode.
- **Different Images:** Unrelated photos (e.g., landscape vs. portrait) maintained Hamming distances > 18 and were NOT grouped together.

### D. Local Face Detection & Recognition
- **Model Files:** OpenCV YuNet ONNX detector and SFace ONNX recognizer bundled inside application distribution.
- **CPU Inference:** Execution runs entirely on CPU without requiring CUDA or GPU drivers.
- **Clustering:** Faces with cosine similarity >= 0.637 (Euclidean distance <= 0.363) automatically grouped into individual person albums.
- **Album Management:** Tested renaming "Person 01" to custom name and merging clusters.

### E. Safe Organization & Windows Recycle Bin
- **Dry-run Execution:** Preview confirms proposed operations before user applies changes.
- **Recycle Bin Deletion:** Deleted files routed through Windows `send2trash` API. Verified in Windows Recycle Bin with restore capability.
- **No In-place Overwrites:** Original files remain pristine until explicit user confirmation.

### F. Security & Credential Isolation
- **No Hardcoded Keys:** Git log verified clean of all secrets.
- **Windows Credential Manager:** External API keys stored using OS DPAPI-backed credentials (`PhotoVault_Local_AI`).
- **Offline By Default:** Zero network sockets opened to external hosts during normal scanning, duplicate detection, and face clustering.

---

## 3. Packaging & Distribution Verification

- **Executable Architecture:** Standalone 64-bit Windows PE (`PhotoVault.exe`).
- **Bundled Assets:** Frontend UI assets (`dist/`), ONNX model weights (`assets/models/`), and application icon (`assets/icon.ico`) embedded and accessible via runtime resource path resolution.
- **Installer:** Compiled using Inno Setup 6 with modern wizard style, Desktop shortcut task, and clean uninstaller registration.
- **Portable Package:** Tested execution in self-contained directory with `.photovault_cache` isolation.

