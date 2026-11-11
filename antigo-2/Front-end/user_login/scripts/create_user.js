// ===== PÁGINA DE CRIAR CONTA =====

async function handleGoogleLogin(response) {
    try {
        const resposta = await fetch('/api/login-google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // criar: true -> aqui (e só aqui) o servidor pode criar a conta se ela não existir
            body: JSON.stringify({ token: response.credential, criar: true })
        });

        if (!resposta.ok) {
            const dados = await resposta.json().catch(() => ({}));
            window.alert(dados.erro || 'Não foi possível fazer login com o Google. Tente novamente.');
            return;
        }

        const usuario = await resposta.json();
        localStorage.setItem('usuario', JSON.stringify(usuario));

        window.location.href = '../index.html';
    } catch (erro) {
        console.error('Erro no login com Google:', erro);
        window.alert('Não foi possível conectar ao servidor. Verifique sua conexão.');
    }
}


async function create_dados(event) {
    event.preventDefault();

    // Nome e e-mail perdem espaços das pontas; a senha NÃO (espaço pode fazer parte dela)
    const nome = document.getElementById('inome').value.trim();
    const email = document.getElementById('iemail').value.trim();
    const senha = document.getElementById('isenha').value;

    // 1. ANTISCRIPT: quem tenta colocar <script> ou HTML ganha um presente 😄
    // (A proteção de verdade é feita no servidor e ao exibir os dados na tela.)
    if (/[<>]/.test(nome) || /[<>]/.test(email)) {
        window.alert('Cadastro incorreto! Caracteres inválidos detectados.');
        window.location.href = 'video_presente/presente.html';
        return false;
    }

    // 2. Campos vazios
    if (nome === '' || email === '' || senha === '') {
        window.alert('Cadastro incorreto! Preencha todos os campos.');
        return false;
    }

    // 3. Nome: sem números e até 50 caracteres
    if (/\d/.test(nome)) {
        window.alert('Cadastro incorreto! O nome não pode conter números.');
        return false;
    }
    if (nome.length > 50) {
        window.alert('Cadastro incorreto! O nome pode ter no máximo 50 caracteres.');
        return false;
    }

    // 4. E-mail precisa ter @
    if (!email.includes('@')) {
        window.alert('Cadastro incorreto! Digite um e-mail válido com @.');
        return false;
    }

    // 5. Senha: mínimo 6 caracteres, misturando letra, número e especial
    // (o servidor confere de novo — esta checagem é só para responder rápido)
    if (!/^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{6,}$/.test(senha)) {
        window.alert('Cadastro incorreto! A senha deve ter pelo menos 6 caracteres e misturar letras, números e caracteres especiais (ex: 1234@teste).');
        return false;
    }

    try {
        const resposta = await fetch('/api/usuarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: nome, email: email, senha: senha })
        });

        const dados = await resposta.json().catch(() => ({}));

        if (!resposta.ok) {
            // ex: e-mail já cadastrado (409) — mostra a mensagem que o back-end mandou
            window.alert(dados.erro || 'Não foi possível criar sua conta. Tente novamente.');
            return false;
        }

        // Cadastro deu certo: já loga a pessoa automaticamente.
        // O token é obrigatório: sem ele favoritos, perfil e configurações dão "Login necessário".
        localStorage.setItem('usuario', JSON.stringify({
            nome: dados.nome,
            email: dados.email,
            foto: '',
            token: dados.token
        }));

        window.location.href = '../index.html';
        return true;

    } catch (erro) {
        console.error('Erro na comunicação com a API:', erro);
        window.alert('Não foi possível conectar ao servidor. Verifique sua conexão.');
        return false;
    }
}
