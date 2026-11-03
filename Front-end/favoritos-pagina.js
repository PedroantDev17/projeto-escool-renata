// ===== PÁGINA "SEUS FAVORITOS" =====
// Depende de utils.js

async function abrirFavoritos(event) {
    if (event) event.preventDefault();

    const usuario = getUsuarioLogado();

    const telaPrincipal = document.querySelector('main');
    if (!telaPrincipal) return;

    if (!usuario || !usuario.token) {
        telaPrincipal.innerHTML = `
            <div class="categorias" style="width: 100%; text-align: center; margin-bottom: 20px;">
                <div class="text-final">
                    <section>
                        <h2 style="margin-top: 2vh;">Seus favoritos</h2>
                        <p>Faça login para ver e salvar seus produtos favoritos.</p>
                    </section>
                </div>
            </div>
        `;
        return;
    }

    telaPrincipal.innerHTML = `
        <div class="categorias" style="width: 100%; text-align: center; margin-bottom: 20px;">
            <div class="text-final">
                <section>
                    <h2 style="margin-top: 2vh;">Seus favoritos</h2>
                </section>
            </div>
        </div>
        <div id="container-produtos" class="vitrine-produtos">
            <p style="text-align: center; width: 100%; opacity: 0.7;">Carregando seus favoritos...</p>
        </div>
    `;

    try {
        // O e-mail não vai no corpo: o servidor pega do token
        const resposta = await fetch('/api/favoritos/listar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + usuario.token
            },
            body: JSON.stringify({})
        });

        const containerProdutos = document.getElementById('container-produtos');
        if (!containerProdutos) return;

        // Sessão expirada ou usuário logado antes da atualização (sem token)
        if (resposta.status === 401) {
            localStorage.removeItem('usuario');
            containerProdutos.innerHTML = '<p style="text-align: center; width: 100%;">Sua sessão expirou. Faça login novamente para ver seus favoritos.</p>';
            return;
        }

        if (!resposta.ok) {
            containerProdutos.innerHTML = '<p style="text-align: center; width: 100%; color: #c0392b;">Erro ao buscar seus favoritos.</p>';
            return;
        }

        const listaFavoritos = await resposta.json();
        containerProdutos.innerHTML = '';

        if (listaFavoritos.length === 0) {
            containerProdutos.innerHTML = '<p style="text-align: center; width: 100%; opacity: 0.5;">Você ainda não tem favoritos salvos.</p>';
            return;
        }

        listaFavoritos.forEach((item) => {
            containerProdutos.appendChild(criarElementoCard(item, { modo: 'favorito' }));
        });

    } catch (erro) {
        console.error('Erro ao carregar favoritos:', erro);
        const container = document.getElementById('container-produtos');
        if (container) {
            container.innerHTML = '<p style="text-align: center; width: 100%; opacity: 0.7;">Servidor com problemas, tente novamente mais tarde...</p>';
        }
    }
}

// Remove favorito ao clicar na lixeira (delegação de evento, funciona em cards criados dinamicamente)
document.addEventListener('click', async function (event) {
    const botao = event.target.closest('.btn-remover-favorito');
    if (!botao) return;

    const usuario = getUsuarioLogado();
    if (!usuario || !usuario.token) return;

    const idFavorito = botao.dataset.id;

    botao.disabled = true;

    try {
        const resposta = await fetch('/api/favoritos/remover', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + usuario.token
            },
            body: JSON.stringify({ id_favorito: idFavorito })
        });

        // Sessão expirada ou usuário logado antes da atualização (sem token)
        if (resposta.status === 401) {
            localStorage.removeItem('usuario');
            botao.disabled = false;
            alert('Sua sessão expirou. Faça login novamente.');
            location.reload();
            return;
        }

        if (resposta.ok) {
            // remove o card da tela sem precisar recarregar a lista inteira
            botao.closest('.card-produto').remove();
        } else {
            botao.disabled = false;
            alert('Não foi possível remover agora. Tente de novo.');
        }
    } catch (erro) {
        console.error('Erro ao remover favorito:', erro);
        botao.disabled = false;
    }
});
