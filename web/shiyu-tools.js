/**
 * Shiyu Tools — ComfyUI Enterprise Plugin Framework
 *
 * Frontend extension that adds:
 * - Floating Prompt Manager panel
 * - Floating Group Manager panel
 * - Node context menu integration
 * - Communication with Python API backend
 */

import { app } from "../scripts/app.js";
import { api } from "../scripts/api.js";

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
    if (existing) {
        existing.style.display = existing.style.display === "none" ? "flex" : "none";
        return existing;
    }

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

    // 默认位置 — 左上角，避开 ComfyUI 侧边栏
    panel.style.right = "20px";
    panel.style.top = "60px";
    panel.style.left = "auto";

    document.body.appendChild(panel);
    return panel;
}

// ────────────────────────────────────────────
// 注入菜单按钮到 ComfyUI 工具栏
// ────────────────────────────────────────────

let _menuInjected = false;

function injectMenuButtons() {
    if (_menuInjected) return;

    // 策略 1: 找到 Queue Prompt 按钮的位置，在其旁边插入
    const queueBtn = _findQueueButton();
    if (queueBtn && queueBtn.parentNode) {
        _createButtonsInContainer(queueBtn.parentNode, false);
        _menuInjected = true;
        return;
    }

    // 策略 2: 查找 ComfyUI 工具栏
    const toolbar = document.querySelector(".comfyui-toolbar, .comfy-toolbar, #comfyui-toolbar, [class*='toolbar']");
    if (toolbar) {
        _createButtonsInContainer(toolbar, true);
        _menuInjected = true;
        return;
    }

    // 策略 3: 查找侧边菜单的按钮区域
    const menuBtns = document.querySelector(".comfy-menu-btns, .comfy-menu .comfy-btn, .comfy-menu > button");
    if (menuBtns && menuBtns.parentNode) {
        _createButtonsInContainer(menuBtns.parentNode, false);
        _menuInjected = true;
        return;
    }

    // 策略 4: 在侧边栏 .comfy-menu 底部添加一个分隔栏
    const comfyMenu = document.querySelector(".comfy-menu");
    if (comfyMenu) {
        const sep = document.createElement("div");
        sep.style.cssText = "border-top:1px solid #444;margin:8px 10px;padding-top:8px;";
        _createButtonsInContainer(sep, false);
        comfyMenu.appendChild(sep);
        _menuInjected = true;
        return;
    }

    // 策略 5: 最后回退 — 在页面左上角创建独立工具栏
    const floatingBar = document.createElement("div");
    floatingBar.id = "shiyu-float-bar";
    floatingBar.style.cssText = "position:fixed;top:8px;left:60px;z-index:9999;display:flex;gap:6px;";
    _createButtonsInContainer(floatingBar, true);
    document.body.appendChild(floatingBar);
    _menuInjected = true;
}

function _findQueueButton() {
    // 尝试多种选择器找到 Queue 按钮
    const selectors = [
        'button[aria-label*="Queue"]',
        'button[aria-label*="queue"]',
        'button:has(svg)',
        'button',
    ];
    for (const sel of selectors) {
        try {
            const btns = document.querySelectorAll(sel);
            for (const btn of btns) {
                const text = btn.textContent.toLowerCase();
                if (text.includes("queue") || text.includes("生成") || text.includes("执行")) {
                    return btn;
                }
            }
        } catch (e) {}
    }
    // Last resort: search all buttons
    try {
        const allBtns = document.querySelectorAll('button');
        for (const btn of allBtns) {
            const text = btn.textContent.toLowerCase();
            if (text.includes("queue") || text.includes("生成") || text.includes("执行")) {
                return btn;
            }
        }
    } catch (e) {}
    return null;
}

function _createButtonsInContainer(container, asFirstChild) {
    const wrapper = document.createElement("span");
    wrapper.id = "shiyu-menu";
    wrapper.style.cssText = "display:inline-flex;align-items:center;gap:4px;margin:0 4px;";

    const btnPrompt = document.createElement("button");
    btnPrompt.className = "shiyu-menu-btn";
    btnPrompt.textContent = "📝 Prompts";
    btnPrompt.title = "Open Prompt Manager";
    btnPrompt.onclick = (e) => { e.stopPropagation(); togglePromptPanel(); };

    const btnGroup = document.createElement("button");
    btnGroup.className = "shiyu-menu-btn";
    btnGroup.textContent = "📂 Groups";
    btnGroup.title = "Open Group Manager";
    btnGroup.onclick = (e) => { e.stopPropagation(); toggleGroupPanel(); };

    wrapper.appendChild(btnPrompt);
    wrapper.appendChild(btnGroup);

    if (asFirstChild && container.firstChild) {
        container.insertBefore(wrapper, container.firstChild);
    } else {
        container.appendChild(wrapper);
    }
}

// ────────────────────────────────────────────
// Prompt Manager 面板
// ────────────────────────────────────────────

let _promptsData = [];
let _selectedPromptId = null;

async function togglePromptPanel() {
    const panel = createPanel("shiyu-panel-prompt", "📝 Prompt Manager");
    const body = document.getElementById("shiyu-panel-prompt-body");
    if (panel.style.display !== "none") {
        await renderPromptPanel(body);
    }
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
        if (tagRes.success && tagRes.data && tagRes.data.length) {
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

    const nameVal = escapeAttr(existingData?.metadata?.name || "");
    const posVal = escapeHtml(existingData?.positive || "");
    const negVal = escapeHtml(existingData?.negative || "");
    const tagsVal = escapeAttr((existingData?.tags || []).join(", "));

    overlay.innerHTML = `
        <div class="shiyu-form-dialog">
            <h3>${isEdit ? "Edit Prompt" : "New Prompt"}</h3>
            <label>Name</label>
            <input id="pf-name" type="text" value="${nameVal}" placeholder="Prompt name" />
            <label>Positive Prompt</label>
            <textarea id="pf-positive" placeholder="masterpiece, best quality...">${posVal}</textarea>
            <label>Negative Prompt</label>
            <textarea id="pf-negative" placeholder="lowres, bad anatomy...">${negVal}</textarea>
            <label>Tags (comma separated)</label>
            <input id="pf-tags" type="text" value="${tagsVal}" placeholder="tag1, tag2" />
            <div class="form-actions">
                <button class="btn-cancel" onclick="this.closest('.shiyu-form-overlay').remove()">Cancel</button>
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
            let res;
            if (isEdit) {
                res = await ShiyuAPI.updatePrompt(existingData.id, { name, positive, negative, tags });
            } else {
                res = await ShiyuAPI.createPrompt({ name, positive, negative, tags });
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
    if (panel.style.display !== "none") {
        await renderGroupPanel(body);
    }
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
        const selectedIds = _getSelectedNodeIds();
        if (!selectedIds.length) { toast("No nodes selected", "warning"); return; }
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

function _getSelectedNodeIds() {
    try {
        // ComfyUI stores selected nodes in canvas
        if (app.canvas?.selected_nodes) {
            const sel = app.canvas.selected_nodes;
            if (sel instanceof Set) {
                return [...sel].map(n => String(n.id));
            }
            if (typeof sel === 'object') {
                return Object.keys(sel);
            }
        }
        // Fallback: scan graph nodes
        if (app.graph?._nodes) {
            return app.graph._nodes.filter(n => n.selected).map(n => String(n.id));
        }
    } catch (e) {}
    return [];
}

async function renderGroupTree() {
    const container = document.getElementById("shiyu-group-tree");
    if (!container) return;

    try {
        const res = await ShiyuAPI.listGroups();
        if (!res.success) { container.innerHTML = `<div class="shiyu-empty">Error loading groups</div>`; return; }
        const groups = res.data || [];

        if (!groups.length) {
            container.innerHTML = `<div class="shiyu-empty">No groups yet<div class="hint">Click "+ New Group" to create one</div></div>`;
            return;
        }

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
    const totalNodes = stats.total_node_count || (g.nodeIds ? g.nodeIds.length : 0);

    return `
        <div class="shiyu-group-item" style="border-left:3px solid ${g.color || '#4A90D9'};padding-left:5px;">
            <span class="toggle" onclick="event.stopPropagation();ShiyuFrontend.toggleGroupCollapse('${g.id}')">
                ${hasChildren ? (isExpanded ? "▼" : "▶") : "&nbsp;&nbsp;"}
            </span>
            <span class="color-dot" style="background:${g.color || '#4A90D9'}"></span>
            <span class="gname" onclick="ShiyuFrontend.locateGroup('${g.id}')" title="Locate nodes">${escapeHtml(g.name)}</span>
            <span class="node-count">${totalNodes}</span>
            <span class="g-actions">
                <button title="Add selected nodes" onclick="event.stopPropagation();ShiyuFrontend.addSelectedToGroup('${g.id}')">+</button>
                <button title="Locate on canvas" onclick="event.stopPropagation();ShiyuFrontend.locateGroup('${g.id}')">◎</button>
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
    const parentInput = parentId ? `<input type="hidden" id="gf-parent" value="${parentId}" />` : "";
    overlay.innerHTML = `
        <div class="shiyu-form-dialog">
            <h3>New Group</h3>
            <label>Name</label>
            <input id="gf-name" type="text" placeholder="Group name" />
            <label>Color</label>
            <input id="gf-color" type="color" value="#4A90D9" style="height:36px;padding:2px;" />
            ${parentInput}
            <div class="form-actions">
                <button class="btn-cancel" onclick="this.closest('.shiyu-form-overlay').remove()">Cancel</button>
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
        if (!res.success || !res.data || !res.data.length) {
            toast("No groups available. Create one first.", "warning");
            return;
        }
        const overlay = document.createElement("div");
        overlay.className = "shiyu-form-overlay";
        overlay.innerHTML = `
            <div class="shiyu-form-dialog" style="min-width:300px;">
                <h3>Add to Group</h3>
                <p style="color:#aaa;margin-bottom:8px;">${nodeIds.length} node(s) selected</p>
                <select id="gs-select" style="width:100%;padding:7px;">
                    ${res.data.map(g => `<option value="${g.id}">${escapeHtml(g.name)}</option>`).join("")}
                </select>
                <div class="form-actions">
                    <button class="btn-cancel" onclick="this.closest('.shiyu-form-overlay').remove()">Cancel</button>
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
// 全局 ShiyuFrontend 对象
// ────────────────────────────────────────────

window.ShiyuFrontend = {
    // ── Prompt ──
    selectPrompt(id) {
        _selectedPromptId = _selectedPromptId === id ? null : id;
        renderPromptList();
    },
    async toggleFav(id) {
        await ShiyuAPI.toggleFavorite(id);
        renderPromptList();
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
        try {
            await navigator.clipboard.writeText(p.positive || "");
            toast("Positive prompt copied ✓", "success");
        } catch {
            toast("Copy failed. Prompt: " + (p.positive || ""), "info", 5000);
        }
    },
    async exportPrompt(id) {
        const p = _promptsData.find(d => d.id === id);
        if (!p) return;
        try {
            await navigator.clipboard.writeText(JSON.stringify(p, null, 2));
            toast("Prompt data copied ✓", "success");
        } catch {
            toast("Copy failed", "error");
        }
    },

    // ── Group ──
    async toggleGroupCollapse(id) {
        await ShiyuAPI.toggleCollapse(id);
        renderGroupTree();
    },
    async locateGroup(id) {
        const res = await ShiyuAPI.locateGroup(id);
        if (res.success && res.nodeIds && res.nodeIds.length) {
            // 取消之前的选择
            _deselectAllNodes();
            // 选中返回的节点
            const idSet = new Set(res.nodeIds.map(n => String(n)));
            if (app.graph && app.graph._nodes) {
                for (const n of app.graph._nodes) {
                    if (idSet.has(String(n.id))) {
                        n.selected = true;
                        if (app.canvas && app.canvas.selected_nodes) {
                            if (app.canvas.selected_nodes instanceof Set) {
                                app.canvas.selected_nodes.add(n);
                            } else {
                                app.canvas.selected_nodes[n.id] = n;
                            }
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
        const ids = _getSelectedNodeIds();
        if (!ids.length) { toast("No nodes selected on canvas", "warning"); return; }
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

function _deselectAllNodes() {
    if (app.canvas && app.canvas.selected_nodes) {
        if (app.canvas.selected_nodes instanceof Set) {
            app.canvas.selected_nodes.clear();
        } else {
            app.canvas.selected_nodes = {};
        }
    }
    if (app.graph && app.graph._nodes) {
        for (const n of app.graph._nodes) {
            n.selected = false;
        }
    }
    if (app.canvas) app.canvas.setDirty(true);
}

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
// CSS 注入
// ────────────────────────────────────────────

function injectCSS() {
    if (document.getElementById("shiyu-css")) return;
    const link = document.createElement("link");
    link.id = "shiyu-css";
    link.rel = "stylesheet";
    link.href = `/extensions/shiyu-tools.css`; // ComfyUI serves web/ at /extensions/
    document.head.appendChild(link);
}

// ────────────────────────────────────────────
// ComfyUI Extension 注册
// ────────────────────────────────────────────

app.registerExtension({
    name: EXT_NAME,

    async setup() {
        // 注入 CSS
        injectCSS();

        // 尝试注入菜单按钮
        // setup 时 DOM 可能还没渲染完，重试几次
        const tryInject = (attempt = 0) => {
            if (_menuInjected) return;
            injectMenuButtons();
            if (!_menuInjected && attempt < 10) {
                setTimeout(() => tryInject(attempt + 1), 1000);
            }
        };
        setTimeout(() => tryInject(0), 1000);
    },

    /**
     * Context menu: Add to Group / Create Group from Selection
     */
    getCustomContextMenuOptions(nodeType, nodeData) {
        if (!nodeData) return null;

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
                            this.options = [{ content: "(no groups — create one first)", disabled: true }];
                        } else {
                            this.options = groups.map(g => ({
                                content: `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${g.color};margin-right:6px;"></span>${g.name}`,
                                callback: async () => {
                                    const nodeIds = _getSelectedNodeIds();
                                    if (nodeIds.length) {
                                        await ShiyuAPI.addNodesToGroup(g.id, nodeIds);
                                    } else if (nodeData && nodeData.id !== undefined) {
                                        await ShiyuAPI.addNodesToGroup(g.id, [String(nodeData.id)]);
                                    }
                                    toast(`Added to "${g.name}"`, "success");
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

        const createGroupOption = {
            content: "📁 Create Group from Selection",
            callback: () => {
                const nodeIds = _getSelectedNodeIds();
                showGroupForm(null);
                // 覆盖 submit 逻辑加入节点
                const origSubmit = document.getElementById("gf-submit");
                if (origSubmit) {
                    const origHandler = origSubmit.onclick;
                    origSubmit.onclick = async () => {
                        const name = document.getElementById("gf-name").value.trim();
                        const color = document.getElementById("gf-color").value;
                        if (!name) { toast("Name is required", "warning"); return; }
                        try {
                            const res = await ShiyuAPI.createGroup({ name, color });
                            if (res.success) {
                                await ShiyuAPI.addNodesToGroup(res.data.id, nodeIds);
                                toast(`Group "${name}" created with ${nodeIds.length} node(s)`, "success");
                                document.querySelector(".shiyu-form-overlay")?.remove();
                                renderGroupTree();
                            }
                        } catch (e) {
                            toast("Error: " + e.message, "error");
                        }
                    };
                }
            },
        };

        return [addToGroupOption, createGroupOption];
    },
});
