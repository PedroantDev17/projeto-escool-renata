# Comparaí

Site que compara preços de produtos em várias lojas. Projeto escolar.

**Site:** https://comparaiweb.vercel.app

## O que o site faz
- Busca um produto e mostra preço, loja, avaliação e link de cada resultado (Google Shopping, via SerpAPI)
- Cadastro e login com e-mail/senha ou com a conta Google
- Favoritos, perfil (trocar nome) e configurações (excluir conta)
- Segurança: senha com hash, login com token (JWT), bloqueio temporário após 5 senhas erradas, banco com RLS ligado

## Como está organizado
```
index.html            página inicial
Front-end/            HTML, CSS e JavaScript (sem framework)
  utils.js            funções compartilhadas (escape de HTML, cards de produto)
  user_login/         scripts de login e cadastro
Back-end/APIs/APIs.py API em Flask (Python)
Back-end/schema.sql   estrutura do banco
vercel.json           diz à Vercel o que é site e o que é API
```

## Tecnologias
HTML, CSS e JavaScript · Python + Flask · Postgres (Supabase) · SerpAPI · Google Identity Services · Vercel

## Variáveis de ambiente (Vercel → Settings → Environment Variables)
| Nome | Para que serve |
|---|---|
| `DATABASE_POSTGRES_URL` | conexão com o Postgres (a integração do Supabase cria sozinha) |
| `JWT_SECRET` | texto longo e aleatório que assina os tokens de login |
| `GOOGLE_CLIENT_ID` | ID do app no Google (o mesmo do `data-client_id` das páginas de login) |
| `SERPAPI_KEY` | chave da SerpAPI |
| `ALLOWED_ORIGINS` | *(opcional)* domínios extras liberados no CORS, separados por vírgula |
| `LIMITE_BUSCA_POR_MINUTO` | *(opcional)* buscas novas por IP por minuto (padrão 8) |
| `LIMITE_SERPAPI_POR_DIA` | *(opcional)* buscas novas no site todo por dia (padrão 100) |

## Publicar
```
npx vercel --prod
```
