// ===== FAVORITOS (botão de coração nos cards) =====
// Depende de utils.js (getUsuarioLogado) e do usuário salvo no localStorage
// com a chave 'usuario' contendo pelo menos { email: '...', token: '...' }

async function adicionarFavorito(botao) {
    const usuario = getUsuarioLogado();

    if (!usuario || !usuario.token) {
        alert('Faça login para favoritar produtos.');
        return;
    }

    // Pega os dados do produto guardados no próprio botão (data-*)
    // O e-mail não vai aqui: o servidor pega do token
    const dados = {
        titulo: botao.dataset.titulo,
        imagem: botao.dataset.imagem,
        preco: botao.dataset.preco,
        loja: botao.dataset.loja,
        link: botao.dataset.link
    };

    // Feedback imediato pro usuário (evita clique duplo e dá resposta visual)
    botao.disabled = true;
    botao.classList.add('favoritado');
    botao.textContent = '💙';

    function desfazerVisual() {
        botao.disabled = false;
        botao.classList.remove('favoritado');
        botao.textContent = '🤍';
    }

    try {
        const resposta = await fetch('/api/favoritos/adicionar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + usuario.token
            },
            body: JSON.stringify(dados)
        });

        if (resposta.status === 401) {
            localStorage.removeItem('usuario');
            desfazerVisual();
            alert('Sua sessão expirou. Faça login novamente.');
            location.reload();
            return;
        }

        if (!resposta.ok) {
            throw new Error('Falha ao favoritar');
        }
    } catch (erro) {
        console.error('Erro ao favoritar:', erro);
        // desfaz o feedback visual se der erro
        desfazerVisual();
        alert('Não foi possível favoritar agora. Tente de novo.');
    }
}

// Liga o clique em qualquer botão de favoritar que existir na página
// (funciona mesmo pra cards criados dinamicamente depois, via delegação de evento)
document.addEventListener('click', function (event) {
    const botao = event.target.closest('.btn-favoritar');
    if (botao) {
        adicionarFavorito(botao);
    }
});
