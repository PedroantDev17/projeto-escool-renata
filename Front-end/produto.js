// 1. Criamos a função das categorias totalmente isolada
function criarSecaoCategorias() {
    // Limpa o container de categorias antes de criar para não duplicar se pesquisar de novo
    const containerCategorias = document.getElementById('icategorias');
    containerCategorias.innerHTML = '';

    const text = document.createElement('section');
    text.classList.add('text-final');
    
    text.innerHTML = `
        <h2>Melhores resultados encontrados</h2>
        <p>Confira os modelos disponíveis nas lojas encontradas!</p>
    `;
    
    containerCategorias.appendChild(text);
}
 
          


async function Produto_cliente() {
    const produto = document.getElementById('Produtos');
    

    const valor = produto.value;


    const dadosParaEnviar = {
        nomeProduto: valor
    };

    try {
        const resposta = await fetch(' https://commute-doormat-operator.ngrok-free.dev/produtos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json' // C maiúsculo corrigido
            },
            body: JSON.stringify(dadosParaEnviar)
        });

        if (resposta.ok) {

            document.getElementById('container-produtos').innerHTML='';

            const dadosRetornados = await resposta.json();
            console.log('Sucesso:', dadosRetornados);

            

            const listaProdutos = typeof dadosRetornados === 'string' ? JSON.parse(dadosRetornados) : dadosRetornados;



            listaProdutos.forEach(lista => {
                // Colocando nas Variaveis

                 const divProduto = document.createElement('div');
                 
                // Se você tiver uma lista global acumulando os produtos, zere ela:
                
               
                divProduto.classList.add('card-produto');
                
                // Classe CSS para estilizar depois

                // const posicao = dadosRetornados.posicao;
                // const iconLoja = dadosRetornados.Icon_loja;
                // const title = dadosRetornados.title;
                // const preco = dadosRetornados.preco;
                // const loja = dadosRetornados.loja;
                // const link = dadosRetornados.link;


                const imagens = lista.imagem;
                const iconImagem = lista.Icon_loja;
                const nomeLoja = lista.loja;
                const titulo = lista.title;
                const preco = lista.preco;
                const linkProduto = lista.link;


               

                 divProduto.innerHTML = `
                 
                    <img src="${imagens}" alt="${titulo}" class="produto-img">
                    <div class="produto-info">
                        <div class="marca-container">
                            <img src="${iconImagem}" alt="Logo" ${nomeLoja} class="loja-logo">
                            <span class="produto-loja">${nomeLoja}</span>
                        </div>
                        <h3 class="produto-titulo">${titulo}</h3>
                        <p class="produto-preco">R$ ${preco}</p>
                        <a href="${linkProduto}" target="_blank" class="produto-link">Ver na Loja</a>
                    </div>
                `;
               
                 document.getElementById('container-produtos').appendChild(divProduto);
                
            });

            criarSecaoCategorias();
        } // <- Fecha o if (resposta.ok)

    } catch (erro) { // <- O catch agora está conectado corretamente ao try
        console.error('Erro na conexão ao buscar API:', erro);
    }
} // <- Fecha a função Produto_cliente


function create_cont(){
        window.location.href = '../Front-end/user_login/create_user.html'
}


function entrar(){
    window.location.href = '../Front-end/user_login/entrar.html'
}
