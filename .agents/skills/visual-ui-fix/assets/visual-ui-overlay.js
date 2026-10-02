(() => {
  if (window.__visualUiFix?.host?.isConnected) return;

  const state = {
    selecting: false,
    selected: null,
    selectedOriginal: null,
    changes: [],
    applied: [],
    touched: new Set(),
  };

  const host = document.createElement("div");
  host.id = "visual-ui-fix-overlay";
  host.style.cssText = "all:initial;position:fixed;inset:0;z-index:2147483647;pointer-events:none";
  const shadow = host.attachShadow({ mode: "open" });
  shadow.innerHTML = `
    <style>
      *{box-sizing:border-box}button,input,textarea{font:inherit}
      .toolbar,.editor{font-family:ui-sans-serif,system-ui,sans-serif;color:#18181b;background:#fff;border:1px solid #d4d4d8;box-shadow:0 12px 32px rgba(0,0,0,.2);pointer-events:auto}
      .toolbar{position:fixed;top:16px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:12px}
      .brand{font-weight:700;margin-right:4px;cursor:grab;user-select:none;touch-action:none}.brand.dragging{cursor:grabbing}.count{font-size:12px;color:#52525b;min-width:70px}
      button{border:0;border-radius:8px;padding:7px 10px;background:#e4e4e7;color:#18181b;cursor:pointer}button.primary{background:#4f46e5;color:#fff}button.danger{background:#fee2e2;color:#991b1b}
      .editor{position:fixed;top:72px;right:16px;width:min(360px,calc(100vw - 32px));max-height:calc(100vh - 88px);overflow:auto;padding:14px;border-radius:12px;display:none}.editor.open{display:block}
      .title{font-weight:700;margin-bottom:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      label{display:block;font-size:12px;font-weight:600;margin:9px 0 4px}.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}
      input[type=text],textarea{width:100%;border:1px solid #d4d4d8;border-radius:7px;padding:7px;background:#fff;color:#18181b}
      input[type=color]{width:100%;height:34px;border:1px solid #d4d4d8;border-radius:7px;background:#fff}textarea{min-height:68px;resize:vertical}
      .actions{display:flex;justify-content:flex-end;gap:7px;margin-top:12px}.hint{font-size:11px;color:#71717a;margin-top:5px}.validation{min-height:16px;font-size:11px;color:#b91c1c;margin-top:6px}
      .highlight{position:fixed;border:2px solid #4f46e5;background:rgba(79,70,229,.08);pointer-events:none;display:none}
    </style>
    <div class="highlight"></div>
    <div class="toolbar">
      <span class="brand" role="button" aria-label="Drag toolbar" title="Drag to move">Visual UI Fix</span>
      <button class="select primary">Select element</button>
      <span class="count">0 changes</span>
      <button class="finish">Finish</button>
      <button class="discard danger">Discard</button>
    </div>
    <section class="editor">
      <div class="title">Selected element</div>
      <label>Text</label><input class="text" data-field="text" type="text">
      <div class="row">
        <div><label>Text color</label><input class="color" data-field="color" type="color"></div>
        <div><label>Background</label><input class="background" data-field="backgroundColor" type="color"></div>
      </div>
      <label>Padding</label><input class="padding" data-field="padding" type="text" placeholder="e.g. 12px 16px">
      <div class="row">
        <div><label>Width</label><input class="width" data-field="width" type="text" placeholder="e.g. 320px or 100%"></div>
        <div><label>Height</label><input class="height" data-field="height" type="text" placeholder="e.g. 48px or auto"></div>
      </div>
      <div class="row">
        <div><label>Move X</label><input class="move-x" data-field="moveX" type="text" value="0px"></div>
        <div><label>Move Y</label><input class="move-y" data-field="moveY" type="text" value="0px"></div>
      </div>
      <label>Comment</label><textarea class="note" placeholder="Describe the intended result"></textarea>
      <div class="hint">Preview changes only this browser tab. Source files are untouched.</div>
      <div class="validation" role="status"></div>
      <div class="actions"><button class="cancel">Cancel</button><button class="preview">Preview</button><button class="save primary">Save</button></div>
    </section>`;
  document.documentElement.appendChild(host);

  const $ = (selector) => shadow.querySelector(selector);
  const highlight = $(".highlight");
  const toolbar = $(".toolbar");
  const dragHandle = $(".brand");
  const editor = $(".editor");
  const selectButton = $(".select");
  const validation = $(".validation");
  const toolbarDrag = { pointerId: null, offsetX: 0, offsetY: 0 };

  function moveToolbar(clientX, clientY) {
    const rect = toolbar.getBoundingClientRect();
    const margin = 8;
    const maxLeft = Math.max(margin, innerWidth - rect.width - margin);
    const maxTop = Math.max(margin, innerHeight - rect.height - margin);
    const left = Math.min(Math.max(margin, clientX - toolbarDrag.offsetX), maxLeft);
    const top = Math.min(Math.max(margin, clientY - toolbarDrag.offsetY), maxTop);
    Object.assign(toolbar.style, { left: `${left}px`, top: `${top}px`, transform: "none" });
  }

  dragHandle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    const rect = toolbar.getBoundingClientRect();
    toolbarDrag.pointerId = event.pointerId;
    toolbarDrag.offsetX = event.clientX - rect.left;
    toolbarDrag.offsetY = event.clientY - rect.top;
    dragHandle.classList.add("dragging");
    dragHandle.setPointerCapture(event.pointerId);
    event.preventDefault();
  });

  dragHandle.addEventListener("pointermove", (event) => {
    if (toolbarDrag.pointerId !== event.pointerId) return;
    moveToolbar(event.clientX, event.clientY);
  });

  function stopToolbarDrag(event) {
    if (toolbarDrag.pointerId !== event.pointerId) return;
    toolbarDrag.pointerId = null;
    dragHandle.classList.remove("dragging");
    if (dragHandle.hasPointerCapture(event.pointerId)) dragHandle.releasePointerCapture(event.pointerId);
  }

  dragHandle.addEventListener("pointerup", stopToolbarDrag);
  dragHandle.addEventListener("pointercancel", stopToolbarDrag);

  function rectData(rect) {
    return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
  }

  function rgbToHex(value, fallback) {
    const parts = String(value).match(/[\d.]+/g);
    if (!parts || parts.length < 3) return fallback;
    return `#${parts.slice(0, 3).map((v) => Math.max(0, Math.min(255, Math.round(Number(v)))).toString(16).padStart(2, "0")).join("")}`;
  }

  function stableSelector(element) {
    if (element.id && !/\d{4,}/.test(element.id)) return `#${CSS.escape(element.id)}`;
    for (const name of ["data-testid", "data-test", "aria-label"]) {
      const value = element.getAttribute(name);
      if (value) return `${element.tagName.toLowerCase()}[${name}="${CSS.escape(value)}"]`;
    }
    const parts = [];
    let node = element;
    while (node && node !== document.body && parts.length < 5) {
      let part = node.tagName.toLowerCase();
      const classes = [...node.classList].filter((name) => !/^(active|selected|hover|focus)$/.test(name)).slice(0, 2);
      if (classes.length) part += classes.map((name) => `.${CSS.escape(name)}`).join("");
      const siblings = node.parentElement ? [...node.parentElement.children].filter((item) => item.tagName === node.tagName) : [];
      if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(node) + 1})`;
      parts.unshift(part);
      node = node.parentElement;
    }
    return parts.join(" > ");
  }

  function outline(element) {
    if (!element || element === host || host.contains(element)) {
      highlight.style.display = "none";
      return;
    }
    const rect = element.getBoundingClientRect();
    Object.assign(highlight.style, {
      display: "block",
      left: `${rect.left}px`,
      top: `${rect.top}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
    });
  }

  function restore(item) {
    if (!item) return;
    item.element.style.color = item.inline.color;
    item.element.style.backgroundColor = item.inline.backgroundColor;
    item.element.style.padding = item.inline.padding;
    item.element.style.width = item.inline.width;
    item.element.style.height = item.inline.height;
    item.element.style.translate = item.inline.translate;
    if (item.canEditText) item.element.textContent = item.text;
  }

  function restoreSelectedPreview() {
    restore(state.selectedOriginal);
    state.selectedOriginal = null;
  }

  function selectElement(element) {
    restoreSelectedPreview();
    state.selected = element;
    const style = getComputedStyle(element);
    state.selectedOriginal = {
      element,
      text: element.textContent ?? "",
      canEditText: element.childElementCount === 0,
      inline: {
        color: element.style.color,
        backgroundColor: element.style.backgroundColor,
        padding: element.style.padding,
        width: element.style.width,
        height: element.style.height,
        translate: element.style.translate,
      },
      computed: {
        color: style.color,
        backgroundColor: style.backgroundColor,
        padding: style.padding,
        width: style.width,
        height: style.height,
        translate: style.translate,
      },
      rect: rectData(element.getBoundingClientRect()),
    };
    state.touched.clear();
    $(".title").textContent = `${element.tagName.toLowerCase()} ${stableSelector(element)}`;
    $(".text").value = (element.textContent ?? "").trim();
    $(".text").disabled = !state.selectedOriginal.canEditText;
    $(".color").value = rgbToHex(style.color, "#18181b");
    $(".background").value = rgbToHex(style.backgroundColor, "#ffffff");
    $(".padding").value = style.padding;
    $(".width").value = style.width;
    $(".height").value = style.height;
    $(".move-x").value = "0px";
    $(".move-y").value = "0px";
    $(".note").value = "";
    validation.textContent = "";
    editor.classList.add("open");
    outline(element);
  }

  function applyCss(requested, errors, field, property, value) {
    if (!state.touched.has(field)) return;
    const normalized = value.trim();
    if (!normalized || !CSS.supports(property, normalized)) {
      errors.push(`${field}: invalid CSS value`);
      return;
    }
    state.selected.style.setProperty(property, normalized);
    requested[field] = normalized;
  }

  function applyPreview() {
    const element = state.selected;
    const original = state.selectedOriginal;
    if (!element || !original) return null;
    restore(original);
    const requested = {};
    const errors = [];
    if (state.touched.has("text") && original.canEditText) {
      element.textContent = $(".text").value;
      requested.text = $(".text").value;
    }
    applyCss(requested, errors, "color", "color", $(".color").value);
    applyCss(requested, errors, "backgroundColor", "background-color", $(".background").value);
    applyCss(requested, errors, "padding", "padding", $(".padding").value);
    applyCss(requested, errors, "width", "width", $(".width").value);
    applyCss(requested, errors, "height", "height", $(".height").value);
    if (state.touched.has("moveX") || state.touched.has("moveY")) {
      const x = $(".move-x").value.trim() || "0px";
      const y = $(".move-y").value.trim() || "0px";
      const translate = `${x} ${y}`;
      if (CSS.supports("translate", translate)) {
        element.style.translate = translate;
        requested.move = { x, y };
      } else {
        errors.push("move: invalid CSS length");
      }
    }
    validation.textContent = errors.join("; ");
    if (errors.length) {
      restore(original);
      outline(element);
      return null;
    }
    outline(element);
    return requested;
  }

  function saveChange() {
    if (!state.selected || !state.selectedOriginal) return;
    const requested = applyPreview();
    if (requested === null) return;
    const element = state.selected;
    const original = state.selectedOriginal;
    const note = $(".note").value.trim();
    if (!Object.keys(requested).length && !note) {
      validation.textContent = "Change at least one field or add a comment.";
      return;
    }
    if (note) requested.note = note;
    state.changes.push({
      id: `change-${state.changes.length + 1}`,
      target: {
        selector: stableSelector(element),
        tag: element.tagName.toLowerCase(),
        text: original.text.trim().slice(0, 200),
        rect: original.rect,
      },
      original: { text: original.text, styles: original.computed },
      requested,
      preview: {
        rect: rectData(element.getBoundingClientRect()),
      },
      context: {
        url: location.href,
        viewport: { width: innerWidth, height: innerHeight },
        timestamp: new Date().toISOString(),
      },
    });
    state.applied.push(original);
    state.selected = null;
    state.selectedOriginal = null;
    state.touched.clear();
    editor.classList.remove("open");
    highlight.style.display = "none";
    $(".count").textContent = `${state.changes.length} changes`;
  }

  function discardAll() {
    restoreSelectedPreview();
    for (const item of [...state.applied].reverse()) restore(item);
    state.changes = [];
    state.applied = [];
    state.selected = null;
    state.touched.clear();
    editor.classList.remove("open");
    highlight.style.display = "none";
    $(".count").textContent = "0 changes";
    validation.textContent = "";
  }

  document.addEventListener("mouseover", (event) => {
    if (state.selecting && event.target instanceof HTMLElement) outline(event.target);
  }, true);
  document.addEventListener("click", (event) => {
    if (!state.selecting || !(event.target instanceof HTMLElement) || event.composedPath().includes(host)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    selectElement(event.target);
  }, true);
  window.addEventListener("scroll", () => state.selected && outline(state.selected), true);
  window.addEventListener("resize", () => {
    if (toolbar.style.transform === "none") {
      const rect = toolbar.getBoundingClientRect();
      toolbarDrag.offsetX = 0;
      toolbarDrag.offsetY = 0;
      moveToolbar(rect.left, rect.top);
    }
    if (state.selected) outline(state.selected);
  });

  shadow.querySelectorAll("[data-field]").forEach((control) => {
    control.addEventListener("input", () => {
      state.touched.add(control.dataset.field);
      validation.textContent = "";
    });
  });

  selectButton.addEventListener("click", () => {
    state.selecting = !state.selecting;
    selectButton.textContent = state.selecting ? "Selecting…" : "Select element";
    selectButton.classList.toggle("primary", !state.selecting);
  });
  $(".preview").addEventListener("click", applyPreview);
  $(".save").addEventListener("click", saveChange);
  $(".cancel").addEventListener("click", () => {
    restoreSelectedPreview();
    state.selected = null;
    state.touched.clear();
    editor.classList.remove("open");
    highlight.style.display = "none";
    validation.textContent = "";
  });
  $(".finish").addEventListener("click", () => {
    restoreSelectedPreview();
    state.selected = null;
    state.touched.clear();
    state.selecting = false;
    selectButton.textContent = "Select element";
    selectButton.classList.add("primary");
    editor.classList.remove("open");
    highlight.style.display = "none";
    validation.textContent = "";
  });
  $(".discard").addEventListener("click", discardAll);

  window.__visualUiFix = {
    host,
    install: () => ({ ready: true, version: 2 }),
    exportChanges: () => ({
      version: 2,
      page: {
        url: location.href,
        title: document.title,
        viewport: { width: innerWidth, height: innerHeight },
      },
      changes: state.changes.map((change) => structuredClone(change)),
    }),
    discardAll,
  };
})();
