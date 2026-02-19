// App bootstrap + roteamento via hash + guard de autenticação
// Responsável por:
// - decidir qual "tela" renderizar com base em location.hash
// - controlar visibilidade do menu
// - gerenciar login/logout e reação a 401 (token inválido)
(function () {
  const app = document.getElementById("app");
  const nav = document.getElementById("nav");
  const btnLogout = document.getElementById("btnLogout");

  /** Extrai a rota do hash (#/login, #/dashboard, etc.). */
  function routeFromHash() {
    const h = location.hash || "#/login";
    const m = h.match(/^#\/([^?]+)(\?.*)?$/);
    return m ? m[1] : "login";
  }

  /** Mostra/esconde o menu superior (nav) sem remover do DOM. */
  function showNav(visible) {
    if (!nav) return;
    nav.classList.toggle("hidden", !visible);
  }

  /**
   * Guard de autenticação:
   * - se não houver token, força navegação para /login
   * - retorna boolean para o caller decidir abortar render
   */
  function requireAuth() {
    if (!P01Api.isAuthed()) {
      location.hash = "#/login";
      return false;
    }
    return true;
  }

  /** Renderiza a tela de login (cria DOM via P01UI.el). */
  function renderLogin() {
    showNav(false);
    P01UI.setActiveNav(null);

    app.innerHTML = "";

    const usernameInput = P01UI.el("input", {
      class: "input",
      placeholder: "username",
      autocomplete: "username",
    });

    const passwordInput = P01UI.el("input", {
      class: "input",
      placeholder: "password",
      type: "password",
      autocomplete: "current-password",
    });

    const msgBox = P01UI.el("p", { class: "p", style: "margin-top:10px;" }, [""]);

    const btn = P01UI.el(
      "button",
      { class: "btn primary", type: "button" },
      ["Entrar"]
    );

    /** Executa login: desabilita botão, chama API e redireciona em caso de sucesso. */
    async function doLogin() {
      const username = usernameInput.value.trim();
      const password = passwordInput.value;

      msgBox.textContent = "";
      btn.disabled = true;
      btn.textContent = "Entrando...";

      try {
        await P01Api.login(username, password);
        location.hash = "#/dashboard";
      } catch (err) {
        msgBox.textContent = "Falha no login: " + (err?.message || String(err));
      } finally {
        btn.disabled = false;
        btn.textContent = "Entrar";
      }
    }

    btn.addEventListener("click", doLogin);

    const form = P01UI.el("div", { class: "card" }, [
      P01UI.el("div", { class: "h1" }, ["Login"]),
      P01UI.el("p", { class: "p" }, [
        "Use seu usuário e senha (JWT). Após login, o token fica no localStorage e será usado nas chamadas.",
      ]),
      P01UI.el("hr", { class: "hr" }),
      P01UI.el("div", { class: "grid two" }, [usernameInput, passwordInput]),
      P01UI.el(
        "div",
        { class: "row", style: "margin-top:12px; justify-content:flex-end;" },
        [btn]
      ),
      msgBox,
      P01UI.el("p", { class: "p", style: "margin-top:12px;" }, [
        "API: ",
        P01UI.el("span", { class: "badge ok" }, [P01Api.API_BASE_URL]),
      ]),
    ]);

    // UX: Enter no password executa login; Enter no username move foco para password
    passwordInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") doLogin();
    });
    usernameInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") passwordInput.focus();
    });

    app.appendChild(form);
    usernameInput.focus();
  }

  /** Renderiza dashboard (métricas) consumindo /api/v1/metrics. */
  async function renderDashboard() {
    if (!requireAuth()) return;
    showNav(true);
    P01UI.setActiveNav("dashboard");

    P01UI.renderLoading(app, "Carregando métricas...");

    try {
      const data = await P01Api.request("/api/v1/metrics", { method: "GET" });

      // Estrutura esperada (exemplo):
      // {
      //   total_raw, total_trusted, total_rejected,
      //   rejection_rate, duplicates,
      //   top_rejection_categories: [{ category, count }, ...]
      // }

      const cards = [
        { label: "RAW", value: data.total_raw },
        { label: "TRUSTED", value: data.total_trusted },
        { label: "REJECTED", value: data.total_rejected },
        {
          label: "Rejection rate",
          value:
            typeof data.rejection_rate === "number"
              ? (data.rejection_rate * 100).toFixed(1) + "%"
              : "-",
        },
        { label: "Duplicates", value: data.duplicates },
      ];

      // OBS: você usa "grid three" aqui; garanta que exista CSS pra isso
      const cardsGrid = P01UI.el(
        "div",
        { class: "grid three" },
        cards.map((c) =>
          P01UI.el("div", { class: "card" }, [
            P01UI.el("div", { class: "h1" }, [String(c.value ?? "-")]),
            P01UI.el("p", { class: "p" }, [c.label]),
          ])
        )
      );

      const top = Array.isArray(data.top_rejection_categories)
        ? data.top_rejection_categories
        : [];

      const topList = top.length
        ? P01UI.el("div", { class: "card" }, [
            P01UI.el("div", { class: "h1" }, ["Top rejection categories"]),
            P01UI.el(
              "p",
              { class: "p", style: "margin-bottom:10px;" },
              ["Mais frequentes (amostra curta)."]
            ),
            P01UI.el(
              "div",
              {},
              top.slice(0, 8).map((item) => {
                const category =
                  typeof item === "string" ? item : item.category ?? "-";
                const count =
                  typeof item === "object" && item ? item.count ?? "-" : "-";

                return P01UI.el(
                  "div",
                  {
                    class: "row",
                    style:
                      "justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(34,48,67,.6);",
                  },
                  [
                    P01UI.el("span", { class: "muted" }, [String(category)]),
                    P01UI.el("span", {}, [String(count)]),
                  ]
                );
              })
            ),
          ])
        : P01UI.el("div", { class: "card" }, [
            P01UI.el("div", { class: "h1" }, ["Top rejection categories"]),
            P01UI.el("p", { class: "p" }, [
              "Sem dados para exibir (ainda não houve rejeições ou endpoint não retorna lista).",
            ]),
          ]);

      app.innerHTML = "";
      app.appendChild(
        P01UI.el("div", { class: "grid" }, [cardsGrid, topList])
      );
    } catch (err) {
      P01UI.renderError(app, "Falha ao carregar métricas", err);
    }
  }

  /**
   * Renderiza telas ainda não implementadas (útil durante construção incremental).
   * Mantém o fluxo auth/roteamento funcionando enquanto as páginas reais evoluem.
   */
  function renderPlaceholder(routeKey, title) {
    if (!requireAuth()) return;
    showNav(true);
    P01UI.setActiveNav(routeKey);

    app.innerHTML = "";
    app.appendChild(
      P01UI.el("div", { class: "card" }, [
        P01UI.el("div", { class: "h1" }, [title, " (placeholder)"]),
        P01UI.el("p", { class: "p" }, [
          "Login/Token/Guard OK. Essa tela será implementada nas próximas partes.",
        ]),
      ])
    );
  }

  /** Render padrão para rota inexistente. */
  function renderNotFound(routeKey) {
    showNav(true);
    P01UI.setActiveNav(null);

    app.innerHTML = "";
    app.appendChild(
      P01UI.el("div", { class: "card" }, [
        P01UI.el("div", { class: "h1" }, ["Rota não encontrada"]),
        P01UI.el("p", { class: "p" }, ["Route: ", routeKey]),
      ])
    );
  }

  /**
   * Router principal:
   * - decide o que renderizar com base no hash
   * - aplica guard de auth nas rotas protegidas
   * - delega render das páginas em window.P01Pages (trusted/rejections/etc.)
   */
  function render() {
    // Atualiza badge de ambiente (base URL)
    P01UI.setEnvBadge();

    const route = routeFromHash();

    // Se já estiver logado e cair em /login, redireciona para dashboard
    if (route === "login" && P01Api.isAuthed()) {
      location.hash = "#/dashboard";
      return;
    }

    if (route === "login" || route === "") return renderLogin();
    if (route === "dashboard") return renderDashboard();

    // Páginas delegadas: exigem que window.P01Pages exista e exporte renderX(app)
    if (route === "trusted") {
      if (!requireAuth()) return;
      showNav(true);
      P01UI.setActiveNav("trusted");
      return window.P01Pages.renderTrusted(app);
    }

    if (route === "rejections") {
      if (!requireAuth()) return;
      showNav(true);
      P01UI.setActiveNav("rejections");
      return window.P01Pages.renderRejections(app);
    }

    if (route === "security-events") {
      if (!requireAuth()) return;
      showNav(true);
      P01UI.setActiveNav("security-events");
      return window.P01Pages.renderSecurityEvents(app);
    }

    if (route === "audit") {
      if (!requireAuth()) return;
      showNav(true);
      P01UI.setActiveNav("audit");
      return window.P01Pages.renderAudit(app);
    }

    return renderNotFound(route);
  }

  // Re-renderiza quando o hash muda (navegação sem recarregar a página)
  window.addEventListener("hashchange", render);

  // 401 → api.js dispara p01:unauthorized; aqui o app reage voltando pro login
  window.addEventListener("p01:unauthorized", () => {
    location.hash = "#/login";
  });

  // Logout manual: limpa token e volta pro login
  if (btnLogout) {
    btnLogout.addEventListener("click", () => {
      P01Api.clearToken();
      location.hash = "#/login";
    });
  }

  // Bootstrap inicial: garante uma rota padrão e faz o primeiro render
  if (!location.hash) location.hash = "#/login";
  render();
})();