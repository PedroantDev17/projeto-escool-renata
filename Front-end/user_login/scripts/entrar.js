async function handleGoogleLogin(response) {
    console.log('1. Google chamou a função');
    try {
        const resposta = await fetch('/api/login-google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: response.credential })
        });
        console.log('2. status:', resposta.status);

        if (!resposta.ok) {
        const dados = await resposta.json().catch(() => ({}));
        window.alert(dados.erro || 'Não foi possível fazer login com o Google. Tente novamente.');
        return;
        }

        const usuario = await resposta.json();
        console.log('3. usuário recebido:', usuario);

        localStorage.setItem('usuario', JSON.stringify(usuario));
        console.log('4. salvo, redirecionando...');

        window.location.href = '../../../index.html';
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


// Adicionamos 'async' antes da função para permitir o uso de 'await'
async function entrar(event) {
  
    event.preventDefault();
    
    // Captura o texto digitado e remove espaços inúteis nas pontas
    let email = document.getElementById('iemail').value.trim();
    let senha = document.getElementById('isenha').value.trim();

    // 1. ANTISCRIPT: Remove qualquer caractere < ou > para impedir códigos HTML/Script
    const contemScript = /[<>]/;
    // Removemos o hífen (-) para não quebrar e-mails válidos
    const injeçãoCaracteres = /[=()]/; 

    if (contemScript.test(email) || injeçãoCaracteres.test(email) || contemScript.test(senha) || injeçãoCaracteres.test(senha)) {
        window.alert('Cadastro incorreto! Caracteres inválidos detectados.');
        window.location.href = '../../video_presente/presente.html';
        return false;
    }

    // 2. Validação de campos vazios
    if (email === "" || senha === "") {
        window.alert('Cadastro incorreto! Preencha todos os campos.');
        return false;
    }

    // 4. Validação do Email (Obrigatório ter o caractere @)
    if (!email.includes('@')) {
        window.alert('Cadastro incorreto! Digite um e-mail válido com @.');
        return false;
    }

    // 5. Validação da Senha (Mínimo 6 caracteres: letras, números e especiais)
    const senhaValida = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{6,}$/.test(senha);

    if (!senhaValida) {
        window.alert('Cadastro incorreto! A senha deve ter pelo menos 6 caracteres e misturar letras, números e caracteres especiais (ex: 2026@teste).');
        return false;
    } 

    // Se o código chegou até aqui, os dados são válidos. Iniciamos o envio:
    try {
        // CORREÇÃO: Aguarda o envio do fetch terminar para não cancelar a requisição
        const resposta = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Corrigido o 'C' maiúsculo de Content-Type
                'ngrok-skip-browser-warning': 'true'
            },
            body: JSON.stringify({
                'email': email,
                'senha': senha
            })
        });

        const dados_DaResposta = await resposta.json();

        if (dados_DaResposta.autenticado === true) {
            // Só redireciona se o servidor aceitou os dados (Status 200-299)
          
            console.log("Resposta da API:",dados_DaResposta);
            window.alert(`Bem-vindo, ${dados_DaResposta.usuario || 'Login realizado com sucesso!'}`);

            // Salva o usuário logado, igual o login do Google já faz —
            // sem isso, o menu do header não sabe que alguém está logado
            localStorage.setItem('usuario', JSON.stringify({
                nome: dados_DaResposta.nome,
                email: dados_DaResposta.email,
                // conta criada por senha pode não ter foto do Google —
                // usa um avatar genérico nesse caso
                foto: dados_DaResposta.foto || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(dados_DaResposta.nome || 'U'),
                token: dados_DaResposta.token
            }));

            window.location.href = '../../../index.html';
            return true;
         }        // Conta bloqueada: mostra a contagem regressiva na tela, sem alert
        if (resposta.status === 429) {
            const botao = event.target.querySelector('[type="submit"], button');
            iniciarContagem(dados_DaResposta.segundos_restantes, botao);
            return false;
        } else {
            // Bloqueio (429) ou conta Google (400): a API manda a mensagem pronta.
            // Senha ou e-mail errado: a API não manda 'erro', então usamos o texto padrão.
            window.alert(dados_DaResposta.erro || 'E-mail ou senha incorretos.');
            return false;
        }

    } catch (erro) {
        // Captura erros de rede (como o ngrok estar offline)
        console.error("Erro na comunicação com a API:", erro);
        window.alert('Não foi possível conectar ao servidor. Verifique sua conexão.');
        return false;
    }
}