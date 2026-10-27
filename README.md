# 📸 PhotoVault Local AI

> **Privacy-First, 100% Offline Desktop Photo Organizer with Visual Similarity & Local Face Recognition.**  
> *आपके कंप्यूटर पर पूरी तरह सुरक्षित और प्राइवेट फ़ोटो आर्गेनाइज़र — बिना किसी इंटरनेट या क्लाउड के।*

---

## 🌟 What is PhotoVault Local AI? (यह क्या है?)

**PhotoVault Local AI** is a professional desktop software designed to scan and organize your personal photos locally on your Windows PC. 

Unlike traditional software that relies on filenames or file sizes, PhotoVault uses **actual visual content analysis**, **cryptographic hashing (SHA-256)**, **perceptual hashing (pHash/dHash)**, and **local AI models** to find exact duplicates, identify near-identical burst photos, detect faces, and group them into people — **all completely offline on your own CPU**.

### 🔒 10 Core Privacy & Safety Guarantees
1. **100% Offline by Default:** Your photos, face data, and analysis never leave your machine.
2. **Never Auto-Deletes:** No file is ever removed or moved without your explicit review and confirmation.
3. **Safe Cleanup:** Files are moved to the **Windows Recycle Bin**, allowing you to easily undo any action.
4. **True Content Hashing:** Uses full SHA-256 content hashes, never judging duplicates by identical file size alone.
5. **Real Visual Similarity:** Spots cropped, compressed, or burst-mode shots even if filenames and resolutions differ.
6. **Local Face Clustering:** Automatically groups matching faces into person albums (Person 01, Person 02...) with no cloud service.
7. **No Accounts or Cloud:** No signup, no login, no remote database.
8. **Optional External AI:** Optional vision APIs (Google Gemini, OpenAI, Claude) can be connected if desired, but remain strictly disabled by default.
9. **OS-Level Key Security:** External API keys are saved inside Windows Credential Manager, never in plain-text logs or code.
10. **Low Memory Footprint:** Built to smoothly handle 10,000+ photos on a standard laptop (e.g., Intel i5, 16GB RAM) without memory crashes.

---

## 📋 System Requirements (कंप्यूटर की आवश्यकताएँ)

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Processor:** Intel Core i5 (or equivalent AMD Ryzen)
- **RAM:** 8 GB minimum (16 GB recommended for 10,000+ photos)
- **Disk Space:** 500 MB free space (plus space for photo cache)
- **Tools Needed:**
  - [Python 3.10+](https://www.python.org/downloads/) (Make sure *"Add Python to PATH"* is checked)
  - [Node.js 18+](https://nodejs.org/) (LTS or Current)

---

## 🚀 Beginner Step-by-Step Setup Guide (आसान इंस्टॉलेशन गाइड)

Follow these simple steps in order:

### Step 1: Open PowerShell / Terminal in the Project Folder
Open your PowerShell or Command Prompt, and navigate to the project directory:
```powershell
cd D:\Project\PhotoVault
```

### Step 2: Set Up the Python Local AI Engine
Run the following commands to create a clean virtual environment and install dependencies:
```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip and install all required libraries
pip install -r backend/requirements.txt
```

### Step 3: Install Desktop Frontend Dependencies
In the same folder, run:
```powershell
npm install
```

### Step 4: Launch the Desktop Application
To start PhotoVault in Desktop mode:
```powershell
npm run dev:desktop
```
The desktop application window will open immediately! 🎉

---

## 💡 How to Use PhotoVault Local AI (उपयोग कैसे करें)

### 1. 📁 Scanning Folders
- Click **"Add Folder"** on the top toolbar or Dashboard.
- Choose any folder on your computer (e.g., `Pictures/Family` or `D:\Photos`).
- PhotoVault recursively scans every subfolder, indexes file metadata, generates high-speed 256px thumbnails, and calculates content hashes in the background.

### 2. 🔍 Finding Exact Duplicates
- Navigate to the **"Exact Duplicates"** tab in the left sidebar.
- Photos with matching SHA-256 content hashes are grouped together.
- Use the quick recommendation buttons:
  - **Keep Largest / Highest Resolution**
  - **Select Smaller Copies**
  - **Move to Recycle Bin** (Sends redundant copies safely to Windows Recycle Bin with one click).

### 3. 🖼️ Visual Similarity & Burst Shot Detection
- Navigate to **"Similar Photos"**.
- Adjust the sensitivity slider between **Strict**, **Balanced**, and **Loose**.
- PhotoVault groups images that look visually similar, such as multi-shot bursts, cropped variations, or resized copies.

### 4. 👤 Face-Wise Person Organizer
- Navigate to the **"Faces"** tab.
- PhotoVault detects all human faces in your pictures using local computer vision and clusters them into distinct individuals:
  - *Person 01 (120 photos)*
  - *Person 02 (85 photos)*
- You can:
  - Rename any person cluster (e.g., "Rahul", "Pooja").
  - Merge two clusters if they belong to the same individual.
  - Delete stored face embeddings anytime.

### 5. 🗂️ Safe Photo Organization
- Click **"Organize Photos"** to sort your photos by Person, Category, Date, or Visual Group.
- Choose:
  - **Virtual Organization:** Organizes photos inside the app without moving original files.
  - **Physical Copy / Move:** Creates organized folders (e.g., `Organized/People/Rahul/`).
- **Dry-Run Preview:** PhotoVault displays a complete preview list of all proposed file moves before executing anything. Nothing is moved without your approval.

---

## 🛠️ Project Architecture

```text
PhotoVault/
├── backend/                  # Python Local AI Core
│   ├── app.py                # Local IPC Server (127.0.0.1)
│   ├── requirements.txt      # Python dependencies
│   ├── core/
│   │   ├── scanner.py        # Recursive folder scanner & thumbnailer
│   │   ├── duplicates.py     # Content-based SHA-256 duplicate engine
│   │   ├── similarity.py     # Perceptual hashing (pHash) & vision embeddings
│   │   ├── faces.py          # OpenCV YuNet detection & SFace clustering
│   │   ├── categories.py     # Rule-based & local vision categorization
│   │   ├── organizer.py      # Safe file copy/move with dry-run preview
│   │   ├── cache.py          # JSON metadata & indexing cache
│   │   └── security.py       # Windows Credential Manager integration
│   └── adapters/             # Optional External AI (Disabled by default)
│       ├── gemini_adapter.py
│       ├── openai_adapter.py
│       └── claude_adapter.py
├── src/                      # Desktop UI (HTML5, Vanilla CSS, TypeScript)
│   ├── components/           # Sidebar, PhotoGrid, Inspector, Modals
│   ├── styles/               # Clean, neutral dark/light theme
│   └── main.ts               # App entrypoint
├── electron/                 # Desktop Shell wrapper
│   └── main.cjs              # Native window, folder dialogs, sidecar lifecycle
├── tests/                    # Automated test suites
├── package.json              # Build scripts and frontend dependencies
└── README.md                 # This documentation
```

---

## 📦 Building a Standalone Windows Installer (.exe)

When you are ready to distribute or install PhotoVault as a native Windows `.exe` application:

```powershell
npm run build:installer
```
This generates an installer inside the `dist-electron/` folder:
- `PhotoVault-Setup-1.0.0.exe` (Standalone Windows Installer)

---

## 🧪 Running Automated Tests

To verify that the scanner, duplicate detection, and face clustering engines work correctly:
```powershell
.\venv\Scripts\Activate.ps1
pytest backend/tests/
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).  
Local vision models used (OpenCV YuNet & SFace) are licensed under Apache 2.0.
