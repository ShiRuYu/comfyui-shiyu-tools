/**
 * Shiyu Tools — ComfyUI Enterprise Plugin Framework
 *
 * Frontend extension that adds:
 * - Floating Prompt Manager panel
 * - Floating Group Manager panel
 * - Node context menu integration
 * - Communication with Python API backend
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// ────────────────────────────────────────────
// 常量
// ────────────────────────────────────────────

const EXT_NAME = "ShiyuTools";
const BASE_URL = "/shiyu-tools";

// ────────────────────────────────────────────
// Toast 通知
// ────────────────────────────────────────────

let _toastContainer = null;

function toast(msg, type = "info", duration = 3000) {
    if (!_toastContainer) {
        _toastContainer = document.createElement("div");
        _toastContainer.className = "shiyu-toast";
        document.body.appendChild(_toastContainer);
    }
    const el = document.createElement("div");
    el.className = `shiyu-toast-msg ${type}`;
    el.textContent = msg;
    _toastContainer.appendChild(el);
    setTimeout(() => { el.remove(); }, duration);
}

// ────────────────────────────────────────────
// API 层
// ────────────────────────────────────────────

const ShiyuAPI = {
    // ── Prompt ──
    async listPrompts(query = "", tags = [], favorites = false) {
        const params = new URLSearchParams();
        if (query) params.set("query", query);
        if (tags.length) params.set("tags", tags.join(","));
        if (favorites) params.set("favorites", "true");
        const res = await api.fetchApi(`${BASE_URL}/prompts?${params}`);
        return res.json();
    },
    async createPrompt(data) {
        const res = await api.fetchApi(`${BASE_URL}/prompts`, {
            method: "POST",
            body: JSON.stringify(data),
        });
        return res.json();
    },
    async updatePrompt(id, data) {
        const res = await api.fetchApi(`${BASE_URL}/prompts/${id}`, {
            method: "PUT",
            body: JSON.stringify(data),
        });
        return res.json();
    },
    async deletePrompt(id) {
        const res = await api.fetchApi(`${BASE_URL}/prompts/${id}`, { method: "DELETE" });
        return res.json();
    },
    async toggleFavorite(id) {
        const res = await api.fetchApi(`${BASE_URL}/prompts/${id}/favorite`, { method: "POST" });
        return res.json();
    },
    async addTag(id, tag) {
        const res = await api.fetchApi(`${BASE_URL}/prompts/${id}/tags`, {
            method: "POST",
            body: JSON.stringify({ tag }),
        });
        return res.json();
    },
    async removeTag(id, tag) {
        const res = await api.fetchApi(`${BASE_URL}/prompts/${id}/tags/${encodeURIComponent(tag)}`, { method: "DELETE" });
        return res.json();
    },
    async getAllTags() {
        const res = await api.fetchApi(`${BASE_URL}/prompts/tags`);
        return res.json();
    },

    // ── Group ──
    async listGroups() {
        const res = await api.fetchApi(`${BASE_URL}/groups`);
        return res.json();
    },
    async createGroup(data) {
        const res = await api.fetchApi(`${BASE_URL}/groups`, {
            method: "POST",
            body: JSON.stringify(data),
        });
        return res.json();
    },
    async deleteGroup(id) {
        const res = await api.fetchApi(`${BASE_URL}/groups/${id}`, { method: "DELETE" });
        return res.json();
    },
    async addNodesToGroup(groupId, nodeIds) {
        const res = await api.fetchApi(`${BASE_URL}/groups/${groupId}/nodes`, {
            method: "POST",
            body: JSON.stringify({ nodeIds }),
        });
        return res.json();
    },
    async removeNodesFromGroup(groupId, nodeIds) {
        const res = await api.fetchApi(`${BASE_URL}/groups/${groupId}/nodes`, {
            method: "DELETE",
            body: JSON.stringify({ nodeIds }),
        });
        return res.json();
    },
    async locateGroup(groupId) {
        const res = await api.fetchApi(`${BASE_URL}/groups/${groupId}/locate`, { method: "POST" });
        return res.json();
    },
    async toggleCollapse(groupId) {
        const res = await api.fetchApi(`${BASE_URL}/groups/${groupId}/toggle-collapse`, { method: "POST" });
        return res.json();
    },
    async toggleLock(groupId) {
        const res = await api.fetchApi(`${BASE_URL}/groups/${groupId}/toggle-lock`, { method: "POST" });
        return res.json();
    },
    async moveGroup(groupId, targetParent) {
        const res = await api.fetchApi(`${BASE_URL}/groups/move`, {
            method: "POST",
            body: JSON.stringify({ groupId, targetParent }),
        });
        return res.json();
    },
};

// ────────────────────────────────────────────
// 浮动面板工厂
// ────────────────────────────────────────────

function createPanel(id, title) {
    const existing = document.getElementById(id);
    if (existing) { existing.style.display = existing.style.display === "none" ? "flex" : "none"; return existing; }

    const panel = document.createElement("div");
    panel.id = id;
    panel.className = "shiyu-panel";
    panel.style.display = "flex";

    const header = document.createElement("div");
    header.className = "shiyu-panel-header";
    const h3 = document.createElement("h3");
    h3.textContent = title;
    const closeBtn = document.createElement("button");
    closeBtn.className = "shiyu-panel-close";
    closeBtn.innerHTML = "&times;";
    closeBtn.onclick = () => { panel.style.display = "none"; };
    header.appendChild(h3);
    header.appendChild(closeBtn);
    panel.appendChild(header);

    const body = document.createElement("div");
    body.className = "shiyu-panel-body";
    body.id = `${id}-body`;
    panel.appendChild(body);

    // 拖拽
    let drag = false, ox = 0, oy = 0;
    header.onmousedown = (e) => {
        drag = true; ox = e.offsetX; oy = e.offsetY;
        panel.style.cursor = "grabbing";
    };
    document.onmousemove = (e) => {
        if (!drag) return;
        panel.style.left = (e.clientX - ox) + "px";
        panel.style.top = (e.clientY - oy) + "px";
    };
    document.onmouseup = () => {
        if (drag) { drag = false; panel.style.cursor = ""; }
    };

    // 默认位置
    panel.style.left = "60px";
    panel.style.top = "50px";

    document.body.appendChild(panel);
    return panel;
}

// ────────────────────────────────────────────
// 菜单按钮创建
// ────────────────────────────────────────────

function createMenuButton(label, onClick) {
    const btn = document.createElement("button");
    btn.className = "shiyu-menu-btn";
    btn.textContent = label;
    btn.onclick = onClick;
    return btn;
}

function insertMenuButtons() {
    // 找 ComfyUI 的顶部工具栏
    const toolbar = document.querySelector(".comfy-menu") || document.querySelector(".comfyui-menu") || document.querySelector("header") || document.body;
    // 一般在 .comfy-menu 的后面，我们插入一个分隔组
    let container = document.getElementById("shiyu-menu");
    if (!container) {
        container = document.createElement("div");
        container.id = "shiyu-menu";
        container.style.cssText = "display:inline-flex;align-items:center;margin-left:8px;";
        const parent = toolbar.parentNode || document.body;
        // 尝试放到 .comfy-menu 后面
        if (toolbar && toolbar.nextSibling) {
            parent.insertBefore(container, toolbar.nextSibling);
        } else if (toolbar) {
            // 作为兄弟元素
            toolbar.after(container);
        } else {
            parent.appendChild(container);
        }
    }

    const btnPrompt = createMenuButton("📝 Prompts", () => {
        togglePromptPanel();
    });
    const btnGroup = createMenuButton("📂 Groups", () => {
        toggleGroupPanel();
    });
    container.appendChild(btnPrompt);
    container.appendChild(btnGroup);
}

// ────────────────────────────────────────────
// Prompt Manager 面板
// ────────────────────────────────────────────

let _promptPanelActive = false;
let _promptsData = [];
let _selectedPromptId = null;

async function togglePromptPanel() {
    const panel = createPanel("shiyu-panel-prompt", "📝 Prompt Manager");
    const body = document.getElementById("shiyu-panel-prompt-body");
    _promptPanelActive = !_promptPanelActive;
    if (panel.style.display !== "none") renderPromptPanel(body);
}

async function renderPromptPanel(body) {
    body.innerHTML = `<div style="text-align:center;color:#888;padding:30px;">Loading...</div>`;

    // 搜索栏
    const searchBar = document.createElement("div");
    searchBar.className = "shiyu-search-bar";
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "Search prompts...";
    searchInput.oninput = () => renderPromptList();
    searchBar.appendChild(searchInput);

    const btnNew = document.createElement("button");
    btnNew.className = "primary";
    btnNew.textContent = "+ New";
    btnNew.onclick = () => showPromptForm();
    searchBar.appendChild(btnNew);
    body.appendChild(searchBar);

    // 标签过滤
    const tagFilter = document.createElement("div");
    tagFilter.className = "shiyu-tag-filter";
    tagFilter.id = "shiyu-tag-filter";
    body.appendChild(tagFilter);

    // 列表容器
    const list = document.createElement("ul");
    list.className = "shiyu-prompt-list";
    list.id = "shiyu-prompt-list";
    body.appendChild(list);

    // 加载标签
    try {
        const tagRes = await ShiyuAPI.getAllTags();
        if (tagRes.success && tagRes.data.length) {
            tagFilter.innerHTML = tagRes.data.map(t =>
                `<button class="tag-pill" data-tag="${t}" onclick="this.classList.toggle('active');renderPromptList()">${t}</button>`
            ).join("");
        }
    } catch (e) {}

    await renderPromptList();
}

async function renderPromptList() {
    const container = document.getElementById("shiyu-prompt-list");
    if (!container) return;

    const searchInput = container.parentElement?.querySelector(".shiyu-search-bar input");
    const tagFilter = document.getElementById("shiyu-tag-filter");
    const query = searchInput?.value || "";
    const activeTags = tagFilter ? [...tagFilter.querySelectorAll(".tag-pill.active")].map(el => el.dataset.tag) : [];

    try {
        const res = await ShiyuAPI.listPrompts(query, activeTags);
        if (!res.success) { container.innerHTML = `<li class="shiyu-empty">Error loading prompts</li>`; return; }
        _promptsData = res.data || [];

        if (!_promptsData.length) {
            container.innerHTML = `<li class="shiyu-empty">No prompts found<div class="hint">Click "+ New" to create your first prompt</div></li>`;
            return;
        }

        container.innerHTML = _promptsData.map(p => `
            <li class="shiyu-prompt-item" data-id="${p.id}" onclick="ShiyuFrontend.selectPrompt('${p.id}')">
                <button class="fav-btn ${p.metadata?.favorite ? 'active' : ''}" onclick="event.stopPropagation();ShiyuFrontend.toggleFav('${p.id}')">${p.metadata?.favorite ? '★' : '☆'}</button>
                <span class="name">${escapeHtml(p.metadata?.name || "Untitled")}</span>
                <span class="tags">${(p.tags || []).slice(0, 3).map(t => `<span class="tag-badge">${escapeHtml(t)}</span>`).join("")}</span>
                <button class="del-btn" onclick="event.stopPropagation();ShiyuFrontend.deletePrompt('${p.id}')">&times;</button>
            </li>
            ${_selectedPromptId === p.id ? renderPromptDetail(p) : ""}
        `).join("");
    } catch (e) {
        container.innerHTML = `<li class="shiyu-empty">API error: ${e.message}</li>`;
    }
}

function renderPromptDetail(p) {
    return `<li class="shiyu-prompt-detail">
        <h4>${escapeHtml(p.metadata?.name || "Untitled")}</h4>
        <div class="section">
            <div class="section-label">Positive</div>
            <div class="section-content">${escapeHtml(p.positive || "")}</div>
        </div>
        ${p.negative ? `<div class="section">
            <div class="section-label">Negative</div>
            <div class="section-content">${escapeHtml(p.negative)}</div>
        </div>` : ""}
        <div class="section">
            <div class="section-label">Tags: ${(p.tags || []).map(t => escapeHtml(t)).join(", ") || "(none)"}</div>
        </div>
        <div class="shiyu-prompt-detail-actions">
            <button class="primary" onclick="ShiyuFrontend.sendToWorkflow('${p.id}')">Send to Workflow</button>
            <button onclick="ShiyuFrontend.editPrompt('${p.id}')">Edit</button>
            <button onclick="ShiyuFrontend.exportPrompt('${p.id}')">Copy</button>
        </div>
    </li>`;
}

function showPromptForm(existingData = null) {
    const isEdit = existingData !== null;
    const overlay = document.createElement("div");
    overlay.className = "shiyu-form-overlay";
    overlay.id = "shiyu-form-overlay";

    overlay.innerHTML = `
        <div class="shiyu-form-dialog">
            <h3>${isEdit ? "Edit Prompt" : "New Prompt"}</h3>
            <label>Name</label>
            <input id="pf-name" type="text" value="${escapeAttr(existingData?.metadata?.name || "")}" placeholder="Prompt name" />
            <label>Positive Prompt</label>
            <textarea id="pf-positive" placeholder="masterpiece, best quality...">${escapeHtml(existingData?.positive || "")}</textarea>
            <label>Negative Prompt</label>
            <textarea id="pf-negative" placeholder="lowres, bad anatomy...">${escapeHtml(existingData?.negative || "")}</textarea>
            <label>Tags (comma separated)</label>
            <input id="pf-tags" type="text" value="${escapeAttr((existingData?.tags || []).join(", "))}" placeholder="tag1, tag2" />
            <div class="form-actions">
                <button class="btn-cancel" onclick="document.getElementById('shiyu-form-overlay').remove()">Cancel</button>
                <button class="btn-submit" id="pf-submit">${isEdit ? "Update" : "Create"}</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    document.getElementById("pf-submit").onclick = async () => {
        const name = document.getElementById("pf-name").value.trim();
        const positive = document.getElementById("pf-positive").value.trim();
        const negative = document.getElementById("pf-negative").value.trim();
        const tags = document.getElementById("pf-tags").value.split(",").map(t => t.trim()).filter(Boolean);

        if (!name) { toast("Name is required", "warning"); return; }
        if (!positive) { toast("Positive prompt is required", "warning"); return; }

        try {
            const data = { name, positive, negative, tags };
            let res;
            if (isEdit) {
                res = await ShiyuAPI.updatePrompt(existingData.id, data);
            } else {
                res = await ShiyuAPI.createPrompt(data);
            }
            if (res.success) {
                toast(isEdit ? "Prompt updated" : "Prompt created", "success");
                overlay.remove();
                _selectedPromptId = res.data?.id || null;
                renderPromptList();
            } else {
                toast(res.error || "Failed", "error");
            }
        } catch (e) {
            toast("API error: " + e.message, "error");
        }
    };
}

// ────────────────────────────────────────────
// Group Manager 面板
// ────────────────────────────────────────────

async function toggleGroupPanel() {
    const panel = createPanel("shiyu-panel-group", "📂 Group Manager");
    const body = document.getElementById("shiyu-panel-group-body");
    if (panel.style.display !== "none") renderGroupPanel(body);
}

async function renderGroupPanel(body) {
    body.innerHTML = `<div style="text-align:center;color:#888;padding:30px;">Loading...</div>`;

    // 顶部操作栏
    const bar = document.createElement("div");
    bar.className = "shiyu-search-bar";
    const btnNewGroup = document.createElement("button");
    btnNewGroup.className = "primary";
    btnNewGroup.textContent = "+ New Group";
    btnNewGroup.onclick = () => showGroupForm();
    const btnRefresh = document.createElement("button");
    btnRefresh.textContent = "⟳ Refresh";
    btnRefresh.onclick = () => renderGroupPanel(body);
    const btnAddSelected = document.createElement("button");
    btnAddSelected.textContent = "+ Add Selected";
    btnAddSelected.title = "Add selected nodes to a group";
    btnAddSelected.onclick = async () => {
        const selected = app.graph?.selected_nodes || [];
        const selectedIds = Object.keys(selected);
        if (!selectedIds.length) { toast("No nodes selected", "warning"); return; }
        // 显示分组选择器
        showGroupSelector(selectedIds);
    };
    bar.appendChild(btnNewGroup);
    bar.appendChild(btnAddSelected);
    bar.appendChild(btnRefresh);
    body.appendChild(bar);

    // 树
    const tree = document.createElement("div");
    tree.className = "shiyu-group-tree";
    tree.id = "shiyu-group-tree";
    body.appendChild(tree);
    await renderGroupTree();
}

async function renderGroupTree() {
    const container = document.getElementById("shiyu-group-tree");
    if (!container) return;

    try {
        const res = await ShiyuAPI.listGroups();
        if (!res.success) { container.innerHTML = `<div class="shiyu-empty">Error loading groups</div>`; return; }
        const groups = res.data || [];

        if (!groups.length) {
            container.innerHTML = `<div class="shiyu-empty">No groups yet<div class="hint">Click "+ New Group" to create one, or right-click a node → "Add to Group"</div></div>`;
            return;
        }

        // Build tree
        const rootGroups = groups.filter(g => !g.parent);
        container.innerHTML = rootGroups.map(g => renderGroupTreeNode(g, groups)).join("");
    } catch (e) {
        container.innerHTML = `<div class="shiyu-empty">API error: ${e.message}</div>`;
    }
}

function renderGroupTreeNode(g, allGroups) {
    const children = allGroups.filter(c => c.parent === g.id);
    const hasChildren = children.length > 0;
    const isExpanded = !g.collapsed;
    const stats = g.statistics || {};
    const totalNodes = stats.total_node_count || g.nodeIds?.length || 0;

    return `
        <div class="shiyu-group-item" style="border-left:3px solid ${g.color || '#4A90D9'};padding-left:5px;">
            <span class="toggle" onclick="event.stopPropagation();ShiyuFrontend.toggleGroupCollapse('${g.id}', ${!isExpanded})">
                ${hasChildren ? (isExpanded ? "▼" : "▶") : "&nbsp;&nbsp;"}
            </span>
            <span class="color-dot" style="background:${g.color || '#4A90D9'}"></span>
            <span class="gname" onclick="ShiyuFrontend.locateGroup('${g.id}')">${escapeHtml(g.name)}</span>
            <span class="node-count">${totalNodes}</span>
            <span class="g-actions">
                <button title="Add selected nodes" onclick="event.stopPropagation();ShiyuFrontend.addSelectedToGroup('${g.id}')">+</button>
                <button title="Locate" onclick="event.stopPropagation();ShiyuFrontend.locateGroup('${g.id}')">◎</button>
                <button title="${g.locked ? 'Unlock' : 'Lock'}" onclick="event.stopPropagation();ShiyuFrontend.toggleLock('${g.id}')">${g.locked ? '🔒' : '🔓'}</button>
                <button title="Delete" onclick="event.stopPropagation();ShiyuFrontend.deleteGroup('${g.id}')">&times;</button>
            </span>
        </div>
        ${hasChildren && isExpanded ? `<ul>${children.map(c => `<li>${renderGroupTreeNode(c, allGroups)}</li>`).join("")}</ul>` : ""}
    `;
}

function showGroupForm(parentId = null) {
    const overlay = document.createElement("div");
    overlay.className = "shiyu-form-overlay";
    overlay.id = "shiyu-form-overlay";
    overlay.innerHTML = `
        <div class="shiyu-form-dialog">
            <h3>New Group</h3>
            <label>Name</label>
            <input id="gf-name" type="text" placeholder="Group name" />
            <label>Color</label>
            <input id="gf-color" type="color" value="#4A90D9" style="height:36px;padding:2px;" />
            ${parentId ? `<input type="hidden" id="gf-parent" value="${parentId}" />` : ""}
            <div class="form-actions">
                <button class="btn-cancel" onclick="document.getElementById('shiyu-form-overlay').remove()">Cancel</button>
                <button class="btn-submit" id="gf-submit">Create</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    document.getElementById("gf-submit").onclick = async () => {
        const name = document.getElementById("gf-name").value.trim();
        const color = document.getElementById("gf-color").value;
        const parentEl = document.getElementById("gf-parent");
        const parent = parentEl ? parentEl.value : null;

        if (!name) { toast("Name is required", "warning"); return; }

        try {
            const res = await ShiyuAPI.createGroup({ name, color, parent });
            if (res.success) {
                toast("Group created", "success");
                overlay.remove();
                renderGroupTree();
            } else {
                toast(res.error || "Failed", "error");
            }
        } catch (e) {
            toast("API error: " + e.message, "error");
        }
    };
}

function showGroupSelector(nodeIds) {
    ShiyuAPI.listGroups().then(res => {
        if (!res.success || !res.data.length) {
            toast("No groups available. Create one first.", "warning");
            return;
        }
        const overlay = document.createElement("div");
        overlay.className = "shiyu-form-overlay";
        overlay.id = "shiyu-form-overlay";
        overlay.innerHTML = `
            <div class="shiyu-form-dialog" style="min-width:300px;">
                <h3>Add to Group</h3>
                <p style="color:#aaa;margin-bottom:8px;">${nodeIds.length} node(s) selected</p>
                <select id="gs-select" style="width:100%;padding:7px;">
                    ${res.data.map(g => `<option value="${g.id}">${escapeHtml(g.name)}</option>`).join("")}
                </select>
                <div class="form-actions">
                    <button class="btn-cancel" onclick="document.getElementById('shiyu-form-overlay').remove()">Cancel</button>
                    <button class="btn-submit" id="gs-submit">Add</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        document.getElementById("gs-submit").onclick = async () => {
            const gid = document.getElementById("gs-select").value;
            const r = await ShiyuAPI.addNodesToGroup(gid, nodeIds);
            if (r.success) { toast("Nodes added to group", "success"); overlay.remove(); renderGroupTree(); }
            else { toast(r.error || "Failed", "error"); }
        };
    }).catch(e => toast("API error: " + e.message, "error"));
}

// ────────────────────────────────────────────
// 全局 ShiyuFrontend 对象（内联 onclick 用）
// ────────────────────────────────────────────

window.ShiyuFrontend = {
    // Prompt
    selectPrompt(id) {
        _selectedPromptId = _selectedPromptId === id ? null : id;
        renderPromptList();
    },
    async toggleFav(id) {
        const res = await ShiyuAPI.toggleFavorite(id);
        if (res.success) renderPromptList();
    },
    async deletePrompt(id) {
        if (!confirm("Delete this prompt?")) return;
        const res = await ShiyuAPI.deletePrompt(id);
        if (res.success) { toast("Deleted", "success"); _selectedPromptId = null; renderPromptList(); }
    },
    editPrompt(id) {
        const p = _promptsData.find(d => d.id === id);
        if (p) showPromptForm(p);
    },
    async sendToWorkflow(id) {
        const p = _promptsData.find(d => d.id === id);
        if (!p) return;
        // Set the positive/negative on the selected prompt widget if available
        // or copy to clipboard
        try {
            await navigator.clipboard.writeText(p.positive || "");
            toast("Positive prompt copied to clipboard ✓", "success");
        } catch {
            toast("Copy failed. Prompt: " + (p.positive || ""), "info", 5000);
        }
    },
    async exportPrompt(id) {
        const p = _promptsData.find(d => d.id === id);
        if (!p) return;
        try {
            await navigator.clipboard.writeText(JSON.stringify(p, null, 2));
            toast("Prompt data copied to clipboard ✓", "success");
        } catch {
            toast("Copy failed", "error");
        }
    },

    // Group
    async toggleGroupCollapse(id, collapsed) {
        await ShiyuAPI.toggleCollapse(id);
        renderGroupTree();
    },
    async locateGroup(id) {
        const res = await ShiyuAPI.locateGroup(id);
        if (res.success && res.nodeIds?.length) {
            // Clear existing selection and select those nodes
            if (app.graph) {
                app.graph.selected_nodes = {};
                const nodes = app.graph._nodes || [];
                for (const n of nodes) {
                    if (res.nodeIds.includes(n.id + "") || res.nodeIds.includes(n.id)) {
                        n.selected = true;
                        if (app.graph.selected_nodes) {
                            app.graph.selected_nodes[n.id] = n;
                        }
                    }
                }
                if (app.canvas) app.canvas.setDirty(true);
                toast(`Located ${res.nodeIds.length} node(s)`, "success");
            }
        } else {
            toast("No nodes in this group", "info");
        }
    },
    async addSelectedToGroup(groupId) {
        const selected = app.graph?.selected_nodes || {};
        const ids = Object.keys(selected);
        if (!ids.length) { toast("No nodes selected", "warning"); return; }
        const res = await ShiyuAPI.addNodesToGroup(groupId, ids);
        if (res.success) { toast(`Added ${ids.length} node(s)`, "success"); renderGroupTree(); }
    },
    async toggleLock(id) {
        await ShiyuAPI.toggleLock(id);
        renderGroupTree();
    },
    async deleteGroup(id) {
        if (!confirm("Delete this group and its children?")) return;
        const res = await ShiyuAPI.deleteGroup(id);
        if (res.success) { toast("Group deleted", "success"); renderGroupTree(); }
    },
};

// ────────────────────────────────────────────
// 工具函数
// ────────────────────────────────────────────

function escapeHtml(s) {
    if (!s) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function escapeAttr(s) {
    if (!s) return "";
    return String(s).replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ────────────────────────────────────────────
// ComfyUI Extension 注册
// ────────────────────────────────────────────

app.registerExtension({
    name: EXT_NAME,

    async setup() {
        // 注入 CSS
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "/extensions/css/shiyu-tools.css";
        document.head.appendChild(link);

        // Insert menu buttons after a short delay to let ComfyUI render
        setTimeout(insertMenuButtons, 500);
    },

    /**
     * 右键菜单扩展：Add to Group / Create Group from Selection
     */
    getCustomContextMenuOptions(nodeType, nodeData) {
        if (!nodeData) return null;

        const options = [];

        // ── "Add to Group" 子菜单 ──
        const addToGroupOption = {
            content: "📂 Add to Group",
            has_submenu: true,
            submenu: {
                options: [],
                async open() {
                    try {
                        const res = await ShiyuAPI.listGroups();
                        const groups = res.success ? (res.data || []) : [];
                        if (!groups.length) {
                            this.options = [{
                                content: "(no groups — create one first)",
                                disabled: true,
                            }];
                        } else {
                            this.options = groups.map(g => ({
                                content: `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${g.color};margin-right:6px;"></span>${g.name}`,
                                callback: async () => {
                                    const node = app.graph?._nodes?.find(n => n.type === nodeData?.name);
                                    if (node) {
                                        const nid = String(node.id);
                                        await ShiyuAPI.addNodesToGroup(g.id, [nid]);
                                        toast(`Added to "${g.name}"`, "success");
                                    }
                                },
                            }));
                            this.options.push(null);
                            this.options.push({
                                content: "+ New Group...",
                                callback: () => showGroupForm(),
                            });
                        }
                    } catch (e) {
                        this.options = [{ content: "Error loading groups", disabled: true }];
                    }
                },
            },
        };

        // ── "Create Group from Selection" ──
        const createGroupOption = {
            content: "📁 Create Group from Selection",
            callback: () => {
                const selected = app.graph?.selected_nodes || {};
                const nodeIds = Object.keys(selected);
                if (!nodeIds.length) { toast("Select at least one node first", "warning"); return; }
                showGroupForm(null);
                // 创建后加到 group form 的 submit 逻辑已经可以处理
                // 但我们需要额外加节点。改用覆盖方式：
                const origSubmit = document.getElementById("gf-submit")?.onclick;
                if (origSubmit) {
                    document.getElementById("gf-submit").onclick = async () => {
                        const name = document.getElementById("gf-name").value.trim();
                        const color = document.getElementById("gf-color").value;
                        if (!name) { toast("Name is required", "warning"); return; }
                        try {
                            const res = await ShiyuAPI.createGroup({ name, color });
                            if (res.success) {
                                await ShiyuAPI.addNodesToGroup(res.data.id, nodeIds);
                                toast(`Group "${name}" created with ${nodeIds.length} node(s)`, "success");
                                document.getElementById("shiyu-form-overlay")?.remove();
                                renderGroupTree();
                            }
                        } catch (e) {
                            toast("Error: " + e.message, "error");
                        }
                    };
                }
            },
        };

        options.push(addToGroupOption);
        options.push(createGroupOption);

        return options;
    },
});
