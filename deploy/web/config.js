// deploy/web/config.js
// Configuração de endpoints remotos para RedWar (WebSocket & REST API).
// Valores definidos aqui têm precedência sobre os padrões locais.
// Também podem ser substituídos em tempo de execução via localStorage (ex: localStorage.setItem('redwar_ws_url', '...'))
// ou via variáveis de ambiente no GitHub Pages deployment.
window.REDWAR_WS_URL = window.REDWAR_WS_URL || "";
window.REDWAR_API_URL = window.REDWAR_API_URL || "";
