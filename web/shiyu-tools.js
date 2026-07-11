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
    const style = document.createElement("style");
    style.id = "shiyu-css";
    style.textContent = `/* ═══════════════════════════════════════════
   Shiyu Tools — UI Styles
   ═══════════════════════════════════════════ */

/* ── 浮动面板 ── */

.shiyu-panel {
    position: fixed;
    z-index: 9999;
    background: #2a2a2e;
    border: 1px solid #555;
    border-radius: 8px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    display: flex;
    flex-direction: column;
    color: #ddd;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
    min-width: 380px;
    min-height: 300px;
    max-height: 80vh;
}

.shiyu-panel-header {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    background: #333;
    border-radius: 8px 8px 0 0;
    cursor: grab;
    user-select: none;
    flex-shrink: 0;
}

.shiyu-panel-header:active { cursor: grabbing; }

.shiyu-panel-header h3 {
    margin: 0;
    flex: 1;
    font-size: 14px;
    font-weight: 600;
    color: #fff;
}

.shiyu-panel-close {
    background: none;
    border: none;
    color: #999;
    cursor: pointer;
    font-size: 18px;
    padding: 0 4px;
    line-height: 1;
}

.shiyu-panel-close:hover { color: #ff6b6b; }

.shiyu-panel-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
}

/* ── 菜单按钮 ── */

.shiyu-menu-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    margin: 0 2px;
    background: #3a3a3e;
    border: 1px solid #555;
    border-radius: 4px;
    color: #ccc;
    cursor: pointer;
    font-size: 12px;
    transition: background 0.15s;
}

.shiyu-menu-btn:hover {
    background: #4a4a4e;
    color: #fff;
}

.shiyu-menu-btn.active {
    background: #4a90d9;
    border-color: #5a9ff0;
    color: #fff;
}

/* ── Prompt 列表 ── */

.shiyu-prompt-list { list-style: none; margin: 0; padding: 0; }

.shiyu-prompt-item {
    display: flex;
    align-items: center;
    padding: 8px 10px;
    margin: 2px 0;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.1s;
    gap: 8px;
}

.shiyu-prompt-item:hover { background: #3a3a3e; }

.shiyu-prompt-item .name {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.shiyu-prompt-item .tags {
    display: flex;
    gap: 3px;
    flex-wrap: wrap;
}

.shiyu-prompt-item .tag-badge {
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 3px;
    background: #4a4a5e;
    color: #aaa;
}

.shiyu-prompt-item .fav-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: #666;
    font-size: 14px;
    padding: 0 4px;
}

.shiyu-prompt-item .fav-btn.active { color: #f1c40f; }

.shiyu-prompt-item .del-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: #666;
    font-size: 14px;
    padding: 0 4px;
    visibility: hidden;
}

.shiyu-prompt-item:hover .del-btn { visibility: visible; }
.shiyu-prompt-item .del-btn:hover { color: #ff6b6b; }

/* ── 搜索栏 ── */

.shiyu-search-bar {
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
}

.shiyu-search-bar input {
    flex: 1;
    padding: 6px 10px;
    border: 1px solid #555;
    border-radius: 4px;
    background: #1a1a1e;
    color: #ddd;
    font-size: 13px;
    outline: none;
}

.shiyu-search-bar input:focus { border-color: #4a90d9; }

.shiyu-search-bar button {
    padding: 6px 12px;
    border: 1px solid #555;
    border-radius: 4px;
    background: #3a3a3e;
    color: #ccc;
    cursor: pointer;
    font-size: 12px;
}

.shiyu-search-bar button:hover { background: #4a4a4e; color: #fff; }
.shiyu-search-bar button.primary { background: #4a90d9; border-color: #5a9ff0; color: #fff; }
.shiyu-search-bar button.primary:hover { background: #5a9ff0; }

/* ── 标签过滤 ── */

.shiyu-tag-filter {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 10px;
}

.shiyu-tag-filter .tag-pill {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    border: 1px solid #555;
    background: transparent;
    color: #aaa;
    cursor: pointer;
    transition: all 0.1s;
}

.shiyu-tag-filter .tag-pill:hover { border-color: #4a90d9; color: #4a90d9; }
.shiyu-tag-filter .tag-pill.active { background: #4a90d9; border-color: #4a90d9; color: #fff; }

/* ── Group 树 ── */

.shiyu-group-tree { list-style: none; margin: 0; padding: 0; }

.shiyu-group-tree ul {
    list-style: none;
    margin: 0;
    padding-left: 20px;
}

.shiyu-group-item {
    display: flex;
    align-items: center;
    padding: 5px 8px;
    margin: 1px 0;
    border-radius: 4px;
    cursor: pointer;
    gap: 6px;
    transition: background 0.1s;
}

.shiyu-group-item:hover { background: #3a3a3e; }

.shiyu-group-item .toggle {
    width: 16px;
    text-align: center;
    color: #888;
    font-size: 10px;
    flex-shrink: 0;
}

.shiyu-group-item .color-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}

.shiyu-group-item .gname {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.shiyu-group-item .node-count {
    font-size: 10px;
    color: #888;
    margin-left: auto;
}

.shiyu-group-item .g-actions {
    display: flex;
    gap: 2px;
    visibility: hidden;
}

.shiyu-group-item:hover .g-actions { visibility: visible; }

.shiyu-group-item .g-actions button {
    background: none;
    border: none;
    color: #888;
    cursor: pointer;
    font-size: 11px;
    padding: 1px 4px;
}

.shiyu-group-item .g-actions button:hover { color: #4a90d9; }

/* ── 空状态 ── */

.shiyu-empty {
    text-align: center;
    color: #666;
    padding: 30px 10px;
    font-size: 13px;
}

.shiyu-empty .hint {
    font-size: 11px;
    color: #555;
    margin-top: 6px;
}

/* ── 表单对话框 ── */

.shiyu-form-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 10001;
    display: flex;
    align-items: center;
    justify-content: center;
}

.shiyu-form-dialog {
    background: #2a2a2e;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 20px;
    min-width: 400px;
    max-width: 600px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}

.shiyu-form-dialog h3 { margin: 0 0 16px; color: #fff; }

.shiyu-form-dialog label {
    display: block;
    margin-bottom: 4px;
    color: #aaa;
    font-size: 12px;
}

.shiyu-form-dialog input,
.shiyu-form-dialog textarea,
.shiyu-form-dialog select {
    width: 100%;
    padding: 7px 10px;
    margin-bottom: 12px;
    border: 1px solid #555;
    border-radius: 4px;
    background: #1a1a1e;
    color: #ddd;
    font-size: 13px;
    outline: none;
    box-sizing: border-box;
}

.shiyu-form-dialog input:focus,
.shiyu-form-dialog textarea:focus { border-color: #4a90d9; }

.shiyu-form-dialog textarea {
    min-height: 80px;
    resize: vertical;
    font-family: inherit;
}

.shiyu-form-dialog .form-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    margin-top: 8px;
}

.shiyu-form-dialog .form-actions button {
    padding: 7px 16px;
    border: 1px solid #555;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
}

.shiyu-form-dialog .form-actions .btn-cancel {
    background: #3a3a3e;
    color: #ccc;
}

.shiyu-form-dialog .form-actions .btn-submit {
    background: #4a90d9;
    border-color: #5a9ff0;
    color: #fff;
}

.shiyu-form-dialog .form-actions .btn-submit:hover { background: #5a9ff0; }

/* ── 通知 Toast ── */

.shiyu-toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 99999;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.shiyu-toast-msg {
    padding: 10px 16px;
    border-radius: 6px;
    color: #fff;
    font-size: 13px;
    animation: shiyu-fadein 0.2s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.shiyu-toast-msg.info { background: #4a90d9; }
.shiyu-toast-msg.success { background: #27ae60; }
.shiyu-toast-msg.warning { background: #f39c12; }
.shiyu-toast-msg.error { background: #e74c3c; }

@keyframes shiyu-fadein {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ── 详情面板 ├── 在 prompt 列表点击后展开 ── */

.shiyu-prompt-detail {
    background: #222;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 12px;
    margin-top: 8px;
}

.shiyu-prompt-detail h4 { margin: 0 0 8px; color: #fff; font-size: 14px; }

.shiyu-prompt-detail .section {
    margin-bottom: 8px;
}

.shiyu-prompt-detail .section-label {
    font-size: 11px;
    color: #888;
    margin-bottom: 2px;
}

.shiyu-prompt-detail .section-content {
    background: #1a1a1e;
    border-radius: 4px;
    padding: 6px 8px;
    font-family: monospace;
    font-size: 12px;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 120px;
    overflow-y: auto;
}

.shiyu-prompt-detail-actions {
    display: flex;
    gap: 6px;
    margin-top: 10px;
}

.shiyu-prompt-detail-actions button {
    padding: 4px 10px;
    border: 1px solid #555;
    border-radius: 4px;
    background: #3a3a3e;
    color: #ccc;
    cursor: pointer;
    font-size: 11px;
}

.shiyu-prompt-detail-actions button:hover { background: #4a4a4e; color: #fff; }
.shiyu-prompt-detail-actions button.primary { background: #4a90d9; border-color: #5a9ff0; color: #fff; }
`;
    document.head.appendChild(style);
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
