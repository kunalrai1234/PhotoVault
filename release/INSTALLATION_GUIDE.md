# PhotoVault Local AI — Installation & User Guide

Welcome to **PhotoVault Local AI**, a 100% offline, privacy-first Windows desktop photo organizer powered by local visual similarity algorithms and local face recognition.

---

## System Requirements

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Processor:** Intel Core i5 / AMD Ryzen 5 or better (CPU-only inference supported)
- **RAM:** 4 GB minimum (8 GB+ recommended for thousands of photos)
- **Storage:** ~350 MB free disk space for application + models
- **Display:** 1280 × 720 resolution or higher

---

## Option 1: Standard Windows Setup (.exe Installer)

This is the recommended method for most users.

1. **Download Setup:**
   - Locate `PhotoVault-Setup-x64.exe` in the `release/` directory or download from the [Releases](https://github.com/kunalrai1234/PhotoVault/releases) page.

2. **Run Installer:**
   - Double-click `PhotoVault-Setup-x64.exe`.
   - If Windows SmartScreen shows a prompt ("Windows protected your PC"), click **More info** and then **Run anyway**. *(This happens for newly released open-source software without an expensive commercial code-signing certificate).*

3. **Complete Installation:**
   - Choose whether to create a Desktop shortcut.
   - Click **Install**.
   - PhotoVault will install into your user profile directory (`%LOCALAPPDATA%\Programs\PhotoVault` or `Program Files`), requiring no administrative privileges.

4. **Launch Application:**
   - Launch PhotoVault Local AI from your Desktop shortcut or Start Menu.
   - The native desktop window will open immediately.

---

## Option 2: Portable Package (.zip)

No installation required—run directly from any folder or USB drive.

1. **Download & Extract:**
   - Download `PhotoVault-Portable-x64.zip`.
   - Extract the entire archive to any folder (e.g., `D:\PhotoVault` or a USB drive).

2. **Run:**
   - Double-click `PhotoVault.exe` inside the extracted folder.
   - In portable mode, cache and thumbnails are stored directly inside the application folder (`.photovault_cache`), keeping all data self-contained.

---

## How to Use PhotoVault

### 1. Select Folders
- Click **"Add Folder"** on the Dashboard.
- Choose one or more directories containing your photos (e.g., `Pictures`, `DCIM`, external hard drive folders).
- You can add multiple folders to scan them simultaneously.

### 2. Scan & Organize
- Click **"Scan Selected Folders"**.
- Watch the live progress bar:
  - **Phase 1: File Discovery & Metadata:** Reads dimensions, EXIF dates, file sizes, and generates thumbnails.
  - **Phase 2: Local AI Analysis:** Extracts perceptual hashes (pHash/dHash) and detects human faces using OpenCV YuNet & SFace models.
- You can cancel the scan at any point by clicking **"Cancel Scan"**.

### 3. Review Duplicate Groups
- Click **"Duplicates"** in the sidebar.
- Exact duplicates are verified by full content SHA-256 cryptographic hashing (never just file size).
- Mark photos to keep or delete.

### 4. Visual Similarity & Burst Shots
- Click **"Similar Photos"** in the sidebar.
- Switch between **Strict**, **Balanced**, or **Loose** matching modes.
- Find burst shots, slight edits, and re-compressed versions.

### 5. Face Recognition & People Albums
- Click **"Faces / People"** in the sidebar.
- Browse automatically identified people clusters (e.g., "Person 01", "Person 02").
- Click any person to view all photographs they appear in.
- Rename individuals to real names (e.g., "Alice", "Mom", "John").
- Merge clusters if the same person was detected in different lighting.

### 6. Safe Cleanup (Windows Recycle Bin)
- When cleaning up unwanted photos or duplicate copies, click **"Delete Selected"**.
- Files are safely moved to the **Windows Recycle Bin** via OS shell APIs (`send2trash`). No permanent deletion occurs without your OS confirmation!

### 7. Optional AI Features
- By default, PhotoVault runs **100% offline with ZERO network calls**.
- If you wish to use optional cloud vision models (Google Gemini, OpenAI, Anthropic Claude), navigate to **AI Settings**.
- Paste your API key—it is encrypted and stored securely in **Windows Credential Manager** (never in plain text files or git).

---

## Uninstallation

To remove PhotoVault:
1. Open Windows **Settings > Apps > Installed apps**.
2. Search for **PhotoVault Local AI**.
3. Click **Uninstall**.
4. The uninstaller removes all application files and shortcuts. Your original photos and personal metadata are never touched.

