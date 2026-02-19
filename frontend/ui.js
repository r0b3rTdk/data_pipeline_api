/**
 * P01UI — helpers pequenos de UI (vanilla JS)
 * Centraliza utilitários de DOM para manter as telas consistentes e evitar repetição.
 */
(function () {
  /**
   * Cria um elemento DOM com atributos, handlers de eventos e filhos.
   * @param {string} tag
   * @param {Record<string, any>} [attrs]
   * @param {Array<string|Node|null|undefined>} [children]
   * @returns {HTMLElement}
   */
  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);

    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "class") node.className = v;
      else if (k === "html") node.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") {
        // Ex.: onClick -> evento "click"
        node.addEventListener(k.slice(2), v);
      } else node.setAttribute(k, String(v));
    }

    for (const c of children) {
      if (c == null) continue;
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }

    return node;
  }

  /** Marca o link ativo do menu superior via a[data-route]. */
  function setActiveNav(routeKey) {
    const nav = document.getElementById("nav");
    if (!nav) return;

    nav.querySelectorAll("a[data-route]").forEach((a) => {
      a.classList.toggle("active", a.getAttribute("data-route") === routeKey);
    });
  }

  /** Substitui o conteúdo do target por um estado de carregamento. */
  function renderLoading(target, text = "Carregando...") {
    target.innerHTML = "";
    target.appendChild(
      el("div", { class: "card" }, [
        el("div", { class: "h1" }, [text]),
        el("p", { class: "p" }, ["Aguarde."]),
      ])
    );
  }

  /** Substitui o conteúdo do target por um estado de erro com mensagem. */
  function renderError(target, title, err) {
    const msg = err?.message || String(err || "");
    target.innerHTML = "";
    target.appendChild(
      el("div", { class: "alert" }, [
        el("div", { class: "h1" }, [title]),
        el("p", { class: "p" }, [msg]),
      ])
    );
  }

  /** Atualiza o badge de ambiente com base na URL base configurada para a API. */
  function setEnvBadge() {
    const badge = document.getElementById("envBadge");
    if (!badge) return;

    const base = window.P01Api?.API_BASE_URL || "";
    badge.textContent = "API: " + base;

    // Garante classe base + variação de ambiente (local vs fora do local).
    badge.classList.add("badge", base.includes("localhost") ? "ok" : "warn");
  }

  // Namespace global para consumo por outros scripts sem bundler/imports.
  window.P01UI = { el, setActiveNav, renderLoading, renderError, setEnvBadge };
})();