// ===== PÁGINA DE LOGIN =====

async function handleGoogleLogin(response) {
    try {
        const resposta = await fetch('/api/login-google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: response.credential })
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

let intervaloContagem = null;

function iniciarContagem(segundos, botao) {
    const aviso = document.getElementById('contagem-login');
    const fim = Date.now() + segundos * 1000;

    clearInterval(intervaloContagem);
    if (botao) botao.disabled = true;

    function atualizar() {
        const restante = Math.ceil((fim - Date.now()) / 1000);

        if (restante <= 0) {
            clearInterval(intervaloContagem);
            aviso.style.display = 'none';
            if (botao) botao.disabled = false;
            return;
        }

        const min = String(Math.floor(restante / 60)).padStart(2, '0');
        const seg = String(restante % 60).padStart(2, '0');
        aviso.textContent = `Muitas tentativas. Tente novamente em ${min}:${seg}`;
        aviso.style.display = 'block';
    }

    atualizar();
    intervaloContagem = setInterval(atualizar, 1000);
}


async function entrar(event) {
    event.preventDefault();

    // Captura o que foi digitado. O e-mail perde espaços das pontas; a senha NÃO
    // (espaço pode fazer parte da senha).
    const email = document.getElementById('iemail').value.trim();
    const senha = document.getElementById('isenha').value;

    // 1. ANTISCRIPT: quem tenta colocar <script> ou HTML no e-mail ganha um presente 😄
    // (A proteção de verdade é feita no servidor e ao exibir os dados na tela;
    // isto aqui é só a brincadeira. Senhas podem ter qualquer caractere.)
    if (/[<>]/.test(email)) {
        window.alert('Login incorreto! Caracteres inválidos detectados.');
        window.location.href = 'video_presente/presente.html';
        return false;
    }

    // 2. Campos vazios
    if (email === '' || senha === '') {
        window.alert('Login incorreto! Preencha todos os campos.');
        return false;
    }

    // 3. E-mail precisa ter @
    if (!email.includes('@')) {
        window.alert('Login incorreto! Digite um e-mail válido com @.');
        return false;
    }

    // As regras de senha forte valem só no cadastro. No login quem confere é o servidor.

    const botao = document.querySelector('#container form [type="submit"]');

    try {
        const resposta = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, senha: senha })
        });

        const dados = await resposta.json().catch(() => ({}));

        if (dados.autenticado === true) {
            window.alert(`Bem-vindo, ${dados.usuario || 'login realizado com sucesso!'}`);

            // Salva o usuário logado, igual o login do Google já faz —
            // sem isso, o menu do header não sabe que alguém está logado
            localStorage.setItem('usuario', JSON.stringify({
                nome: dados.nome,
                email: dados.email,
                // conta criada por senha pode não ter foto do Google — o menu usa um avatar genérico
                foto: dados.foto || '',
                token: dados.token
            }));

            window.location.href = '../index.html';
            return true;
        }

        // Conta bloqueada: mostra a contagem regressiva na tela, sem alert
        if (resposta.status === 429 && dados.segundos_restantes) {
            iniciarContagem(dados.segundos_restantes, botao);
            return false;
        }

        // Senha/e-mail errados (401) ou outro erro: usa a mensagem que o servidor mandou
      const mensagem = document.getElementById('mensagem-erro');
if (mensagem) mensagem.textContent = dados.erro || 'E-mail ou senha incorretos.';
        return false;

    } catch (erro) {
        const mensagem = document.getElementById('mensagem-erro');
if (mensagem) mensagem.textContent = 'Não foi possível conectar ao servidor. Verifique sua conexão.';
        window.alert('Não foi possível conectar ao servidor. Verifique sua conexão.');
        return false;
    }
}
