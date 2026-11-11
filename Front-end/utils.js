// ===== FUNÇÕES COMPARTILHADAS =====
// Este arquivo precisa ser carregado ANTES dos outros scripts do index.html.

// Transforma texto em algo seguro para colocar dentro de HTML.
// Use sempre que for montar HTML com dados que vieram da API, do banco ou do usuário
// (nome de produto, nome do usuário, links...). Sem isso, alguém poderia colocar
// <script> ou <img onerror=...> no nome e rodar código na tela dos outros.
function escapeHTML(valor) {
    const mapa = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return String(valor ?? '').replace(/[&<>"']/g, (c) => mapa[c]);
}

// Só deixa passar links http(s) completos. Bloqueia "javascript:", "data:", vazio e parecidos.
function urlSegura(url) {
    if (typeof url !== 'string' || url.trim() === '') return '';
    try {
        const u = new URL(url.trim()); // sem base: link relativo/incompleto dá erro e vira ''
        return (u.protocol === 'http:' || u.protocol === 'https:') ? u.href : '';
    } catch (e) {
        return '';
    }
}

// A SerpAPI já manda o preço pronto ("R$ 1.299,00"). Só coloca o "R$" se faltar.
function formatarPreco(preco) {
    const texto = String(preco ?? '').trim();
    if (!texto) return 'Preço indisponível';
    return /R\$/.test(texto) ? texto : 'R$ ' + texto;
}

// Converte preços brasileiros ("R$ 1.299,90") para número para ordenação.
function valorNumericoPreco(preco) {
    const texto = String(preco ?? '').replace(/[^\d,.-]/g, '').trim();
    if (!texto) return Number.POSITIVE_INFINITY;
    const normalizado = texto.includes(',')
        ? texto.replace(/\./g, '').replace(',', '.')
        : texto;
    const valor = Number(normalizado);
    return Number.isFinite(valor) ? valor : Number.POSITIVE_INFINITY;
}

function ordenarProdutosPorPreco(lista, ordem) {
    return [...lista].sort((a, b) => {
        const diferenca = valorNumericoPreco(a.preco) - valorNumericoPreco(b.preco);
        return ordem === 'maior-menor' ? -diferenca : diferenca;
    });
}

function renderizarOrdenacaoPreco(container, lista, opcoes = {}) {
    const controles = document.createElement('div');
    controles.className = 'ordenacao-preco';
    controles.innerHTML = `
        <label for="ordenar-preco">Ordenar por preço</label>
        <select id="ordenar-preco" aria-label="Ordenar produtos por preço">
            <option value="menor-maior">Menor para maior</option>
            <option value="maior-menor">Maior para menor</option>
        </select>`;
    const vitrine = document.createElement('div');
    vitrine.className = 'vitrine-produtos';
    vitrine.id = 'lista-produtos-ordenada';
    container.replaceChildren(controles, vitrine);
    const desenhar = () => {
        vitrine.replaceChildren(...ordenarProdutosPorPreco(lista, controles.querySelector('select').value)
            .map(item => criarElementoCard(item, opcoes)));
    };
    controles.querySelector('select').addEventListener('change', desenhar);
    desenhar();
}

// Usuário salvo no navegador ({ nome, email, foto, token }) ou null.
function getUsuarioLogado() {
    try {
        return JSON.parse(localStorage.getItem('usuario')) || null;
    } catch (e) {
        localStorage.removeItem('usuario'); // dado corrompido: limpa
        return null;
    }
}

// Foto de perfil, ou um avatar com a inicial do nome quando não houver foto
function fotoDoUsuario(usuario) {
    return urlSegura(usuario && usuario.foto) ||
        'https://ui-avatars.com/api/?name=' + encodeURIComponent((usuario && usuario.nome) || 'U');
}

// Monta o HTML de um card de produto (busca, categoria e favoritos usam o mesmo).
// item: { imagem, Icon_loja, loja, title|titulo, nota, compras, preco, link, id_favorito }
// opcoes.modo: 'busca' (botão de favoritar) ou 'favorito' (botão de remover)
function criarCardProduto(item, opcoes = {}) {
    const titulo = item.title || item.titulo || '';
    const imagem = urlSegura(item.imagem);
    const logo = urlSegura(item.Icon_loja);
    const link = urlSegura(item.link);
    const loja = item.loja || '';

    let botao;
    if (opcoes.modo === 'favorito') {
        botao = `<button type="button" class="btn-card btn-remover-favorito"
                    data-id="${escapeHTML(item.id_favorito)}" title="Remover dos favoritos">🗑️</button>`;
    } else {
        botao = `<button type="button" class="btn-card btn-favoritar"
                    title="Salvar nos favoritos"
                    data-titulo="${escapeHTML(titulo)}"
                    data-imagem="${escapeHTML(imagem)}"
                    data-preco="${escapeHTML(item.preco || '')}"
                    data-loja="${escapeHTML(loja)}"
                    data-link="${escapeHTML(link)}">🤍</button>`;
    }

    const nota = item.nota
        ? `<p class="esrelas">⭐ ${escapeHTML(item.nota)}${item.compras ? ` (${escapeHTML(item.compras)} avaliações)` : ''}</p>`
        : '';

    return `
        ${botao}
        ${imagem ? `<img src="${escapeHTML(imagem)}" alt="${escapeHTML(titulo)}" class="produto-img" loading="lazy">` : ''}
        <div class="marca-container">
            ${logo ? `<img src="${escapeHTML(logo)}" alt="" class="loja-logo" loading="lazy">` : ''}
            <span class="produto-loja">${escapeHTML(loja)}</span>
        </div>
        <h3 class="produto-titulo">${escapeHTML(titulo)}</h3>
        ${nota}
        <p class="produto-preco">${escapeHTML(formatarPreco(item.preco))}</p>
        ${link ? `<a href="${escapeHTML(link)}" target="_blank" rel="noopener noreferrer" class="produto-link">Ver na Loja</a>` : ''}
    `;
}

// Cria o <div> do card já pronto para colocar na vitrine
function criarElementoCard(item, opcoes) {
    const div = document.createElement('div');
    div.className = 'card-produto';
    div.innerHTML = criarCardProduto(item, opcoes);
    return div;
}
