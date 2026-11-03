// ===== BUSCA DE PRODUTOS (página inicial) =====

function criarSecaoCategorias() {
    // Limpa o container antes de criar para não duplicar se pesquisar de novo
    const containerCategorias = document.getElementById('icategorias');
    if (!containerCategorias) return;
    containerCategorias.innerHTML = '';

    const text = document.createElement('section');
    text.classList.add('text-final');
    text.innerHTML = `
        <h2>Melhores resultados encontrados</h2>
        <p>Confira os modelos disponíveis nas lojas encontradas!</p>
    `;
    containerCategorias.appendChild(text);
}

let buscaEmAndamento = false;

async function Produto_cliente() {
    if (buscaEmAndamento) return; // evita clique duplo gastando a cota da API

    const campo = document.getElementById('Produtos');
    const botao = document.querySelector('.inputs .resultado');
    const container = document.getElementById('container-produtos');
    if (!campo || !container) return;

    const valor = campo.value.trim();

    if (valor.length < 2) {
        window.alert('Digite o nome de um produto (mínimo 2 letras).');
        campo.focus();
        return;
    }

    buscaEmAndamento = true;
    if (botao) { botao.disabled = true; botao.value = 'Buscando...'; }
    container.innerHTML = '<p style="text-align:center; width:100%; opacity:0.7;">Buscando preços...</p>';

    try {
        const resposta = await fetch('/api/produtos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nomeProduto: valor })
        });

        const dados = await resposta.json().catch(() => null);

        if (!resposta.ok) {
            const msg = (dados && dados.erro) || 'Não foi possível buscar agora. Tente novamente.';
            container.innerHTML = `<p style="text-align:center; width:100%; color:#c0392b;">${escapeHTML(msg)}</p>`;
            return;
        }

        const listaProdutos = Array.isArray(dados) ? dados : [];

        criarSecaoCategorias();
        container.innerHTML = '';

        if (listaProdutos.length === 0) {
            container.innerHTML = '<p style="text-align:center; width:100%; opacity:0.6;">Nenhum produto encontrado. Tente outro nome.</p>';
            return;
        }

        listaProdutos.forEach((item) => {
            container.appendChild(criarElementoCard(item, { modo: 'busca' }));
        });

        // rola até os resultados uma vez só (antes rolava a cada produto)
        document.getElementById('icategorias').scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (erro) {
        console.error('Erro na conexão ao buscar API:', erro);
        container.innerHTML = '<p style="text-align:center; width:100%; opacity:0.7;">Sem conexão com o servidor. Tente novamente.</p>';
    } finally {
        buscaEmAndamento = false;
        if (botao) { botao.disabled = false; botao.value = 'Comparar preços'; }
    }
}

// Enter no campo de busca também pesquisa.
// (delegação no document: continua funcionando depois que a página inicial é restaurada)
document.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && event.target && event.target.id === 'Produtos') {
        event.preventDefault();
        Produto_cliente();
    }
});

function create_cont(event) {
    if (event) event.preventDefault();
    window.location.href = 'Front-end/create_user.html';
}

function entrar(event) {
    if (event) event.preventDefault();
    window.location.href = 'Front-end/entrar.html';
}
