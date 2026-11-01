# 📸 PhotoVault Local AI

> **Privacy-First, 100% Offline Windows Desktop Photo Organizer with Visual Similarity & Local Face Recognition.**  
> *आपके कंप्यूटर पर पूरी तरह सुरक्षित और प्राइवेट फ़ोटो आर्गेनाइज़र — बिना किसी इंटरनेट या क्लाउड के।*

[![Release](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](https://github.com/kunalrai1234/PhotoVault/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: Windows 10/11](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(64--bit)-lightgrey.svg)]()

---

## 🌟 What is PhotoVault Local AI? (यह क्या है?)

**PhotoVault Local AI** is a complete, native Windows desktop application designed to scan, analyze, and organize your photo collection locally on your PC. 

Unlike traditional software that relies only on filenames or file sizes, PhotoVault uses **actual visual content analysis**, **cryptographic hashing (SHA-256)**, **perceptual hashing (pHash/dHash)**, and **local AI computer vision models (OpenCV YuNet & SFace)** to:
- Find **Exact Duplicates** (verified by content bytes, never file size alone).
- Detect **Near-Identical Burst Shots** and visually similar edited/resized photos.
- Automatically recognize **Human Faces** and cluster them into individual person albums (*Person 01*, *Person 02*, etc.).
- Safely clean up unwanted photos by moving them to the **Windows Recycle Bin** (`send2trash`), preventing accidental data loss.

**Everything runs 100% locally on your computer's CPU — zero internet, zero cloud uploads, zero telemetry.**

---

## 💾 Quick Download & Installation (सबसे आसान तरीका)

No coding, Python, or Node.js required! Simply download and install like standard desktop software:

### Method 1: Standard Windows Setup (.exe Installer) — Recommended
1. Go to the `release/` folder or download [PhotoVault-Setup-x64.exe](https://github.com/kunalrai1234/PhotoVault/releases).
2. Double-click **`PhotoVault-Setup-x64.exe`**.
3. Follow the setup wizard (choose Desktop Shortcut).
4. Click **Install**.
5. Launch **PhotoVault Local AI** from your Desktop or Start Menu!

### Method 2: Portable Edition (.zip) — No Installation Required
1. Download **`PhotoVault-Portable-x64.zip`** from the `release/` folder.
2. Right-click and extract the `.zip` archive anywhere (e.g. `D:\PhotoVault` or a USB flash drive).
3. Double-click **`PhotoVault.exe`** inside the folder to run immediately.

---

## 🔒 10 Core Privacy & Safety Guarantees

1. **100% Offline by Default:** Your photos, face data, and analysis never leave your machine.
2. **Never Auto-Deletes:** No file is ever removed or moved without your explicit review and confirmation.
3. **Safe Cleanup:** Files are moved to the **Windows Recycle Bin**, allowing you to easily restore any photo.
4. **True Content Hashing:** Uses full SHA-256 content hashes; never treats identical file sizes as duplicates without cryptographic verification.
5. **Real Visual Similarity:** Spots cropped, compressed, or burst-mode shots even if filenames and resolutions differ.
6. **Local Face Clustering:** Automatically groups matching faces into person albums (Person 01, Person 02...) with no cloud service.
7. **No Accounts or Cloud:** No signup, no login, no remote database.
8. **Optional External AI:** Optional vision APIs (Google Gemini, OpenAI, Claude) can be connected if desired, but remain strictly disabled by default.
9. **OS-Level Key Security:** External API keys are stored encrypted inside Windows Credential Manager, never in plain-text logs or code.
10. **Low Memory Footprint:** Built to smoothly handle 10,000+ photos on a standard laptop (e.g., Intel i5, 16GB RAM) without memory crashes.

---

## 💡 How to Use PhotoVault (उपयोग कैसे करें — आसान स्टेप्स)

### Step 1: Add Photo Folders
- Open PhotoVault and click **"Add Folder"**.
- Select one or more folders from your computer (e.g., `Pictures`, `DCIM`, or an external hard drive).
- Click **"Scan Selected Folders"**.
- Watch the live progress bar: PhotoVault scans nested folders, creates thumbnails, extracts perceptual hashes, and detects faces in real time.

### Step 2: Review Exact Duplicates
- Click **"Duplicates"** in the sidebar.
- Photos with identical SHA-256 byte hashes are grouped together.
- Compare side-by-side: view file paths, resolutions, and file sizes.
- Click **"Move Redundant to Recycle Bin"** to reclaim disk space safely.

### Step 3: Find Similar Photos & Burst Shots
- Click **"Similar Photos"** in the sidebar.
- Choose between **Strict**, **Balanced**, or **Loose** matching.
- Find burst shots taken seconds apart or images with subtle edits.

### Step 4: Explore People Albums (Faces)
- Click **"Faces / People"** in the sidebar.
- Browse detected individuals (*Person 01*, *Person 02*...).
- Click any person to see all photographs where they appear.
- Click **Rename** to set their actual name (e.g., "Alice", "Mom", "John").
- Click **Merge** if two clusters belong to the same person.

### Step 5: Safe Photo Organization
- Click **"Organize"** to preview suggested folder structures by Year, Month, Person, or Category.
- Review the **Dry-Run Preview** table. Original files remain untouched until you explicitly confirm!

---

## 🛠️ Developer Guide (Source Build & Testing)

If you wish to modify the source code or build the installer yourself:

### 1. Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10+
- Node.js 18+
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (for compiling the installer)

### 2. Setup Virtual Environment
```powershell
# Clone the repository
git clone https://github.com/kunalrai1234/PhotoVault.git
cd PhotoVault

# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Python requirements
pip install -r backend/requirements.txt
```

### 3. Build Desktop Frontend
```powershell
npm install
npm run build
```

### 4. Run Automated Tests
```powershell
pytest backend/tests/ -v
```

### 5. Build Standalone Application (.exe)
```powershell
.\venv\Scripts\pyinstaller.exe --distpath dist-app --workpath build-app -y photovault.spec
```

### 6. Build Windows Installer (.exe)
```powershell
& "C:\Users\kamle\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss
```
The compiled installer will be available at:
`release/PhotoVault-Setup-x64.exe`

---

## 📜 License & Acknowledgments

- Licensed under the [MIT License](LICENSE).
- Local Face Detection & Recognition models: OpenCV YuNet and OpenCV SFace (Apache 2.0).
- Privacy Guarantee: Zero telemetry, 100% offline.
