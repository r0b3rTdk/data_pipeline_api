// Cliente de API: baseURL + Bearer token + guard de 401 (expira/invalidou) + helper de JSON
(function () {
  // Config global opcional (ex.: setado no index.html antes de carregar este script)
  const config = window.__APP_CONFIG__ || {};
  const API_BASE_URL = config.API_BASE_URL || "http://localhost:8000";

  // Onde o token JWT fica armazenado no navegador
  const TOKEN_KEY = "p01_access_token";

  /** Lê o token atual do localStorage (ou null se não existir). */
  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  /** Persiste o token no localStorage. */
  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  /** Remove o token (ex.: logout ou token inválido). */
  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  /** Retorna true/false se existe token salvo (autenticado no front). */
  function isAuthed() {
    return !!getToken();
  }

  /**
   * request(path, options)
   * Wrapper de fetch com:
   * - baseURL configurável
   * - Accept: application/json
   * - Authorization: Bearer <token> (se existir)
   * - options.json -> faz JSON.stringify e seta Content-Type automaticamente
   * - tratamento de erro padronizado com msg + status + data
   * - guard de 401: limpa token e notifica a UI para forçar login
   */
  async function request(path, options = {}) {
    // Normaliza baseURL (remove barra final) e concatena com o path
    const url = API_BASE_URL.replace(/\/$/, "") + path;

    // Monta headers a partir do que vier em options
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");

    // Se tiver token, injeta Bearer
    const token = getToken();
    if (token) headers.set("Authorization", "Bearer " + token);

    // Helper para enviar body como JSON:
    // permite chamar request(..., { json: {...} }) ao invés de montar body manualmente.
    if (options.json !== undefined) {
      headers.set("Content-Type", "application/json");
      options.body = JSON.stringify(options.json);
      delete options.json; // evita repassar "json" para o fetch
    }

    // Executa fetch com headers normalizados
    const resp = await fetch(url, { ...options, headers });

    // Guard: token inválido/expirado (401) -> limpa token e sinaliza a aplicação
    // A UI pode escutar esse evento e redirecionar para tela de login.
    if (resp.status === 401) {
      clearToken();
      window.dispatchEvent(new CustomEvent("p01:unauthorized"));
      throw new Error("401 Unauthorized");
    }

    // Tenta ler body (json ou texto) para mensagens de erro mais úteis
    const contentType = resp.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");

    let data = null;

    // 204 (No Content) não possui body
    if (resp.status !== 204) {
      data = isJson
        ? await resp.json().catch(() => null)
        : await resp.text().catch(() => null);
    }

    // Se não for 2xx, cria um Error melhorado com status e payload
    if (!resp.ok) {
      const msg =
        (data && (data.detail || data.message)) ||
        (typeof data === "string" ? data : null) ||
        resp.statusText;

      const err = new Error(msg);
      err.status = resp.status;
      err.data = data;
      throw err;
    }

    // Sucesso: devolve o body já interpretado (json/texto) ou null (204)
    return data;
  }

  /**
   * login(username, password)
   * Endpoint de autenticação (JWT):
   * - faz POST /api/v1/auth/login
   * - espera receber { access_token: "..." }
   * - salva token no localStorage para requisições futuras
   */
  async function login(username, password) {
    const data = await request("/api/v1/auth/login", {
      method: "POST",
      json: { username, password },
    });

    if (!data || !data.access_token) {
      throw new Error("Resposta de login inválida (access_token ausente).");
    }

    setToken(data.access_token);
    return data.access_token;
  }

  // Exporta um namespace global simples (sem bundler/imports)
  window.P01Api = {
    API_BASE_URL,
    TOKEN_KEY,
    getToken,
    setToken,
    clearToken,
    isAuthed,
    request,
    login,
  };
})();