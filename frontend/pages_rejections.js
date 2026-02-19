// Página: Rejections (lista paginada + modal de detalhes)
// Responsável por:
// - ler page/page_size do hash (#/rejections?page=1&page_size=10)
// - buscar /api/v1/rejections paginado
// - renderizar tabela com campos de rejeição
// - truncar message na tabela (short) e mostrar JSON completo no modal
(function () {
  /**
   * Render principal da página de rejeições.
   * @param {HTMLElement} app - container principal
   */
  async function renderRejections(app) {
    // Feedback imediato: estado de carregamento
    P01UI.renderLoading(app, "Carregando rejeições...");

    // Estado via querystring no hash:
    // #/rejections?page=1&page_size=10
    const params = new URLSearchParams(location.hash.split("?")[1] || "");
    const page = Number(params.get("page") || 1);
    const pageSize = Number(params.get("page_size") || 10);

    try {
      // Busca paginada
      const data = await P01Api.request(
        `/api/v1/rejections?page=${page}&page_size=${pageSize}`,
        { method: "GET" }
      );

      // Itens (fallback para array vazio)
      const items = data.items || [];

      // Normalização do total (tolerante a diferentes nomes de campo)
      const totalFromApi = Number(
        data.total ?? data.total_items ?? data.total_count ?? data.count ?? NaN
      );
      const total =
        Number.isFinite(totalFromApi) && totalFromApi >= items.length
          ? totalFromApi
          : items.length;

      const totalPages = Math.max(1, Math.ceil(total / pageSize));

      // Header (título + status de paginação)
      const header = P01UI.el("div", { class: "card" }, [
        P01UI.el("div", { class: "h1" }, ["Rejections"]),
        P01UI.el("p", { class: "p" }, [
          `Página ${page} de ${totalPages} • Total: ${total}`,
        ]),
      ]);

      // Tabela principal
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

        // Wrapper para scroll horizontal
        P01UI.el("div", { style: "overflow:auto;" }, [
          P01UI.el(
            "table",
            { style: "width:100%; border-collapse:collapse; font-size:14px;" },
            [
              P01UI.el("thead", {}, [
                P01UI.el("tr", {}, [
                  th("id"),
                  th("raw_ingestion_id"),
                  th("category"),
                  th("field"),
                  th("rule"),
                  th("severity"),
                  th("message"),
                  th("created_at"),
                  th(""),
                ]),
              ]),

              // Linhas
              P01UI.el(
                "tbody",
                {},
                items.map((it) =>
                  P01UI.el("tr", {}, [
                    td(it.id),
                    td(it.raw_ingestion_id),
                    td(it.category),
                    td(it.field),
                    td(it.rule),
                    td(it.severity),
                    // UX: na tabela mostra versão curta da mensagem (60 chars)
                    td(short(it.message, 60)),
                    td(it.created_at),
                    tdBtn("Detalhes", () => showDetails(app, it)),
                  ])
                )
              ),
            ]
          ),
        ]),
      ]);

      // Paginação (anterior / próxima)
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

      // Render final
      app.innerHTML = "";
      app.appendChild(P01UI.el("div", { class: "grid" }, [header, table, pager]));
    } catch (err) {
      // Erro padronizado
      P01UI.renderError(app, "Falha ao carregar rejections", err);
    }
  }

  /** Atualiza o hash para navegar entre páginas (dispara hashchange). */
  function goPage(page, pageSize) {
    location.hash = `#/rejections?page=${page}&page_size=${pageSize}`;
  }

  /**
   * Modal simples com JSON completo do item.
   * Mantém a tabela enxuta e permite inspeção detalhada ao clicar.
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
            P01UI.el("div", { class: "h1" }, [`Rejection #${item.id}`]),
            P01UI.el(
              "button",
              { class: "btn", type: "button", onclick: () => overlay.remove() },
              ["Fechar"]
            ),
          ]
        ),

        // JSON formatado (pretty print)
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

  /**
   * Trunca texto para caber bem na tabela.
   * Ex.: message muito grande vira "Lorem ipsu…"
   */
  function short(text, max) {
    const s = String(text ?? "");
    if (s.length <= max) return s;
    return s.slice(0, max - 1) + "…";
  }

  // Helpers de tabela para reduzir repetição
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

  /** Estilo base de células (th/td). */
  function baseCellStyle(isHeader) {
    return `
      padding: 10px 8px;
      border-bottom: 1px solid rgba(34,48,67,.6);
      text-align: left;
      ${isHeader ? "color:#9fb0c0; font-weight:700;" : ""}
    `;
  }

  // Export incremental para o roteador (app.js) chamar esta página
  window.P01Pages = window.P01Pages || {};
  window.P01Pages.renderRejections = renderRejections;
})();