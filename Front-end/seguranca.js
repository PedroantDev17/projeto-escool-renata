(function () {
    'use strict';

    // ---------- CONFIGURAÇÃO (mude aqui) ----------
    var CONFIG = {
        mensagem: 'Caracteres inválidos detectados.',
        // Caminho absoluto (começa com "/"): funciona de qualquer página do site.
        // Use null para só mostrar o alerta, sem redirecionar.
        paginaDestino: '/Front-end/video_presente/presente.html'
    };

    // ---------- PADRÕES SUSPEITOS ----------
    var PADROES_SUSPEITOS = [
        /[<>]/,                                                                           // HTML / script
        /\b(drop|delete|truncate|alter|insert|update|union|select)\b[\s\S]*\b(table|from|into|set|all)\b/i, // SQL
        /(--|;|\/\*|\*\/)/,                                                               // comentários e fim de comando SQL
        /\b(or|and)\b\s+\d+\s*=\s*\d+/i,                                                  // ' OR 1=1
        /javascript:|\bon(error|load|click|mouseover|focus|submit)\s*=/i,                 // XSS em atributos
        /\.\.[\/\\]/,                                                                     // path traversal (../)
        /(\$\(|`|\|\||&&)/                                                                // injeção de comandos
    ];

    // true se o texto parece perigoso
    function entradaSuspeita(texto) {
        if (typeof texto !== 'string') return false;
        return PADROES_SUSPEITOS.some(function (p) { return p.test(texto); });
    }

    // true se o texto está OK. Se for suspeito: avisa, redireciona (se configurado) e devolve false.
    function validarEntrada(texto) {
        if (!entradaSuspeita(texto)) return true;
        window.alert(CONFIG.mensagem);
        if (CONFIG.paginaDestino) window.location.href = CONFIG.paginaDestino;
        return false;
    }

    // ---------- MODO AUTOMÁTICO: campos com data-protegido ----------
    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!form || !form.querySelectorAll) return;
        var campos = form.querySelectorAll('[data-protegido]');
        for (var i = 0; i < campos.length; i++) {
            if (!validarEntrada(campos[i].value)) {
                event.preventDefault();
                return;
            }
        }
    }, true);

    // Deixa as funções disponíveis para os outros scripts
    window.PADROES_SUSPEITOS = PADROES_SUSPEITOS;
    window.entradaSuspeita = entradaSuspeita;
    window.validarEntrada = validarEntrada;
    window.SEGURANCA_CONFIG = CONFIG;
})();