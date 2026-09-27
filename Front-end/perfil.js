function abrirPerfil(event) {
    if (event) event.preventDefault();

    const usuario = getUsuarioLogado();
    const telaPrincipal = document.querySelector('main');
    if (!telaPrincipal) return;

    if (!usuario) {
        telaPrincipal.innerHTML = `
            <div class="categorias" style="width: 100%; text-align: center; margin-bottom: 20px;">
                <div class="text-final">
                    <section>
                        <h2 style="margin-top: 2vh;">Meu perfil</h2>
                        <p>Faça login para ver seu perfil.</p>
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
                    <h2 style="margin-top: 2vh;">Meu perfil</h2>
                </section>
            </div>
        </div>
        <div style="max-width: 400px; margin: 20px auto; background: #fff; border-radius: 10px; padding: 30px; box-shadow: 4px 4px 10px rgba(0,0,0,0.116); text-align: center;">
            <img src="${usuario.foto}" alt="Foto de perfil" style="width: 90px; height: 90px; border-radius: 50%; border: 2px solid var(--blue-escuro); object-fit: cover; margin-bottom: 15px;">

            <p style="opacity: 0.6; font-size: 13px; margin-bottom: 20px;">${usuario.email}</p>

            <label for="input-nome-perfil" style="display: block; text-align: left; font-size: 13px; margin-bottom: 5px; opacity: 0.7;">Nome</label>
            <input type="text" id="input-nome-perfil" value="${usuario.nome}"
                style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 15px; box-sizing: border-box;">

            <button id="btn-salvar-perfil" type="button"
                style="background-color: var(--blue-escuro); color: #fff; border: none; border-radius: 10px; padding: 10px 20px; cursor: pointer; width: 100%;">
                Salvar alterações
            </button>

            <p id="msg-perfil" style="margin-top: 12px; font-size: 13px;"></p>
        </div>
    `;

    document.getElementById('btn-salvar-perfil').addEventListener('click', salvarNomePerfil);
}

async function salvarNomePerfil() {
    const usuario = getUsuarioLogado();
    const input = document.getElementById('input-nome-perfil');
    const msg = document.getElementById('msg-perfil');
    const novoNome = input.value.trim();

    if (!novoNome) {
        msg.textContent = 'O nome não pode ficar vazio.';
        msg.style.color = 'red';
        return;
    }

    try {
        const resposta = await fetch('/api/usuarios/atualizar-nome', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gmail: usuario.email, nome: novoNome })
        });

        if (!resposta.ok) throw new Error('Falha ao salvar');

        // Atualiza o usuário salvo localmente, pra refletir o novo nome no menu de perfil também
        usuario.nome = novoNome;
        localStorage.setItem('usuario', JSON.stringify(usuario));

        msg.textContent = 'Nome atualizado com sucesso!';
        msg.style.color = 'green';

        // Atualiza o menu de perfil no header, se a função existir
        if (typeof montarMenuPerfil === 'function') {
            montarMenuPerfil(usuario);
        }
    } catch (erro) {
        console.error('Erro ao salvar nome:', erro);
        msg.textContent = 'Não foi possível salvar agora. Tente de novo.';
        msg.style.color = 'red';
    }
}