// async function categorias() {
//     const dadosParaEnviar = {
//         nomeProduto: valor
//     };

//     try {
//         const resposta = await fetch('https://commute-doormat-operator.ngrok-free.dev/categoria', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json' // C maiúsculo corrigido
//             },
//             body: JSON.stringify(dadosParaEnviar)
//         });

//         if (resposta.ok) {

//             document.getElementById('container-produtos')

//             const dadosRetornados = await resposta.json();
//             console.log('Sucesso:', dadosRetornados);

            

//             const listaProdutos = typeof dadosRetornados === 'string' ? JSON.parse(dadosRetornados) : dadosRetornados;



//             listaProdutos.forEach(lista => {
//                 // Colocando nas Variaveis

//                  const divProduto = document.createElement('div');
                 
//                 // Se você tiver uma lista global acumulando os produtos, zere ela:
                
               
//                 divProduto.classList.add('card-produto');
                
//                 // Classe CSS para estilizar depois

//                 // const posicao = dadosRetornados.posicao;
//                 // const iconLoja = dadosRetornados.Icon_loja;
//                 // const title = dadosRetornados.title;
//                 // const preco = dadosRetornados.preco;
//                 // const loja = dadosRetornados.loja;
//                 // const link = dadosRetornados.link;


//                 const imagens = lista.imagem;
//                 const iconImagem = lista.Icon_loja;
//                 const nomeLoja = lista.loja;
//                 const titulo = lista.title;
//                 const preco = lista.preco;
//                 const linkProduto = lista.link;
//                 const nota_produto = lista.nota;
//                 const compras_total = lista.compras


               

//                  divProduto.innerHTML = `
                 
//                     <img src="${imagens}" alt="${titulo}" class="produto-img">
//                     <div class="produto-info">
//                         <div class="marca-container">
//                             <img src="${iconImagem}" alt="Logo" ${nomeLoja} class="loja-logo">
//                             <span class="produto-loja">${nomeLoja}</span>
//                         </div>
//                         <h3 class="produto-titulo">${titulo}</h3>
//                         <p class="esrelas">Avaliação: ⭐ ${nota_produto}</p>

//                         <p class="produto-preco">R$ ${preco}</p>
//                         <a href="${linkProduto}" target="_blank" class="produto-link">Ver na Loja</a>
//                         <p class="total_de_compras">total:${compras_total}</p>
//                     </div>
//                 `;
               
//                  document.getElementById('container-produtos').appendChild(divProduto);
                
//             });

//             categorias();
//         } // <- Fecha o if (resposta.ok)

//     } catch (erro) { // <- O catch agora está conectado corretamente ao try
//         console.error('Erro na conexão ao buscar API:', erro);
//     }
// } // <- Fecha a função Produto_cliente

// Adicionamos 'termo' como argumento para a função saber o que buscar
async function categorias(termo) {
    if (!termo) {
        console.error("Nenhum termo de busca foi fornecido.");
        return;
    }

    const dadosParaEnviar = {
        nomeProduto: termo
    };

    // 1. Localiza o corpo principal do site (Tag <main>)
    const telaPrincipal = document.querySelector('main');
    
    if (!telaPrincipal) {
        // Fallback caso você tenha usado uma div com id em vez da tag main
        const fallback = document.getElementById('conteudo-principal');
        if (!fallback) {
            console.error("Não foi possível encontrar a tag <main> ou o ID 'conteudo-principal' no seu HTML.");
            return;
        }
    }

    // Alvo final será a tag main encontrada
    const alvoJanela = telaPrincipal || document.getElementById('conteudo-principal');

    // 2. APAGA a página inicial e monta o título junto com o container estilizado do seu CSS (.vitrine-produtos)
    alvoJanela.innerHTML = `
        <div class="categorias" style="width: 100%; text-align: center; margin-bottom: 20px;">
            <div class="text-final">
                <section>
                    <h2 style="margin-top: 2vh;">Resultados para: <span style="color: var(--blue-escuro);">Eletronicos</span></h2>
                </section>
            </div>
        </div>
        <div id="container-produtos" class="vitrine-produtos">
            <p style="text-align: center; width: 100%; opacity: 0.7;">Buscando produtos na API...</p>
        </div>
    `;

    try {
        // 3. Faz a requisição para a API do ngrok
        const resposta = await fetch('https://commute-doormat-operator.ngrok-free.dev/categoria', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dadosParaEnviar)
        });

        if (resposta.ok) {
            const dadosRetornados = await resposta.json();
            
            // Localiza o container de produtos injetado acima
            const containerProdutos = document.getElementById('container-produtos');
            if (!containerProdutos) return;

            // Limpa o texto de carregamento
            containerProdutos.innerHTML = ''; 

            const listaProdutos = typeof dadosRetornados === 'string' ? JSON.parse(dadosRetornados) : dadosRetornados;

            if (listaProdutos.length === 0) {
                containerProdutos.innerHTML = '<p style="text-align: center; width: 100%; opacity: 0.5;">Nenhum produto encontrado para esta categoria.</p>';
                return;
            }

            // 4. Mapeia e desenha os cards respeitando INTEGRALMENTE as classes do seu CSS
            listaProdutos.forEach(lista => {
                const divProduto = document.createElement('div');
                divProduto.classList.add('card-produto'); // Sua classe CSS da linha 212

                const imagens = lista.imagem;
                const iconImagem = lista.Icon_loja;
                const nomeLoja = lista.loja;
                const titulo = lista.title;
                const preco = lista.preco;
                const linkProduto = lista.link;
                const nota_produto = lista.nota;
                const compras_total = lista.compras;

                // Montagem da estrutura de tags idêntica à esperada pelo seu CSS
                divProduto.innerHTML = `
                    <img src="${imagens}" alt="${titulo}" class="produto-img">
                    
                    <div class="marca-container">
                        <img src="${iconImagem}" alt="${nomeLoja}" class="loja-logo">
                        <span class="produto-loja">${nomeLoja}</span>
                    </div>
                    
                    <h3 class="produto-titulo" style="font-size: 16px; margin: 8px 0; text-align: left;">${titulo}</h3>
                    
                    <p class="esrelas" style="font-size: 13px; margin-bottom: 5px; text-align: left;">⭐ ${nota_produto}</p>
                    
                    <p class="produto-preco" style="font-weight: bold; color: var(--blue-escuro); margin-bottom: 10px; text-align: left;">R$ ${preco}</p>
                    
                    <a href="${linkProduto}" target="_blank" class="produto-link" style="
                        display: block; 
                        text-align: center; 
                        background-color: var(--blue-escuro); 
                        color: white; 
                        text-decoration: none; 
                        padding: 8px; 
                        border-radius: 5px; 
                        font-size: 14px;
                        margin-top: auto;
                    ">Ver na Loja</a>
                    
                    <p class="total_de_compras" style="font-size: 11px; opacity: 0.6; text-align: center; margin-top: 5px;">Total: ${compras_total}</p>
                `;
               
                containerProdutos.appendChild(divProduto);
            });

            // Faz a tela rolar suavemente até o topo da nova listagem de produtos
            containerProdutos.scrollIntoView({ behavior: 'smooth' });

        } else {
            document.getElementById('container-produtos').innerHTML = '<p style="text-align: center; color: red;">Erro ao responder ao servidor.</p>';
        }

    } catch (erro) {
        console.error('Erro na conexão ao buscar API:', erro);
        const container = document.getElementById('container-produtos');
        if (container) {
            container.innerHTML = '<p style="text-align: center; opacity: 0.7;">Não foi possível conectar ao servidor da API.</p>';
        }
    }
}



