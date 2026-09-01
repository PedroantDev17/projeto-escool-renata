async function Produto_cliente() {
    const produto = document.getElementById('Produtos');
    const valor = produto.value;
// Dados enviados para API_produtos:
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
// Dados Retornados da API_produtos: 
        if (resposta.ok) {
            const dadosRetornados = await resposta.json();
            console.log('Sucesso:', dadosRetornados);
            // Laço for para retirar do JSON:
            dadosRetornados.forEach(produto => {
                // Colocando nas Variaveis
                const posicao = dadosRetornados.posicao;
                const iconLoja = dadosRetornados.Icon_loja;
                const title = dadosRetornados.title;
                const preco = dadosRetornados.price;
                const loja = dadosRetornados.loja_name;
                const link = dadosRetornados.link_product;
            });

        } else {
            console.log('Erro na resposta da API', resposta.status);
        } // Chave que fecha o else adicionada

    } catch (erro) { // O catch agora pega tudo o que falhar no bloco acima
        console.error('Erro de conexão ao buscar API:', erro);
    }
}
