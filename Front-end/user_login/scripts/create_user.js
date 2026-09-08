function create_dados(event) {
    event.preventDefault();
    // Captura o texto digitado e remove espaços inúteis nas pontas com o .trim()
    let nome = document.getElementById('inome').value.trim();
    let email = document.getElementById('iemail').value.trim();
    let senha = document.getElementById('isenha').value.trim();

    // 1. ANTISCRIPT: Remove qualquer caractere < ou > para impedir códigos HTML/Script
    const contemScript = /[<>]/;
    const python = /[=\-()]/;
    if (contemScript.test(nome) || python.test(nome) || contemScript.test(email) || python.test(email) || contemScript.test(senha) || python(senha)) {
        window.alert('Cadastro incorreto! Caracteres inválidos detectados.');
        window.location.href = '../video_presente/presente.html'
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

    // 5. Validação da Senha (Apenas símbolos e caracteres especiais - SEM letras e SEM números)
    // A regra abaixo diz: "Se encontrar qualquer letra (a-z, A-Z) ou número (0-9)"
    const senhaValida = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{6,}$/.test(senha);

    if (!senhaValida) { // O "!" significa: Se NÃO atender aos requisitos acima
    window.alert('Cadastro incorreto! A senha deve ter pelo menos 6 caracteres e misturar letras, números e caracteres especiais (ex: 1234@teste).');
    return false;
}else{
    window.location.href = '../../index.html'
    
    

    return true;
}

    // Se passou por todas as regras sem dar "return false"
    
}