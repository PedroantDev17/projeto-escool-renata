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
                // 1. Cria o container do produto
                const divProduto = document.createElement('div');
                divProduto.classList.add('card-produto'); // Classe CSS para estilizar depois

                // 2. Extrai os dados do objeto
                const imagem = produto.posicao; 
                const nomeLoja = produto.com_loja;
                const titulo = produto.title;
                const preco = produto.price;
                const linkProduto = produto.link_product;

                // 3. Insere a estrutura de HTML dentro da div do produto
                divProduto.innerHTML = `
                    <img src="${imagem}" alt="${titulo}" class="produto-img">
                    <div class="produto-info">
                        <span class="produto-loja">${nomeLoja}</span>
                        <h3 class="produto-titulo">${titulo}</h3>
                        <p class="produto-preco">R$ ${preco}</p>
                        <a href="${linkProduto}" target="_blank" class="produto-link">Ver na Loja</a>
                    </div>
                `;

                // 4. Adiciona esse novo produto ao container existente no seu HTML
                document.getElementById('container-produtos').appendChild(divProduto);
            });
        } // <- Fecha o if (resposta.ok)

    } catch (erro) { // <- O catch agora está conectado corretamente ao try
        console.error('Erro na conexão ao buscar API:', erro);
    }
} // <- Fecha a função Produto_cliente

