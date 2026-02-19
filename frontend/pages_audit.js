// Página: Audit Logs (Parte 7) — filtros + paginação + modal de detalhes
// Responsável por:
// - ler paginação/filtros do hash (#/audit?page=1&page_size=10&action=...)
// - montar querystring para /api/v1/audit
// - renderizar: header com filtros + tabela + pager
// - abrir modal com JSON completo do item
(function () {
  async function renderAudit(app) {
    // Guard simples: exige token (sessão no front)
    if (!P01Api.isAuthed()) {
      location.hash = "#/login";
      return;
    }

    // hash esperado:
    // #/audit?page=1&page_size=10&action=...&entity_type=...&user_id=...
    const params = new URLSearchParams(location.hash.split("?")[1] || "");
    const page = Number(params.get("page") || 1);
    const pageSize = Number(params.get("page_size") || 10);

    // Filtros (opcionais)
    const action = (params.get("action") || "").trim();
    const entityType = (params.get("entity_type") || "").trim();
    const userId = (params.get("user_id") || "").trim();

    // UI: inputs de filtro (mantém valores conforme o hash)
    const actionInput = P01UI.el("input", {
      class: "input",
      placeholder: "action (ex: UPDATE_USER)",
      value: action,
    });
    const entityTypeInput = P01UI.el("input", {
      class: "input",
      placeholder: "entity_type (ex: trusted_event)",
      value: entityType,
    });
    const userIdInput = P01UI.el("input", {
      class: "input",
      placeholder: "user_id (ex: 1)",
      value: userId,
    });

    // Ações
    const btnApply = P01UI.el(
      "button",
      { class: "btn primary", type: "button" },
      ["Aplicar"]
    );
    const btnClear = P01UI.el(
      "button",
      { class: "btn", type: "button" },
      ["Limpar"]
    );

    // Aplicar: reseta page para 1 e atualiza hash com filtros atuais
    btnApply.addEventListener("click", () => {
      goRoute(1, pageSize, actionInput.value, entityTypeInput.value, userIdInput.value);
    });

    // Limpar: remove filtros e volta para page 1
    btnClear.addEventListener("click", () => {
      goRoute(1, pageSize, "", "", "");
    });

    // Header + filtros (renderiza primeiro para não “sumir” durante loading)
    app.innerHTML = "";
    const header = P01UI.el("div", { class: "card" }, [
      P01UI.el("div", { class: "h1" }, ["Audit Logs"]),
      P01UI.el("p", { class: "p" }, [
        "Lista paginada + filtros simples (se o backend suportar query params).",
      ]),
      P01UI.el("hr", { class: "hr" }),
      P01UI.el("div", { class: "grid two" }, [
        P01UI.el("div", {}, [
          P01UI.el("p", { class: "p", style: "margin-bottom:6px;" }, ["Action"]),
          actionInput,
        ]),
        P01UI.el("div", {}, [
          P01UI.el("p", { class: "p", style: "margin-bottom:6px;" }, ["Entity type"]),
          entityTypeInput,
        ]),
      ]),
      P01UI.el("div", {}, [
        P01UI.el("p", { class: "p", style: "margin:10px 0 6px;" }, ["User id"]),
        userIdInput,
      ]),
      P01UI.el(
        "div",
        { class: "row", style: "margin-top:12px; justify-content:flex-end;" },
        [btnClear, btnApply]
      ),
    ]);

    app.appendChild(P01UI.el("div", { class: "grid" }, [header]));

    // Content: resultados (carrega abaixo do header)
    const content = P01UI.el("div", { class: "card" }, [
      P01UI.el("div", { class: "h1" }, ["Carregando..."]),
      P01UI.el("p", { class: "p" }, ["Buscando audit logs."]),
    ]);
    app.appendChild(content);

    // Monta query para a API (inclui filtros apenas se preenchidos)
    const query = new URLSearchParams();
    query.set("page", String(page));
    query.set("page_size", String(pageSize));
    if (action) query.set("action", action);
    if (entityType) query.set("entity_type", entityType);
    if (userId) query.set("user_id", userId);

    try {
      // Chamada paginada na API
      const data = await P01Api.request(`/api/v1/audit?${query.toString()}`, {
        method: "GET",
      });

      const items = data.items || [];

      // Normalização do total (tolerante a nomes diferentes de campo)
      const totalFromApi = Number(
        data.total ?? data.total_items ?? data.total_count ?? data.count ?? NaN
      );
      const total =
        Number.isFinite(totalFromApi) && totalFromApi >= items.length
          ? totalFromApi
          : items.length;

      const totalPages = Math.max(1, Math.ceil(total / pageSize));

      // Tabela (scroll horizontal em telas pequenas)
      const table = P01UI.el("div", { style: "overflow:auto;" }, [
        P01UI.el(
          "table",
          { style: "width:100%; border-collapse:collapse; font-size:14px;" },
          [
            P01UI.el("thead", {}, [
              P01UI.el("tr", {}, [
                th("id"),
                th("action"),
                th("entity_type"),
                th("entity_id"),
                th("user_id"),
                th("reason"),
                th("request_id"),
                th("created_at"),
                th(""),
              ]),
            ]),
            P01UI.el(
              "tbody",
              {},
              items.map((it) =>
                P01UI.el("tr", {}, [
                  td(it.id),
                  td(it.action),
                  td(it.entity_type),
                  td(it.entity_id),
                  td(it.user_id),
                  // UX: reason costuma ser grande → trunca na tabela
                  td(short(it.reason, 50)),
                  // request_id é útil, mas pode ser longo → trunca
                  td(short(it.request_id || "-", 20)),
                  td(it.created_at),
                  tdBtn("Detalhes", () => showDetails(it)),
                ])
              )
            ),
          ]
        ),
      ]);

      // Pager (mantém filtros ao navegar)
      const pager = P01UI.el(
        "div",
        { class: "row", style: "justify-content:space-between; margin-top:12px;" },
        [
          P01UI.el(
            "button",
            {
              class: "btn",
              type: "button",
              disabled: page <= 1 ? "true" : null,
              onclick: () => goRoute(page - 1, pageSize, action, entityType, userId),
            },
            ["← Anterior"]
          ),
          P01UI.el("p", { class: "p" }, [
            `Página ${page} de ${totalPages} • Total: ${total}`,
          ]),
          P01UI.el(
            "button",
            {
              class: "btn",
              type: "button",
              disabled: page >= totalPages ? "true" : null,
              onclick: () => goRoute(page + 1, pageSize, action, entityType, userId),
            },
            ["Próxima →"]
          ),
        ]
      );

      // Render final dentro do content (header permanece)
      content.innerHTML = "";
      content.appendChild(
        P01UI.el(
          "div",
          { class: "row", style: "justify-content:space-between; margin-bottom:10px;" },
          [
            P01UI.el("div", { class: "muted" }, ["Resultados"]),
            P01UI.el("div", { class: "muted" }, [`page_size: ${pageSize}`]),
          ]
        )
      );
      content.appendChild(table);
      content.appendChild(pager);

      // UX: Enter em qualquer input aplica filtros (reseta para page 1)
      [actionInput, entityTypeInput, userIdInput].forEach((inp) => {
        inp.addEventListener("keydown", (e) => {
          if (e.key === "Enter")
            goRoute(1, pageSize, actionInput.value, entityTypeInput.value, userIdInput.value);
        });
      });
    } catch (err) {
      // Mantém o header e mostra a falha no content
      content.innerHTML = "";
      content.appendChild(P01UI.el("div", { class: "h1" }, ["Falha ao carregar audit logs"]));
      content.appendChild(P01UI.el("p", { class: "p" }, [err?.message || String(err)]));
      content.appendChild(
        P01UI.el("p", { class: "p", style: "margin-top:8px;" }, [
          "Obs: Se seu backend usar outra rota (ex: /api/v1/audit-logs), ajuste o path.",
        ])
      );
    }
  }

  /**
   * Atualiza o hash com paginação + filtros.
   * O app.js escuta hashchange e re-renderiza a rota.
   */
  function goRoute(page, pageSize, action, entityType, userId) {
    const qs = new URLSearchParams();
    qs.set("page", String(page));
    qs.set("page_size", String(pageSize));
    if ((action || "").trim()) qs.set("action", action.trim());
    if ((entityType || "").trim()) qs.set("entity_type", entityType.trim());
    if ((userId || "").trim()) qs.set("user_id", userId.trim());
    location.hash = `#/audit?${qs.toString()}`;
  }

  /** Modal simples com o item completo em JSON. */
  function showDetails(item) {
    const overlay = P01UI.el("div", {
      style: `
        position:fixed; inset:0;
        background: rgba(0,0,0,.55);
        display:flex; align-items:center; justify-content:center;
        padding: 16px;
      `,
    });

    const modal = P01UI.el(
      "div",
      {
        class: "card",
        style: "max-width:900px; width:100%; max-height:85vh; overflow:auto;",
      },
      [
        P01UI.el(
          "div",
          { class: "row", style: "justify-content:space-between; align-items:center;" },
          [
            P01UI.el("div", { class: "h1" }, [`Audit #${item.id}`]),
            P01UI.el(
              "button",
              { class: "btn", type: "button", onclick: () => overlay.remove() },
              ["Fechar"]
            ),
          ]
        ),
        P01UI.el(
          "pre",
          {
            style: `
              margin: 12px 0 0 0;
              padding: 12px;
              border-radius: 12px;
              border: 1px solid rgba(34,48,67,.8);
              background: rgba(0,0,0,.25);
              color: #e6edf3;
              white-space: pre-wrap;
              word-break: break-word;
              font-size: 12px;
              line-height: 1.45;
            `,
          },
          [JSON.stringify(item, null, 2)]
        ),
      ]
    );

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
  }

  /** Trunca texto para manter tabela enxuta. */
  function short(text, max) {
    const s = String(text ?? "");
    if (s.length <= max) return s;
    return s.slice(0, max - 1) + "…";
  }

  // Helpers de tabela (padroniza estilo de th/td e reduz repetição)
  function th(text) {
    return P01UI.el("th", { style: baseCellStyle(true) }, [text]);
  }
  function td(val) {
    return P01UI.el("td", { style: baseCellStyle(false) }, [String(val ?? "")]);
  }
  function tdBtn(label, onClick) {
    return P01UI.el("td", { style: baseCellStyle(false) }, [
      P01UI.el("button", { class: "btn", type: "button", onclick: onClick }, [label]),
    ]);
  }
  function baseCellStyle(isHeader) {
    return `
      padding: 10px 8px;
      border-bottom: 1px solid rgba(34,48,67,.6);
      text-align: left;
      ${isHeader ? "color:#9fb0c0; font-weight:700;" : ""}
    `;
  }

  // Export incremental para o roteador (app.js)
  window.P01Pages = window.P01Pages || {};
  window.P01Pages.renderAudit = renderAudit;
})();