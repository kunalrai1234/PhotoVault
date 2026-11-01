# PhotoVault Local AI v1.0.0 Release Notes

**Release Date:** November 1, 2026  
**Target Platform:** Windows 10 / Windows 11 (64-bit)  
**Binary Packages:**
- `PhotoVault-Setup-x64.exe` (Official Inno Setup Windows Installer)
- `PhotoVault-Portable-x64.zip` (Zero-install portable standalone archive)

---

## 🌟 Executive Summary

**PhotoVault Local AI** is a privacy-first, 100% offline desktop photo manager built for photographers, families, and privacy-conscious users. It combines recursive folder scanning, cryptographic duplicate matching, multi-threshold visual similarity detection, and local AI facial recognition into a responsive, native Windows desktop application.

---

## 🚀 Key Highlights & Features

### 1. 100% Offline & Privacy-First by Design
- Operates entirely on the local machine without internet connection, telemetry, or cloud dependencies.
- Zero tracking, zero analytics, zero external API requests by default.
- Original image files are never moved, renamed, or modified without user verification.
- Optional external AI services (Gemini, OpenAI, Claude) keep API keys encrypted in **Windows Credential Manager**.

### 2. Recursive Folder Scanner
- Non-blocking, multi-threaded background scanning engine.
- Real-time progress updates with file-by-file feedback and cancellation support.
- Native Windows directory selection dialog.
- Deep recursive scanning across nested directories.
- Full format support: JPEG, PNG, WEBP, BMP, GIF, TIFF.
- Graceful handling of corrupted files, zero-byte images, and Unicode filenames.

### 3. Exact Duplicate Detection
- SHA-256 cryptographic content hashing.
- File sizes are only used as prefilters; photos with identical file sizes are never assumed to be duplicates without cryptographic proof.
- Grouped duplicate viewer with side-by-side comparison, file paths, dimensions, and sizes.

### 4. Visual Similarity & Burst Shot Engine
- Perceptual image hashing using pHash and dHash algorithms.
- Configurable sensitivity modes:
  - **Strict:** Identifies identical photos with format or compression differences.
  - **Balanced:** Detects burst shots, subtle crops, and minor lighting edits.
  - **Loose:** Surfaces visually similar compositions and color schemes.
- Disjoint-set clustering for high-performance grouping of large image collections.

### 5. Local Face Detection & Face Clustering (AI)
- Powered by OpenCV YuNet (ONNX) face detection and OpenCV SFace (ONNX) face recognition.
- 100% local CPU inference, requiring no GPU.
- Automatic clustering of detected faces into individual person albums ("Person 01", "Person 02", etc.).
- Renaming and merging capabilities for identified individuals.

### 6. Safe File Organization
- Dry-run preview before executing any file operations.
- Safe deletion via OS shell APIs directly to the **Windows Recycle Bin** (`send2trash`), preventing accidental permanent data loss.

---

## 📦 Distribution Artifacts

| Filename | Description | Architecture |
|---|---|---|
| `PhotoVault-Setup-x64.exe` | Windows Installer (Desktop icon, Start Menu, Uninstaller) | x86_64 |
| `PhotoVault-Portable-x64.zip` | Standalone Portable Archive (Self-contained, run anywhere) | x86_64 |
| `SHA256SUMS.txt` | Cryptographic checksums for binary integrity verification | All |

---

## 🔒 Security & Privacy Guarantee

- **Local Storage:** All metadata and face vectors reside in `%LOCALAPPDATA%\PhotoVault` or `.photovault_cache`.
- **No Secret Leakage:** Rigorous verification ensures no credentials or API keys exist in git history or configuration files.
- **Source Code:** Open source under the MIT License on GitHub: [kunalrai1234/PhotoVault](https://github.com/kunalrai1234/PhotoVault).

