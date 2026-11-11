function abrirConfiguracoes(event) {
    if (event) event.preventDefault();

    const usuario = getUsuarioLogado();
    const telaPrincipal = document.querySelector('main');
    if (!telaPrincipal) return;

    if (!usuario) {
        telaPrincipal.innerHTML = `
            <div class="categorias" style="width: 100%; text-align: center; margin-bottom: 20px;">
                <div class="text-final">
                    <section>
                        <h2 style="margin-top: 2vh;">Configurações</h2>
                        <p>Faça login para ver suas configurações.</p>
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
                    <h2 style="margin-top: 2vh;">Configurações</h2>
                </section>
            </div>
        </div>
        <div style="max-width: 400px; margin: 20px auto; background: #fff; border-radius: 10px; padding: 30px; box-shadow: 4px 4px 10px rgba(0,0,0,0.116);">
            <h3 style="font-size: 16px; margin-bottom: 8px;">Conta</h3>
            <p style="font-size: 13px; opacity: 0.7; margin-bottom: 20px;">${escapeHTML(usuario.email)}</p>

            <button id="btn-excluir-conta" type="button"
                style="background-color: #c0392b; color: #fff; border: none; border-radius: 10px; padding: 10px 20px; cursor: pointer; width: 100%;">
                Excluir minha conta
            </button>

            <p id="msg-config" style="margin-top: 12px; font-size: 13px;"></p>
        </div>
    `;

    document.getElementById('btn-excluir-conta').addEventListener('click', confirmarExclusaoConta);
}

async function confirmarExclusaoConta() {
    const usuario = getUsuarioLogado();
    const msg = document.getElementById('msg-config');

    const confirmou = confirm('Tem certeza que deseja excluir sua conta? Isso vai apagar também todos os seus favoritos, e não pode ser desfeito.');
    if (!confirmou) return;

    try {
        const resposta = await fetch('/api/usuarios/excluir', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + usuario.token
            },
            body: JSON.stringify({})
        });

        if (resposta.status === 401) {
            localStorage.removeItem('usuario');
            alert('Sua sessão expirou. Faça login novamente.');
            location.reload();
            return;
        }

        if (!resposta.ok) throw new Error('Falha ao excluir');

        localStorage.removeItem('usuario');
        alert('Conta excluída com sucesso.');
        location.reload();
    } catch (erro) {
        console.error('Erro ao excluir conta:', erro);
        msg.textContent = 'Não foi possível excluir agora. Tente de novo.';
        msg.style.color = 'red';
    }
}