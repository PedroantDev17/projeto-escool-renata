// ===== PÁGINA INICIAL / CATEGORIAS =====

let htmlOriginalDaPagina = '';

function areaPrincipal() {
    return document.querySelector('main') || document.getElementById('conteudo-principal');
}

document.addEventListener('DOMContentLoaded', () => {
    const telaPrincipal = areaPrincipal();
    if (telaPrincipal) {
        htmlOriginalDaPagina = telaPrincipal.innerHTML;
    }
});

// Restaura a tela inicial (usado pela logo e pelo botão "início")
function voltarParaInicio(event) {
    if (event) event.preventDefault();

    const telaPrincipal = areaPrincipal();
    if (telaPrincipal && htmlOriginalDaPagina) {
        telaPrincipal.innerHTML = htmlOriginalDaPagina;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Mostra a vitrine de eletrônicos
async function categorias(event) {
    if (event && event.preventDefault) event.preventDefault();

    const alvoJanela = areaPrincipal();
    if (!alvoJanela) {
        console.error("Não foi possível encontrar a tag <main> no HTML.");
        return;
    }

    alvoJanela.innerHTML = `
        <div class="categorias" style="width: 100%; text-align: center; margin-bottom: 20px;">
            <div class="text-final">
                <section>
                    <h2 style="margin-top: 2vh;">Categoria: <span style="color: var(--blue-escuro);">Eletrônicos</span></h2>
                </section>
            </div>
        </div>
        <div id="container-produtos" class="vitrine-produtos">
            <p style="text-align: center; width: 100%; opacity: 0.7;">Buscando produtos...</p>
        </div>
    `;

    const container = document.getElementById('container-produtos');

    try {
        const resposta = await fetch('/api/categoria', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const dados = await resposta.json().catch(() => null);

        if (!resposta.ok) {
            const msg = (dados && dados.erro) || 'Erro ao responder ao servidor.';
            container.innerHTML = `<p style="text-align: center; width: 100%; color: #c0392b;">${escapeHTML(msg)}</p>`;
            return;
        }

        const listaProdutos = Array.isArray(dados) ? dados : [];
        container.innerHTML = '';

        if (listaProdutos.length === 0) {
            container.innerHTML = '<p style="text-align: center; width: 100%; opacity: 0.5;">Nenhum produto encontrado para esta categoria.</p>';
            return;
        }

        listaProdutos.forEach((item) => {
            container.appendChild(criarElementoCard(item, { modo: 'busca' }));
        });

        container.scrollIntoView({ behavior: 'smooth' });

    } catch (erro) {
        console.error('Erro na conexão ao buscar API:', erro);
        container.innerHTML = '<p style="text-align: center; width: 100%; opacity: 0.7;">Servidor com problemas, tente novamente mais tarde...</p>';
    }
}
