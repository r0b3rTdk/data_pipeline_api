// Página: Security Events (Parte 6) — filtros + paginação + modal de detalhes
// Responsável por:
// - proteger acesso (precisa de token)
// - ler filtros/paginação do hash
// - montar querystring para /api/v1/security-events
// - renderizar: header com filtros + tabela + pager
// - exibir detalhes do item em modal (JSON)
(function () {
  async function renderSecurityEvents(app) {
    // Guard simples: se não há token, volta ao login
    if (!P01Api.isAuthed()) {
      location.hash = "#/login";
      return;
    }

    // hash esperado:
    // #/security-events?page=1&page_size=10&severity=HIGH&event_type=AUTH_FAILED
    const params = new URLSearchParams(location.hash.split("?")[1] || "");
    const page = Number(params.get("page") || 1);
    const pageSize = Number(params.get("page_size") || 10);

    // Filtros (opcionais)
    const severity = (params.get("severity") || "").trim();
    const eventType = (params.get("event_type") || "").trim();

    // UI: filtro severity (select)
    const severitySelect = P01UI.el("select", { class: "input" }, [
      option("", "ALL severities"),
      option("LOW", "LOW"),
      option("MEDIUM", "MEDIUM"),
      option("HIGH", "HIGH"),
      option("CRITICAL", "CRITICAL"),
    ]);
    severitySelect.value = severity;

    // UI: filtro event_type (input)
    const eventTypeInput = P01UI.el("input", {
      class: "input",
      placeholder: "event_type (ex: AUTH_FAILED)",
      value: eventType,
    });

    // Botões de ação
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

    // Aplicar: reseta page para 1 e atualiza rota (hash) com os filtros atuais
    btnApply.addEventListener("click", () => {
      goRoute(1, pageSize, severitySelect.value, eventTypeInput.value);
    });

    // Limpar: remove filtros e volta para a primeira página
    btnClear.addEventListener("click", () => {
      goRoute(1, pageSize, "", "");
    });

    // Header + filtros (renderiza primeiro para manter filtros visíveis durante loading)
    app.innerHTML = "";
    const header = P01UI.el("div", { class: "card" }, [
      P01UI.el("div", { class: "h1" }, ["Security Events"]),
      P01UI.el("p", { class: "p" }, [
        "Filtros mínimos: severity e event_type. Paginação por page/page_size.",
      ]),
      P01UI.el("hr", { class: "hr" }),
      P01UI.el("div", { class: "grid two" }, [
        P01UI.el("div", {}, [
          P01UI.el("p", { class: "p", style: "margin-bottom:6px;" }, [
            "Severity",
          ]),
          severitySelect,
        ]),
        P01UI.el("div", {}, [
          P01UI.el("p", { class: "p", style: "margin-bottom:6px;" }, [
            "Event type",
          ]),
          eventTypeInput,
        ]),
      ]),
      P01UI.el(
        "div",
        { class: "row", style: "margin-top:12px; justify-content:flex-end;" },
        [btnClear, btnApply]
      ),
    ]);

    app.appendChild(P01UI.el("div", { class: "grid" }, [header]));

    // Loading abaixo do header (mantém os filtros visíveis)
    const content = P01UI.el("div", { class: "card" }, []);
    content.appendChild(P01UI.el("div", { class: "h1" }, ["Carregando..."]));
    content.appendChild(
      P01UI.el("p", { class: "p" }, ["Buscando security events."])
    );
    app.appendChild(content);

    // Monta querystring para o endpoint
    const query = new URLSearchParams();
    query.set("page", String(page));
    query.set("page_size", String(pageSize));
    if (severity) query.set("severity", severity);
    if (eventType) query.set("event_type", eventType);

    try {
      // Busca na API com filtros
      const data = await P01Api.request(
        `/api/v1/security-events?${query.toString()}`,
        { method: "GET" }
      );

      const items = data.items || [];

      // Normalização do total (tolerante a nomes diferentes do campo)
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
                th("event_type"),
                th("severity"),
                th("ip"),
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
                  td(it.event_type),
                  td(it.severity),
                  td(it.ip),
                  td(it.request_id || "-"),
                  td(it.created_at),
                  tdBtn("Detalhes", () => showDetails(it)),
                ])
              )
            ),
          ]
        ),
      ]);

      // Pager + status de paginação
      const pager = P01UI.el(
        "div",
        {
          class: "row",
          style: "justify-content:space-between; margin-top:12px;",
        },
        [
          P01UI.el(
            "button",
            {
              class: "btn",
              type: "button",
              disabled: page <= 1 ? "true" : null,
              onclick: () => goRoute(page - 1, pageSize, severity, eventType),
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
              onclick: () => goRoute(page + 1, pageSize, severity, eventType),
            },
            ["Próxima →"]
          ),
        ]
      );

      // Render final dentro do bloco content
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

      // UX: Enter no input aplica filtros (reseta para page 1)
      eventTypeInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter")
          goRoute(1, pageSize, severitySelect.value, eventTypeInput.value);
      });
    } catch (err) {
      // Erro local (mantém header/filtros visíveis e mostra mensagem no content)
      content.innerHTML = "";
      content.appendChild(
        P01UI.el("div", { class: "h1" }, ["Falha ao carregar security events"])
      );
      content.appendChild(
        P01UI.el("p", { class: "p" }, [err?.message || String(err)])
      );
    }
  }

  /**
   * Atualiza o hash com paginação + filtros.
   * O app.js escuta hashchange e chama o router novamente.
   */
  function goRoute(page, pageSize, severity, eventType) {
    const qs = new URLSearchParams();
    qs.set("page", String(page));
    qs.set("page_size", String(pageSize));
    if ((severity || "").trim()) qs.set("severity", severity.trim());
    if ((eventType || "").trim()) qs.set("event_type", eventType.trim());
    location.hash = `#/security-events?${qs.toString()}`;
  }

  /** Modal simples de detalhes (JSON do item). */
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
            P01UI.el("div", { class: "h1" }, [`SecurityEvent #${item.id}`]),
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

  // Helpers de UI
  function option(value, label) {
    return P01UI.el("option", { value }, [label]);
  }

  // Helpers de tabela (mesmo padrão das outras páginas)
  function th(text) {
    return P01UI.el("th", { style: baseCellStyle(true) }, [text]);
  }
  function td(val) {
    return P01UI.el("td", { style: baseCellStyle(false) }, [String(val ?? "")]);
  }
  function tdBtn(label, onClick) {
    return P01UI.el("td", { style: baseCellStyle(false) }, [
      P01UI.el("button", { class: "btn", type: "button", onclick: onClick }, [
        label,
      ]),
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

  // Export incremental para o roteador
  window.P01Pages = window.P01Pages || {};
  window.P01Pages.renderSecurityEvents = renderSecurityEvents;
})();