async function handleGoogleLogin(response) {
    try {
        const resposta = await fetch('/api/login-google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: response.credential })
        });

        if (!resposta.ok) {
            window.alert('Não foi possível fazer login com o Google. Tente novamente.');
            return;
        }

        const usuario = await resposta.json();
        localStorage.setItem('usuario', JSON.stringify(usuario));

        window.location.href = '../../../index.html';
    } catch (erro) {
        console.error('Erro no login com Google:', erro);
        window.alert('Não foi possível conectar ao servidor. Verifique sua conexão.');
    }
}


async function create_dados(event) {
    event.preventDefault();
    // Captura o texto digitado e remove espaços inúteis nas pontas com o .trim()
    let nome = document.getElementById('inome').value.trim();
    let email = document.getElementById('iemail').value.trim();
    let senha = document.getElementById('isenha').value.trim();

    // 1. ANTISCRIPT: Remove qualquer caractere < ou > para impedir códigos HTML/Script
    const contemScript = /[<>]/;
    const python = /[=\-()]/;

    if (contemScript.test(nome) || python.test(nome) || contemScript.test(email) || python.test(email) || contemScript.test(senha) || python.test(senha)) {
        window.alert('Cadastro incorreto! Caracteres inválidos detectados.');
        window.location.href = '../../video_presente/presente.html'
        return false;
    }

    // 2. Validação de campos vazios
    if (nome === "" || email === "" || senha === "") {
        window.alert('Cadastro incorreto! Preencha todos os campos.');
        return false;
    }

    // 3. Validação do Nome (Não pode ter números de 0 a 9)
    const temNumeroNoNome = /\d/.test(nome);
    if (temNumeroNoNome) {
        window.alert('Cadastro incorreto! O nome não pode conter números.');
        return false;
    }

    // 4. Validação do Email (Obrigatório ter o caractere @)
    if (!email.includes('@')) {
        window.alert('Cadastro incorreto! Digite um e-mail válido com @.');
        return false;
    }

    // 5. Validação da Senha (mínimo 6 caracteres, misturando letra, número e especial)
    const senhaValida = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{6,}$/.test(senha);

    if (!senhaValida) {
        window.alert('Cadastro incorreto! A senha deve ter pelo menos 6 caracteres e misturar letras, números e caracteres especiais (ex: 1234@teste).');
        return false;
    }

    // Só redireciona DEPOIS de confirmar que o cadastro deu certo no servidor
    try {
        const resposta = await fetch('/api/usuarios', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true'
            },
            body: JSON.stringify({
                'nome': nome,
                'email': email,
                'senha': senha
            })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            // ex: e-mail já cadastrado (409) — mostra a mensagem que o back-end mandou
            window.alert(dados.erro || 'Não foi possível criar sua conta. Tente novamente.');
            return false;
        }

        // Cadastro deu certo: já loga a pessoa automaticamente,
        // igual acontece no login pelo Google
        localStorage.setItem('usuario', JSON.stringify({
            nome: nome,
            email: email,
            foto: 'https://ui-avatars.com/api/?name=' + encodeURIComponent(nome)
        }));

        window.location.href = '../../../index.html';
        return true;

    } catch (erro) {
        console.error('Erro na comunicação com a API:', erro);
        window.alert('Não foi possível conectar ao servidor. Verifique sua conexão.');
        return false;
    }
}