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

            
            window.location.href = '../../../index.html';
            return true;
        } else {
            // Se o back-end avisou que a conta é do Google (sem senha), mostra essa mensagem específica
            window.alert(dados_DaResposta.erro || 'Erro de login, tente novamente');
            return false;
        }

    } catch (erro) {
        // Captura erros de rede (como o ngrok estar offline)
        console.error("Erro na comunicação com a API:", erro);
        window.alert('Não foi possível conectar ao servidor. Verifique sua conexão.');
        return false;
    }
}