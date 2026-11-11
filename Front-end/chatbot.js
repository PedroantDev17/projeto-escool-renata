(function () {
    const botao = document.createElement('button');
    botao.className = 'chatbot-abrir';
    botao.type = 'button';
    botao.setAttribute('aria-label', 'Abrir assistente de ajuda');
    botao.setAttribute('aria-expanded', 'false');
    botao.innerHTML = '<span aria-hidden="true">✦</span><span>Ajuda</span>';

    const painel = document.createElement('section');
    painel.className = 'chatbot-painel';
    painel.setAttribute('aria-label', 'Assistente de ajuda');
    painel.hidden = true;
    painel.innerHTML = `
        <header class="chatbot-cabecalho"><div><strong>Assistente Comparaí</strong><span>Como posso ajudar?</span></div>
            <button type="button" class="chatbot-fechar" aria-label="Fechar ajuda">×</button></header>
        <div class="chatbot-mensagens" aria-live="polite">
            <p class="chatbot-mensagem chatbot-bot">Olá! Posso ajudar você a comparar preços, criar sua conta ou encontrar seus favoritos.</p>
            <div class="chatbot-sugestoes">
                <button type="button" data-pergunta="Como comparar preços?">Comparar preços</button>
                <button type="button" data-pergunta="Como criar uma conta?">Conta e acesso</button>
                <button type="button" data-pergunta="Como salvar favoritos?">Favoritos</button>
            </div>
        </div>
        <form class="chatbot-form"><label class="chatbot-sr-only" for="chatbot-pergunta">Sua dúvida</label>
            <input id="chatbot-pergunta" maxlength="300" placeholder="Digite sua dúvida..." autocomplete="off" required>
            <button type="submit" aria-label="Enviar dúvida">➤</button></form>`;

    document.body.append(botao, painel);
    const mensagens = painel.querySelector('.chatbot-mensagens');
    const respostas = [
        { termos: ['preço', 'preco', 'compar', 'produto', 'busca', 'pesquis'], texto: 'Na página inicial, digite o nome do produto e toque em “Comparar preços”. Nos resultados, use “Ordenar por preço” para ver do menor para o maior ou do maior para o menor.' },
        { termos: ['conta', 'cadastro', 'criar', 'entrar', 'login', 'senha', 'acesso'], texto: 'Use “Criar conta” para se cadastrar ou “Entrar” se já tiver uma conta. Se o acesso falhar, confira o e-mail e a senha e tente novamente.' },
        { termos: ['favorit', 'salvar', 'coração'], texto: 'Entre na sua conta e toque no coração do produto para salvá-lo. Depois, abra “Favoritos” no menu para consultar ou remover itens.' },
        { termos: ['loja', 'comprar', 'link'], texto: 'Nos resultados, toque em “Ver na Loja” para abrir a página da loja. Confira o preço e as condições diretamente com o vendedor antes de comprar.' },
        { termos: ['suporte', 'atendente', 'humano', 'contato', 'problema', 'erro'], texto: 'Este assistente responde dúvidas comuns do Comparaí. Para falar com o suporte, envie um e-mail para suporte.comparai@gmail.com.', link: 'mailto:suporte.comparai@gmail.com' }
    ];

    function responder(pergunta) {
        const texto = pergunta.trim();
        if (!texto) return;
        const usuario = document.createElement('p');
        usuario.className = 'chatbot-mensagem chatbot-usuario';
        usuario.textContent = texto;
        mensagens.append(usuario);
        const normalizada = texto.toLocaleLowerCase('pt-BR');
        const resposta = respostas.find(item => item.termos.some(termo => normalizada.includes(termo)));
        const retorno = document.createElement('p');
        retorno.className = 'chatbot-mensagem chatbot-bot';
        retorno.textContent = resposta ? resposta.texto : 'Ainda não sei responder a essa dúvida. Posso ajudar com comparação de preços, conta e favoritos. Tente perguntar sobre um desses assuntos.';
        mensagens.append(retorno);
        if (resposta && resposta.link) {
            const link = document.createElement('a');
            link.href = resposta.link;
            link.className = 'chatbot-link-suporte';
            link.textContent = 'Enviar e-mail ao suporte';
            mensagens.append(link);
        }
        mensagens.scrollTop = mensagens.scrollHeight;
    }

    botao.addEventListener('click', () => {
        painel.hidden = !painel.hidden;
        botao.setAttribute('aria-expanded', String(!painel.hidden));
        if (!painel.hidden) painel.querySelector('input').focus();
    });
    painel.querySelector('.chatbot-fechar').addEventListener('click', () => {
        painel.hidden = true;
        botao.setAttribute('aria-expanded', 'false');
        botao.focus();
    });
    painel.querySelector('.chatbot-form').addEventListener('submit', event => {
        event.preventDefault();
        const input = painel.querySelector('input');
        responder(input.value);
        input.value = '';
        input.focus();
    });
    painel.querySelectorAll('[data-pergunta]').forEach(item => item.addEventListener('click', () => responder(item.dataset.pergunta)));
})();
