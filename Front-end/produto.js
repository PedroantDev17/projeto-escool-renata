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

            const listaDeProdutos = [dadosRetornados];

            listaDeProdutos.forEach(produto => {
                // Colocando nas Variaveis

                 const divProduto = document.createElement('div');
                divProduto.classList.add('card-produto'); // Classe CSS para estilizar depois

                // const posicao = dadosRetornados.posicao;
                // const iconLoja = dadosRetornados.Icon_loja;
                // const title = dadosRetornados.title;
                // const preco = dadosRetornados.preco;
                // const loja = dadosRetornados.loja;
                // const link = dadosRetornados.link;

                const imagem = produto.icon_loja; 
                const nomeLoja = produto.loja_name;
                const titulo = produto.titulo;
                const preco = produto.preco;
                const linkProduto = produto.link;

                 divProduto.innerHTML = `
                    <img src="${imagem}" alt="${titulo}" class="produto-img">
                    <div class="produto-info">
                        <span class="produto-loja">${nomeLoja}</span>
                        <h3 class="produto-titulo">${titulo}</h3>
                        <p class="produto-preco">R$ ${preco}</p>
                        <a href="${linkProduto}" target="_blank" class="produto-link">Ver na Loja</a>
                    </div>
                `;

                 document.getElementById('container-produtos').appendChild(divProduto);
            });
        } // <- Fecha o if (resposta.ok)

    } catch (erro) { // <- O catch agora está conectado corretamente ao try
        console.error('Erro na conexão ao buscar API:', erro);
    }
} // <- Fecha a função Produto_cliente

