// Página: Trusted Events (lista paginada + modal de detalhes)
// Responsável por:
// - ler page/page_size do hash (#/trusted?page=1&page_size=10)
// - buscar /api/v1/trusted paginado
// - renderizar tabela + paginação
// - abrir modal simples com JSON do item
(function () {
  /**
   * Render principal da página trusted.
   * @param {HTMLElement} app - container principal onde a página é desenhada
   */
  async function renderTrusted(app) {
    // Estado inicial: feedback imediato ao usuário
    P01UI.renderLoading(app, "Carregando trusted events...");

    // Estado via querystring no hash:
    // #/trusted?page=1&page_size=10
    const params = new URLSearchParams(location.hash.split("?")[1] || "");
    const page = Number(params.get("page") || 1);
    const pageSize = Number(params.get("page_size") || 10);

    try {
      // Busca paginada na API (token já é aplicado por P01Api.request)
      const data = await P01Api.request(
        `/api/v1/trusted?page=${page}&page_size=${pageSize}`,
        { method: "GET" }
      );

      // Lista de itens (fallback para array vazio)
      const items = data.items || [];

      // Normalização do total:
      // a API pode devolver total com chaves diferentes dependendo da implementação.
      const totalFromApi = Number(
        data.total ?? data.total_items ?? data.total_count ?? data.count ?? NaN
      );

      // Regras de segurança:
      // - se total vier inválido, usa items.length
      // - evita total menor do que a quantidade recebida
      const total =
        Number.isFinite(totalFromApi) && totalFromApi >= items.length
          ? totalFromApi
          : items.length;

      const totalPages = Math.max(1, Math.ceil(total / pageSize));

      // Cabeçalho com título + metadados da paginação
      const header = P01UI.el("div", { class: "card" }, [
        P01UI.el("div", { class: "h1" }, ["Trusted Events"]),
        P01UI.el("p", { class: "p" }, [
          `Página ${page} de ${totalPages} • Total: ${total}`,
        ]),
      ]);

      // Tabela: lista paginada + botão “Detalhes” por linha
      const table = P01UI.el("div", { class: "card" }, [
        P01UI.el(
          "div",
          {
            class: "row",
            style: "justify-content:space-between; margin-bottom:10px;",
          },
          [
            P01UI.el("div", { class: "muted" }, ["Lista paginada"]),
            P01UI.el("div", { class: "muted" }, [`page_size: ${pageSize}`]),
          ]
        ),

        // Wrapper para permitir scroll horizontal em telas pequenas
        P01UI.el("div", { style: "overflow:auto;" }, [
          P01UI.el(
            "table",
            { style: "width:100%; border-collapse:collapse; font-size:14px;" },
            [
              P01UI.el("thead", {}, [
                P01UI.el("tr", {}, [
                  th("id"),
                  th("source_id"),
                  th("external_id"),
                  th("event_type"),
                  th("event_status"),
                  th("event_timestamp"),
                  th(""),
                ]),
              ]),
              P01UI.el(
                "tbody",
                {},
                items.map((it) =>
                  P01UI.el("tr", {}, [
                    td(it.id),
                    td(it.source_id),
                    td(it.external_id),
                    td(it.event_type),
                    td(it.event_status),
                    td(it.event_timestamp),
                    tdBtn("Detalhes", () => showDetails(app, it)),
                  ])
                )
              ),
            ]
          ),
        ]),
      ]);

      // Paginação: anterior / próxima
      const pager = P01UI.el("div", { class: "card" }, [
        P01UI.el(
          "div",
          { class: "row", style: "justify-content:space-between;" },
          [
            P01UI.el(
              "button",
              {
                class: "btn",
                type: "button",
                // disabled em HTML: qualquer valor “truthy” habilita o disabled
                disabled: page <= 1 ? "true" : null,
                onclick: () => goPage(page - 1, pageSize),
              },
              ["← Anterior"]
            ),
            P01UI.el(
              "button",
              {
                class: "btn",
                type: "button",
                disabled: page >= totalPages ? "true" : null,
                onclick: () => goPage(page + 1, pageSize),
              },
              ["Próxima →"]
            ),
          ]
        ),
      ]);

      // Render final da página
      app.innerHTML = "";
      app.appendChild(P01UI.el("div", { class: "grid" }, [header, table, pager]));
    } catch (err) {
      // Erro padronizado (usa P01UI.renderError)
      P01UI.renderError(app, "Falha ao carregar trusted", err);
    }
  }

  /**
   * Navega para outra página atualizando o hash.
   * Isso dispara hashchange e o app renderiza novamente.
   */
  function goPage(page, pageSize) {
    location.hash = `#/trusted?page=${page}&page_size=${pageSize}`;
  }

  /**
   * Modal simples (overlay) mostrando o item em JSON.
   * Sem framework: cria overlay full-screen e remove ao fechar.
   */
  function showDetails(app, item) {
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
            P01UI.el("div", { class: "h1" }, [`Trusted #${item.id}`]),
            P01UI.el(
              "button",
              { class: "btn", type: "button", onclick: () => overlay.remove() },
              ["Fechar"]
            ),
          ]
        ),

        // Exibe o item com JSON formatado (pretty print)
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

  // Helpers de tabela (centralizam o estilo para reduzir repetição)
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

  /** Estilo base para células da tabela (th/td). */
  function baseCellStyle(isHeader) {
    return `
      padding: 10px 8px;
      border-bottom: 1px solid rgba(34,48,67,.6);
      text-align: left;
      ${isHeader ? "color:#9fb0c0; font-weight:700;" : ""}
    `;
  }

  // Export incremental: preserva P01Pages e adiciona renderTrusted
  window.P01Pages = window.P01Pages || {};
  window.P01Pages.renderTrusted = renderTrusted;
})();