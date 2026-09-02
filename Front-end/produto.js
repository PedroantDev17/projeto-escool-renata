async function Produto_cliente() {
    const produto = document.getElementById('Produtos');
    const valor = produto.value;

    const dadosParaEnviar = {
        nomeProduto: valor
    };

    try {
        const resposta = await fetch('https://commute-doormat-operator.ngrok-free.dev/produtos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json' // C maiúsculo corrigido
            },
            body: JSON.stringify(dadosParaEnviar)
        });

        if (resposta.ok) {
            const dadosRetornados = await resposta.json();
            console.log('Sucesso:', dadosRetornados);

            dadosRetornados.forEach(produto => {
                // Colocando nas Variaveis
                const posicao = dadosRetornados.posicao;
                const iconLoja = dadosRetornados.Icon_loja;
                const title = dadosRetornados.title;
                const preco = dadosRetornados.preco;
                const loja = dadosRetornados.loja;
                const link = dadosRetornados.link;
            });
        } // <- Fecha o if (resposta.ok)

    } catch (erro) { // <- O catch agora está conectado corretamente ao try
        console.error('Erro na conexão ao buscar API:', erro);
    }
} // <- Fecha a função Produto_cliente

