// PhotoVault Local AI Frontend Application
const API_BASE = "http://127.0.0.1:54321/api";

interface Photo {
  id: string;
  filename: string;
  path: string;
  relative_path: string;
  size: number;
  width: number;
  height: number;
  format: string;
  mtime: number;
  date_modified: string;
  sha256?: string;
  phash?: string;
  thumbnail?: string;
  tags?: string[];
  faces?: any[];
  is_corrupt?: boolean;
}

interface DuplicateGroup {
  group_id: string;
  hash: string;
  file_size: number;
  photos: Photo[];
  recommended_keep: string;
  suggested_redundant: string[];
  recoverable_bytes: number;
}

interface SimilarityGroup {
  group_id: string;
  category: string;
  mode: string;
  count: number;
  photos: Photo[];
  representative: Photo;
}

interface FaceCluster {
  cluster_id: string;
  name: string;
  face_count: number;
  photo_count: number;
  photos: string[];
  faces: any[];
}

class PhotoVaultApp {
  private currentView = "dashboard";
  private photos: Photo[] = [];
  private selectedPaths: Set<string> = new Set();
  private selectedPhoto: Photo | null = null;

  public get currentSelectedPhoto(): Photo | null {
    return this.selectedPhoto;
  }

  private duplicateGroups: DuplicateGroup[] = [];
  private similarityGroups: SimilarityGroup[] = [];
  private faceClusters: FaceCluster[] = [];
  private scannedFolders: string[] = [];

  constructor() {
    this.initEventListeners();
    this.refreshStatus();
    this.loadPhotos();
  }

  private initEventListeners() {
    // Navigation
    document.querySelectorAll(".nav-item").forEach((el) => {
      el.addEventListener("click", () => {
        const view = el.getAttribute("data-view");
        if (view) this.switchView(view);
      });
    });

    // Theme Toggle
    document.getElementById("btn-theme-toggle")?.addEventListener("click", () => {
      const html = document.documentElement;
      const current = html.getAttribute("data-theme") || "dark";
      html.setAttribute("data-theme", current === "dark" ? "light" : "dark");
    });

    // Actions
    document.getElementById("btn-add-folder")?.addEventListener("click", () => this.promptAddFolder());
    document.getElementById("btn-scan")?.addEventListener("click", () => this.runScan());
    document.getElementById("btn-organize")?.addEventListener("click", () => this.showOrganizeModal());
    document.getElementById("btn-ai-settings")?.addEventListener("click", () => this.showAISettingsModal());

    // Toolbar
    const searchInput = document.getElementById("input-search") as HTMLInputElement;
    searchInput?.addEventListener("input", () => this.handleSearch(searchInput.value));

    document.getElementById("btn-select-all")?.addEventListener("click", () => this.toggleSelectAll());
    document.getElementById("btn-recycle-selected")?.addEventListener("click", () => this.recycleSelected());

    const sortSelect = document.getElementById("select-sort") as HTMLSelectElement;
    sortSelect?.addEventListener("change", () => this.sortPhotos(sortSelect.value));
  }

  private async refreshStatus() {
    try {
      const res = await fetch(`${API_BASE}/status`);
      if (res.ok) {
        const data = await res.json();
        document.getElementById("badge-total-photos")!.innerText = data.total_photos;
        document.getElementById("badge-duplicates")!.innerText = data.duplicate_groups_count;
        document.getElementById("badge-similar")!.innerText = data.similarity_groups_count;
        document.getElementById("badge-faces")!.innerText = data.face_clusters_count;
      }
    } catch (e) {
      console.warn("Backend server not yet ready, retrying...", e);
    }
  }

  private async loadPhotos() {
    try {
      const res = await fetch(`${API_BASE}/photos`);
      if (res.ok) {
        const data = await res.json();
        this.photos = data.photos || [];
        this.renderCurrentView();
        this.refreshStatus();
      }
    } catch (e) {
      console.error("Failed to load photos", e);
    }
  }

  private switchView(viewName: string) {
    this.currentView = viewName;
    document.querySelectorAll(".nav-item").forEach((el) => {
      el.classList.toggle("active", el.getAttribute("data-view") === viewName);
    });
    this.renderCurrentView();
  }

  private renderCurrentView() {
    const root = document.getElementById("view-root");
    if (!root) return;

    if (this.currentView === "dashboard") {
      this.renderDashboard(root);
    } else if (this.currentView === "all-photos") {
      this.renderPhotoGrid(root, this.photos);
    } else if (this.currentView === "exact-duplicates") {
      this.renderDuplicatesView(root);
    } else if (this.currentView === "similar-photos") {
      this.renderSimilarityView(root);
    } else if (this.currentView === "faces") {
      this.renderFacesView(root);
    } else if (this.currentView === "categories") {
      this.renderCategoriesView(root);
    } else if (this.currentView === "cleanup") {
      this.renderCleanupView(root);
    }
  }

  // --- Views ---

  private renderDashboard(root: HTMLElement) {
    root.innerHTML = `
      <div style="max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px;">
        <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-lg); padding: 24px;">
          <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 8px;">Welcome to PhotoVault Local AI</h2>
          <p style="color:var(--text-muted); font-size:13px; line-height:1.6;">
            Your privacy-first, 100% offline desktop photo manager. Scans folders recursively, detects exact byte duplicates via SHA-256, groups burst shots with perceptual hashing, and clusters people locally using local AI vision models.
          </p>
          
          <div style="margin-top:16px; display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
            <button class="btn btn-primary" onclick="app.promptAddFolder()">📂 Select Folder (Browse)</button>
            <span style="font-size:12px; color:var(--text-dim);">or enter path:</span>
            <input type="text" id="manual-folder-input" placeholder="e.g. D:\\Photos or C:\\Users\\...\\Pictures" class="btn" style="flex:1; min-width:240px; text-align:left; cursor:text;"/>
            <button class="btn" onclick="app.addManualFolder()">Add & Scan</button>
          </div>
        </div>

        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:16px;">
          <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px;">
            <div style="color:var(--text-dim); font-size:12px;">TOTAL INDEXED PHOTOS</div>
            <div style="font-size:28px; font-weight:700; margin-top:4px;">${this.photos.length}</div>
          </div>
          <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px;">
            <div style="color:var(--text-dim); font-size:12px;">EXACT DUPLICATE GROUPS</div>
            <div style="font-size:28px; font-weight:700; margin-top:4px; color:var(--warning);">${this.duplicateGroups.length}</div>
          </div>
          <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px;">
            <div style="color:var(--text-dim); font-size:12px;">SIMILAR BURST GROUPS</div>
            <div style="font-size:28px; font-weight:700; margin-top:4px; color:var(--accent);">${this.similarityGroups.length}</div>
          </div>
          <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px;">
            <div style="color:var(--text-dim); font-size:12px;">FACE CLUSTERS</div>
            <div style="font-size:28px; font-weight:700; margin-top:4px; color:var(--success);">${this.faceClusters.length}</div>
          </div>
        </div>

        <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px;">
          <div style="font-size:14px; font-weight:600; margin-bottom:12px;">Scanned Root Folders</div>
          ${
            this.scannedFolders.length === 0
              ? '<p style="color:var(--text-dim); font-size:13px;">No folders added yet. Click "Select Folder (Browse)" above to select your photos.</p>'
              : `<ul style="font-size:13px; list-style:none; display:flex; flex-direction:column; gap:6px;">
                  ${this.scannedFolders.map((f) => `<li style="font-family:monospace; background:var(--bg-tertiary); padding:6px 10px; border-radius:var(--radius-sm);">📁 ${f}</li>`).join("")}
                </ul>`
          }
        </div>
      </div>
    `;
  }

  public addManualFolder() {
    const input = document.getElementById("manual-folder-input") as HTMLInputElement;
    if (input && input.value && input.value.trim()) {
      const val = input.value.trim();
      if (!this.scannedFolders.includes(val)) {
        this.scannedFolders.push(val);
      }
      this.runScan();
    }
  }

  private renderPhotoGrid(root: HTMLElement, photoList: Photo[]) {
    if (photoList.length === 0) {
      root.innerHTML = `<div style="text-align:center; padding: 60px; color:var(--text-dim);">No photos found in this view. Click "Add Folder" to scan your images.</div>`;
      return;
    }

    const grid = document.createElement("div");
    grid.className = "photo-grid";

    photoList.forEach((photo) => {
      const card = document.createElement("div");
      card.className = "photo-card" + (this.selectedPaths.has(photo.path) ? " selected" : "");
      
      const thumbUrl = `http://127.0.0.1:54321/thumbnail/${photo.id}.webp`;

      card.innerHTML = `
        <div class="photo-thumb-wrap">
          <img src="${thumbUrl}" alt="${photo.filename}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'100\\' height=\\'100\\'><rect fill=\\'%23333\\' width=\\'100\\' height=\\'100\\'/></svg>'"/>
        </div>
        <div class="photo-info">
          <div class="photo-name" title="${photo.filename}">${photo.filename}</div>
          <div class="photo-sub">${(photo.size / (1024 * 1024)).toFixed(2)} MB • ${photo.width}x${photo.height}</div>
        </div>
      `;

      card.addEventListener("click", (e) => {
        if (e.ctrlKey || e.metaKey) {
          if (this.selectedPaths.has(photo.path)) {
            this.selectedPaths.delete(photo.path);
          } else {
            this.selectedPaths.add(photo.path);
          }
          this.updateSelectionToolbar();
          card.classList.toggle("selected", this.selectedPaths.has(photo.path));
        } else {
          this.selectPhoto(photo);
        }
      });

      grid.appendChild(card);
    });

    root.innerHTML = "";
    root.appendChild(grid);
  }

  private async renderDuplicatesView(root: HTMLElement) {
    root.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-dim);">Loading exact duplicate groups...</div>`;
    const res = await fetch(`${API_BASE}/duplicates`);
    if (!res.ok) return;
    const data = await res.json();
    this.duplicateGroups = data.groups || [];

    if (this.duplicateGroups.length === 0) {
      root.innerHTML = `
        <div style="text-align:center; padding:60px;">
          <div style="font-size:36px; margin-bottom:10px;">🎉</div>
          <h3>No Exact Duplicates Found!</h3>
          <p style="color:var(--text-dim); font-size:13px; margin-top:6px;">Your photo library has no redundant byte-for-byte duplicate images.</p>
        </div>`;
      return;
    }

    let html = `<div style="display:flex; flex-direction:column; gap:20px; max-width:1000px; margin:0 auto;">`;
    this.duplicateGroups.forEach((group, idx) => {
      const recoverableMB = (group.recoverable_bytes / (1024 * 1024)).toFixed(2);
      html += `
        <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div>
              <span style="font-weight:600; font-size:14px;">Duplicate Group #${idx + 1}</span>
              <span style="color:var(--text-dim); font-size:12px; margin-left:8px;">(${group.photos.length} copies, ${recoverableMB} MB recoverable)</span>
            </div>
            <div style="display:flex; gap:8px;">
              <button class="btn btn-danger" style="font-size:11px;" onclick="app.recycleRedundant('${group.group_id}')">Move Redundant to Recycle Bin</button>
            </div>
          </div>
          <div style="display:flex; gap:12px; overflow-x:auto; padding-bottom:8px;">
            ${group.photos.map((p) => {
              const isKeep = p.path === group.recommended_keep;
              const thumb = `http://127.0.0.1:54321/thumbnail/${p.id}.webp`;
              return `
                <div style="width:160px; flex-shrink:0; background:var(--bg-tertiary); border:1px solid ${isKeep ? 'var(--success)' : 'var(--border-subtle)'}; border-radius:var(--radius-sm); padding:6px;">
                  <img src="${thumb}" style="width:100%; height:120px; object-fit:cover; border-radius:var(--radius-sm);"/>
                  <div style="font-size:11px; font-weight:600; margin-top:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${p.filename}</div>
                  <div style="font-size:10px; color:var(--text-dim);">${(p.size / (1024 * 1024)).toFixed(2)} MB • ${p.width}x${p.height}</div>
                  ${isKeep ? '<span class="badge" style="background:var(--success); color:white; font-size:9px; margin-top:4px; display:inline-block;">Keep (Highest Res)</span>' : '<span class="badge" style="background:var(--danger); color:white; font-size:9px; margin-top:4px; display:inline-block;">Redundant</span>'}
                </div>
              `;
            }).join("")}
          </div>
        </div>
      `;
    });
    html += `</div>`;
    root.innerHTML = html;
  }

  private async renderSimilarityView(root: HTMLElement) {
    root.innerHTML = `
      <div style="max-width:1000px; margin:0 auto; display:flex; flex-direction:column; gap:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-secondary); padding:12px 16px; border-radius:var(--radius-md); border:1px solid var(--border-color);">
          <div>
            <div style="font-weight:600; font-size:14px;">Visual Similarity & Burst Shots</div>
            <div style="color:var(--text-dim); font-size:12px;">Identifies cropped, compressed, or burst-mode shots using perceptual hashing.</div>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <label style="font-size:12px; color:var(--text-muted);">Threshold:</label>
            <select class="btn" id="select-similarity-mode" onchange="app.changeSimilarityMode(this.value)">
              <option value="strict">Strict (Near Burst Only)</option>
              <option value="balanced" selected>Balanced</option>
              <option value="loose">Loose (Broader Variations)</option>
            </select>
          </div>
        </div>
        <div id="similarity-groups-content">Loading similar photos...</div>
      </div>
    `;

    this.loadSimilarityContent("balanced");
  }

  public async changeSimilarityMode(mode: string) {
    this.loadSimilarityContent(mode);
  }

  private async loadSimilarityContent(mode: string) {
    const container = document.getElementById("similarity-groups-content");
    if (!container) return;

    const res = await fetch(`${API_BASE}/similarity?mode=${mode}`);
    if (!res.ok) return;
    const data = await res.json();
    this.similarityGroups = data.groups || [];

    if (this.similarityGroups.length === 0) {
      container.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-dim);">No visually similar clusters found with ${mode} threshold.</div>`;
      return;
    }

    let html = "";
    this.similarityGroups.forEach((group, idx) => {
      html += `
        <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; margin-bottom:16px;">
          <div style="font-weight:600; font-size:14px; margin-bottom:10px;">${group.category} #${idx + 1} (${group.count} photos)</div>
          <div style="display:flex; gap:12px; overflow-x:auto;">
            ${group.photos.map((p) => {
              const thumb = `http://127.0.0.1:54321/thumbnail/${p.id}.webp`;
              return `
                <div style="width:140px; flex-shrink:0;">
                  <img src="${thumb}" style="width:100%; height:110px; object-fit:cover; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);"/>
                  <div style="font-size:11px; font-weight:500; margin-top:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${p.filename}</div>
                  <div style="font-size:10px; color:var(--text-dim);">${p.width}x${p.height}</div>
                </div>
              `;
            }).join("")}
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  }

  private async renderFacesView(root: HTMLElement) {
    root.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-dim);">Loading face clusters...</div>`;
    const res = await fetch(`${API_BASE}/faces`);
    if (!res.ok) return;
    const data = await res.json();
    this.faceClusters = data.clusters || [];

    if (this.faceClusters.length === 0) {
      root.innerHTML = `
        <div style="text-align:center; padding:60px;">
          <div style="font-size:36px; margin-bottom:10px;">👤</div>
          <h3>No Faces Detected Yet</h3>
          <p style="color:var(--text-dim); font-size:13px; margin-top:6px;">Scan photos containing human faces to automatically cluster them into person albums.</p>
        </div>`;
      return;
    }

    let html = `
      <div style="max-width:1000px; margin:0 auto;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
          <h3 style="font-size:16px; font-weight:600;">People Albums (${this.faceClusters.length})</h3>
        </div>
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:16px;">
    `;

    this.faceClusters.forEach((cluster) => {
      const rep = cluster.faces[0];
      const thumb = rep ? `http://127.0.0.1:54321/thumbnail/${rep.face_id.split('_face_')[0]}.webp` : '';
      html += `
        <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); overflow:hidden; padding:12px;">
          <div style="width:100%; height:160px; background:var(--bg-tertiary); border-radius:var(--radius-sm); overflow:hidden; display:flex; align-items:center; justify-content:center;">
            ${thumb ? `<img src="${thumb}" style="width:100%; height:100%; object-fit:cover;"/>` : '👤'}
          </div>
          <div style="margin-top:10px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:600; font-size:13px;">${cluster.name}</div>
              <div style="color:var(--text-dim); font-size:11px;">${cluster.photo_count} photos</div>
            </div>
            <button class="btn" style="font-size:11px; padding:2px 8px;" onclick="app.renamePersonPrompt('${cluster.cluster_id}', '${cluster.name}')">✏️ Rename</button>
          </div>
        </div>
      `;
    });

    html += `</div></div>`;
    root.innerHTML = html;
  }

  private renderCategoriesView(root: HTMLElement) {
    const categoryMap: { [cat: string]: Photo[] } = {};
    this.photos.forEach((p) => {
      const tags = p.tags && p.tags.length > 0 ? p.tags : ["Other"];
      tags.forEach((t) => {
        if (!categoryMap[t]) categoryMap[t] = [];
        categoryMap[t].push(p);
      });
    });

    let html = `
      <div style="max-width:1000px; margin:0 auto;">
        <h3 style="font-size:16px; font-weight:600; margin-bottom:16px;">AI Photo Categories (Local Offline)</h3>
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:14px;">
    `;

    Object.entries(categoryMap).forEach(([catName, pList]) => {
      const rep = pList[0];
      const thumb = rep ? `http://127.0.0.1:54321/thumbnail/${rep.id}.webp` : '';
      html += `
        <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-md); overflow:hidden; cursor:pointer;" onclick="app.filterByCategory('${catName}')">
          <div style="width:100%; height:130px; background:var(--bg-tertiary); overflow:hidden;">
            ${thumb ? `<img src="${thumb}" style="width:100%; height:100%; object-fit:cover;"/>` : ''}
          </div>
          <div style="padding:10px;">
            <div style="font-weight:600; font-size:13px;">${catName}</div>
            <div style="color:var(--text-dim); font-size:11px;">${pList.length} photos</div>
          </div>
        </div>
      `;
    });

    html += `</div></div>`;
    root.innerHTML = html;
  }

  private renderCleanupView(root: HTMLElement) {
    const totalRecoverable = this.duplicateGroups.reduce((acc, g) => acc + g.recoverable_bytes, 0);
    const recoverableMB = (totalRecoverable / (1024 * 1024)).toFixed(2);

    root.innerHTML = `
      <div style="max-width:800px; margin:0 auto; background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:24px;">
        <h3 style="font-size:18px; font-weight:600; margin-bottom:8px;">🗑️ Safe Storage Cleanup</h3>
        <p style="color:var(--text-muted); font-size:13px; line-height:1.6;">
          PhotoVault guarantees zero accidental data loss. All deletions are sent safely to the <strong>Windows Recycle Bin</strong>, meaning you can easily restore any file anytime.
        </p>

        <div style="display:flex; gap:20px; margin:20px 0; background:var(--bg-tertiary); padding:16px; border-radius:var(--radius-md);">
          <div>
            <div style="color:var(--text-dim); font-size:12px;">POTENTIAL RECOVERABLE SPACE</div>
            <div style="font-size:24px; font-weight:700; color:var(--success); margin-top:4px;">${recoverableMB} MB</div>
          </div>
          <div>
            <div style="color:var(--text-dim); font-size:12px;">DUPLICATE GROUPS</div>
            <div style="font-size:24px; font-weight:700; color:var(--warning); margin-top:4px;">${this.duplicateGroups.length}</div>
          </div>
        </div>

        <div style="display:flex; gap:12px;">
          <button class="btn btn-danger" onclick="app.recycleAllDuplicates()">Move All Recommended Redundant to Recycle Bin</button>
          <button class="btn" onclick="app.switchView('exact-duplicates')">Review Groups Side-by-Side</button>
        </div>
      </div>
    `;
  }

  // --- Inspector ---

  private selectPhoto(photo: Photo) {
    this.selectedPhoto = photo;
    const preview = document.getElementById("inspector-preview");
    if (preview) {
      const thumb = `http://127.0.0.1:54321/thumbnail/${photo.id}.webp`;
      preview.innerHTML = `<img src="${thumb}" alt="${photo.filename}"/>`;
    }

    document.getElementById("insp-name")!.innerText = photo.filename;
    const pathEl = document.getElementById("insp-path")!;
    pathEl.innerText = photo.path;
    pathEl.setAttribute("title", photo.path);

    document.getElementById("insp-size")!.innerText = `${(photo.size / (1024 * 1024)).toFixed(2)} MB`;
    document.getElementById("insp-res")!.innerText = `${photo.width} × ${photo.height}`;
    document.getElementById("insp-date")!.innerText = photo.date_modified || "-";

    const shaEl = document.getElementById("insp-sha")!;
    shaEl.innerText = photo.sha256 ? `${photo.sha256.substring(0, 12)}...` : "Calculated on demand";
    shaEl.setAttribute("title", photo.sha256 || "");

    document.getElementById("insp-phash")!.innerText = photo.phash || "-";

    const tagsContainer = document.getElementById("insp-tags");
    if (tagsContainer) {
      const tags = photo.tags || ["Other"];
      tagsContainer.innerHTML = tags.map((t) => `<span class="tag-pill">${t}</span>`).join("");
    }

    // AI Vision Box
    const aiBox = document.getElementById("insp-ai-desc");
    if (aiBox) {
      aiBox.innerHTML = `
        <button class="btn btn-primary" style="width:100%; font-size:11px; margin-top:8px;" onclick="app.askGeminiForPhoto('${photo.path}')">
          ✨ Ask Gemini Vision to Describe Photo
        </button>
        <div id="ai-desc-text" style="font-size:11px; color:var(--text-muted); margin-top:8px; line-height:1.4;"></div>
      `;
    }
  }

  public async askGeminiForPhoto(imagePath: string) {
    const descEl = document.getElementById("ai-desc-text");
    if (descEl) descEl.innerText = "Analyzing with Google Gemini (gemini-3.5-flash)...";

    try {
      const res = await fetch(`${API_BASE}/ai/describe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_path: imagePath })
      });
      const data = await res.json();
      if (data.success && descEl) {
        descEl.innerHTML = `<strong>Gemini Vision:</strong><br/>${data.analysis}`;
      } else if (descEl) {
        descEl.innerText = `Error: ${data.error || "Failed to analyze"}`;
      }
    } catch (e: any) {
      if (descEl) descEl.innerText = `Error: ${e.message}`;
    }
  }

  // --- Folder & Scan Actions ---

  public async promptAddFolder() {
    let folderPath: string | null = null;
    
    // First try the native Windows Folder Picker API on the backend
    try {
      const res = await fetch(`${API_BASE}/pick-folder`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (data.folder) {
          folderPath = data.folder;
        }
      }
    } catch (e) {
      console.warn("Backend pick-folder failed, trying pywebview/prompt", e);
    }

    // Fallback if dialog cancelled or not opened
    if (!folderPath) {
      if ((window as any).pywebview && (window as any).pywebview.api) {
        folderPath = await (window as any).pywebview.api.select_folder();
      }
    }

    if (!folderPath) {
      const manual = prompt("Enter the absolute folder path to scan (e.g. D:\\Photos or C:\\Users\\...):");
      if (manual && manual.trim()) folderPath = manual.trim();
    }

    if (folderPath && folderPath.trim()) {
      const clean = folderPath.trim();
      if (!this.scannedFolders.includes(clean)) {
        this.scannedFolders.push(clean);
      }
      this.runScan();
    }
  }

  public async runScan() {
    if (this.scannedFolders.length === 0) {
      alert("Please add at least one folder to scan first.");
      return;
    }

    const statusText = document.getElementById("scan-status-text");
    if (statusText) statusText.innerText = "Scanning in progress...";

    try {
      const res = await fetch(`${API_BASE}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folders: this.scannedFolders })
      });
      if (res.ok) {
        const data = await res.json();
        if (statusText) statusText.innerText = `Scan complete (${data.total_scanned} photos)`;
        await this.loadPhotos();
        this.switchView("all-photos");
      } else {
        const err = await res.json();
        alert(`Scan failed: ${err.error || "Unknown error"}`);
        if (statusText) statusText.innerText = "Scan failed";
      }
    } catch (e: any) {
      if (statusText) statusText.innerText = "Scan error";
      alert(`Could not connect to scan engine: ${e.message}`);
    }
  }

  public showOrganizeModal() {
    const modal = document.getElementById("modal-container")!;
    modal.innerHTML = `
      <div class="modal-overlay">
        <div class="modal-dialog">
          <div class="modal-header">
            <span>🗂️ Safe Photo Organization</span>
            <button class="btn" style="padding:2px 6px;" onclick="app.closeModal()">✕</button>
          </div>
          <div class="modal-body">
            <p style="color:var(--text-muted); margin-bottom:14px;">
              Create clean output folders (e.g. Organized/People, Organized/Nature). Review the full plan before copying or moving files.
            </p>
            <div style="display:flex; flex-direction:column; gap:10px;">
              <label>Target Destination Folder:
                <input type="text" id="org-target" class="btn" style="width:100%; text-align:left; margin-top:4px;" value="D:\\OrganizedPhotos"/>
              </label>
              <label>Group Photos By:
                <select id="org-strategy" class="btn" style="width:100%; margin-top:4px;">
                  <option value="category">Category (Nature, Food, Travel, etc.)</option>
                  <option value="person">Person Album (Face Clusters)</option>
                  <option value="date">Date (Year / Month)</option>
                  <option value="duplicates">Separate Exact Duplicates</option>
                </select>
              </label>
              <label>Action:
                <select id="org-action" class="btn" style="width:100%; margin-top:4px;">
                  <option value="copy">Copy (Safest — keeps original files untouched)</option>
                  <option value="move">Move</option>
                </select>
              </label>
            </div>
            <div id="org-preview-area" style="margin-top:16px;"></div>
          </div>
          <div class="modal-footer">
            <button class="btn" onclick="app.generateOrganizePlan()">Generate Plan Preview</button>
            <button class="btn btn-primary" id="btn-exec-plan" style="display:none;" onclick="app.executeOrganizePlan()">Execute Confirmed Plan</button>
          </div>
        </div>
      </div>
    `;
  }

  public async generateOrganizePlan() {
    const target = (document.getElementById("org-target") as HTMLInputElement).value;
    const strategy = (document.getElementById("org-strategy") as HTMLSelectElement).value;
    const action = (document.getElementById("org-action") as HTMLSelectElement).value;

    const res = await fetch(`${API_BASE}/organize/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_root: target, group_by: strategy, action })
    });

    if (res.ok) {
      const data = await res.json();
      (window as any)._currentPlan = data.plan;
      const previewArea = document.getElementById("org-preview-area")!;
      previewArea.innerHTML = `
        <div style="border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:10px; max-height:200px; overflow-y:auto; background:var(--bg-tertiary);">
          <div style="font-weight:600; font-size:12px; margin-bottom:6px;">Plan Preview (${data.total_actions} actions planned):</div>
          <ul style="font-size:11px; font-family:monospace; list-style:none;">
            ${data.plan.slice(0, 20).map((p: any) => `<li>${p.action.toUpperCase()}: ${p.source} ➔ ${p.destination}</li>`).join("")}
            ${data.plan.length > 20 ? `<li>... and ${data.plan.length - 20} more files</li>` : ''}
          </ul>
        </div>
      `;
      document.getElementById("btn-exec-plan")!.style.display = "inline-flex";
    }
  }

  public async executeOrganizePlan() {
    const plan = (window as any)._currentPlan;
    if (!plan) return;

    const res = await fetch(`${API_BASE}/organize/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan })
    });

    if (res.ok) {
      const data = await res.json();
      alert(`Organization Complete! Success: ${data.success}, Failed: ${data.failed}`);
      this.closeModal();
    }
  }

  public showAISettingsModal() {
    const modal = document.getElementById("modal-container")!;
    modal.innerHTML = `
      <div class="modal-overlay">
        <div class="modal-dialog">
          <div class="modal-header">
            <span>⚙️ AI Provider Settings</span>
            <button class="btn" style="padding:2px 6px;" onclick="app.closeModal()">✕</button>
          </div>
          <div class="modal-body">
            <div style="background:var(--bg-tertiary); border-left:3px solid var(--accent); padding:10px; font-size:12px; margin-bottom:14px;">
              🔒 <strong>Strict Privacy Notice:</strong> PhotoVault Local AI works 100% offline. Local face clustering and duplicate detection runs on your CPU. External vision APIs (Google Gemini) are optional. Keys are saved in Windows Credential Manager.
            </div>

            <div style="display:flex; flex-direction:column; gap:12px;">
              <div style="border:1px solid var(--border-color); border-radius:var(--radius-md); padding:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div style="font-weight:600; font-size:13px;">Google Gemini (Active: gemini-3.5-flash)</div>
                  <span class="badge" style="background:var(--success); color:white;">Configured ✓</span>
                </div>
                <div style="display:flex; gap:8px; margin-top:8px;">
                  <input type="password" id="key-gemini" placeholder="Enter your Gemini API Key" class="btn" style="flex:1; text-align:left;"/>
                  <button class="btn" onclick="app.saveKey('gemini')">Save Key</button>
                  <button class="btn btn-primary" onclick="app.testKey('gemini')">Test Connection</button>
                </div>
              </div>

              <div style="border:1px solid var(--border-color); border-radius:var(--radius-md); padding:12px;">
                <div style="font-weight:600; font-size:13px;">OpenAI / Compatible (GPT-4o)</div>
                <div style="display:flex; gap:8px; margin-top:8px;">
                  <input type="password" id="key-openai" placeholder="Enter OpenAI API Key" class="btn" style="flex:1; text-align:left;"/>
                  <button class="btn" onclick="app.saveKey('openai')">Save Key</button>
                  <button class="btn" onclick="app.testKey('openai')">Test</button>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn" onclick="app.closeModal()">Done</button>
          </div>
        </div>
      </div>
    `;
  }

  public async saveKey(provider: string) {
    const input = document.getElementById(`key-${provider}`) as HTMLInputElement;
    if (!input || !input.value) return;

    const res = await fetch(`${API_BASE}/ai/save-key`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, api_key: input.value, enabled: true })
    });

    if (res.ok) {
      alert(`${provider.toUpperCase()} key securely stored in Windows Credential Vault!`);
    }
  }

  public async testKey(provider: string) {
    const res = await fetch(`${API_BASE}/ai/test-connection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider })
    });
    const data = await res.json();
    alert(data.message || data.error);
  }

  public closeModal() {
    const modal = document.getElementById("modal-container");
    if (modal) modal.innerHTML = "";
  }

  public async recycleRedundant(groupId: string) {
    const group = this.duplicateGroups.find((g) => g.group_id === groupId);
    if (!group) return;

    if (!confirm(`Send ${group.suggested_redundant.length} redundant copies to Windows Recycle Bin?`)) {
      return;
    }

    const res = await fetch(`${API_BASE}/cleanup/recycle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ files: group.suggested_redundant })
    });

    if (res.ok) {
      alert("Redundant copies safely moved to Windows Recycle Bin!");
      await this.loadPhotos();
    }
  }

  public async recycleAllDuplicates() {
    const allRedundant = this.duplicateGroups.flatMap((g) => g.suggested_redundant);
    if (allRedundant.length === 0) return;

    if (!confirm(`Are you sure you want to move all ${allRedundant.length} redundant duplicate copies to Windows Recycle Bin?`)) {
      return;
    }

    const res = await fetch(`${API_BASE}/cleanup/recycle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ files: allRedundant })
    });

    if (res.ok) {
      alert("All duplicates safely moved to Windows Recycle Bin!");
      await this.loadPhotos();
    }
  }

  public async renamePersonPrompt(clusterId: string, currentName: string) {
    const newName = prompt("Enter new name for this person:", currentName);
    if (newName && newName.trim() && newName !== currentName) {
      await fetch(`${API_BASE}/faces/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cluster_id: clusterId, name: newName.trim() })
      });
      this.renderFacesView(document.getElementById("view-root")!);
    }
  }

  public filterByCategory(categoryName: string) {
    this.switchView("all-photos");
    const filtered = this.photos.filter((p) => (p.tags || []).includes(categoryName));
    this.renderPhotoGrid(document.getElementById("view-root")!, filtered);
  }

  private handleSearch(query: string) {
    const q = query.toLowerCase();
    const filtered = this.photos.filter((p) => p.filename.toLowerCase().includes(q));
    this.renderPhotoGrid(document.getElementById("view-root")!, filtered);
  }

  private sortPhotos(criterion: string) {
    if (criterion === "date-desc") {
      this.photos.sort((a, b) => (b.mtime || 0) - (a.mtime || 0));
    } else if (criterion === "date-asc") {
      this.photos.sort((a, b) => (a.mtime || 0) - (b.mtime || 0));
    } else if (criterion === "size-desc") {
      this.photos.sort((a, b) => b.size - a.size);
    } else if (criterion === "name-asc") {
      this.photos.sort((a, b) => a.filename.localeCompare(b.filename));
    }
    this.renderCurrentView();
  }

  private toggleSelectAll() {
    if (this.selectedPaths.size === this.photos.length) {
      this.selectedPaths.clear();
    } else {
      this.photos.forEach((p) => this.selectedPaths.add(p.path));
    }
    this.updateSelectionToolbar();
    this.renderCurrentView();
  }

  private updateSelectionToolbar() {
    const btnRecycle = document.getElementById("btn-recycle-selected");
    if (btnRecycle) {
      btnRecycle.style.display = this.selectedPaths.size > 0 ? "inline-flex" : "none";
      btnRecycle.innerText = `Recycle Selected (${this.selectedPaths.size})`;
    }
  }

  private async recycleSelected() {
    const list = Array.from(this.selectedPaths);
    if (!confirm(`Move ${list.length} selected photos to Windows Recycle Bin?`)) return;

    const res = await fetch(`${API_BASE}/cleanup/recycle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ files: list })
    });

    if (res.ok) {
      this.selectedPaths.clear();
      this.updateSelectionToolbar();
      await this.loadPhotos();
    }
  }
}

const app = new PhotoVaultApp();
(window as any).app = app;
