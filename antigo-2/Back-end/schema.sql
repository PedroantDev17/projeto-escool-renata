-- ============================================================
-- Estrutura do banco do Comparaí (Postgres / Supabase)
--
-- A API (APIs.py) já cria estas tabelas sozinha quando sobe.
-- Este arquivo existe como documentação e para recriar o banco
-- do zero: cole no SQL Editor do Supabase e execute.
-- ============================================================

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario        SERIAL PRIMARY KEY,
    nome              VARCHAR(50),
    gmail             VARCHAR(250),
    senha             VARCHAR(255),        -- hash (scrypt); NULL em contas criadas só pelo Google
    foto              VARCHAR(500),
    tentativas_falhas INTEGER NOT NULL DEFAULT 0,
    bloqueado_ate     TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_usuario_gmail_unico ON usuario (gmail);

CREATE TABLE IF NOT EXISTS favorito (
    id_favorito   SERIAL PRIMARY KEY,
    gmail_usuario VARCHAR(250),
    titulo        VARCHAR(300),
    imagem        VARCHAR(500),
    preco         VARCHAR(50),
    loja          VARCHAR(100),
    link          VARCHAR(500)
);
CREATE INDEX IF NOT EXISTS idx_favorito_gmail ON favorito (gmail_usuario);

-- buscas já feitas (guardadas por algumas horas para poupar a cota da SerpAPI)
CREATE TABLE IF NOT EXISTS cache_busca (
    chave     VARCHAR(200) PRIMARY KEY,
    resultado TEXT NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- contadores do limite de buscas (por IP/minuto e total/dia)
CREATE TABLE IF NOT EXISTS limite_uso (
    chave  VARCHAR(100) NOT NULL,
    janela TIMESTAMPTZ NOT NULL,
    total  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (chave, janela)
);

-- Segurança: RLS ligado e SEM policies = a API pública do Supabase (PostgREST)
-- não enxerga nada. A API Flask continua funcionando porque conecta direto
-- no Postgres (usuário "postgres", que ignora o RLS).
ALTER TABLE usuario     ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorito    ENABLE ROW LEVEL SECURITY;
ALTER TABLE cache_busca ENABLE ROW LEVEL SECURITY;
ALTER TABLE limite_uso  ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------
-- Só para bancos ANTIGOS (criados antes das colunas novas).
-- Se o seu já está funcionando, não precisa rodar nada daqui.
-- ------------------------------------------------------------
-- ALTER TABLE usuario ADD COLUMN IF NOT EXISTS foto VARCHAR(500);
-- ALTER TABLE usuario ALTER COLUMN senha TYPE VARCHAR(255);
-- ALTER TABLE usuario ADD COLUMN IF NOT EXISTS tentativas_falhas INTEGER NOT NULL DEFAULT 0;
-- ALTER TABLE usuario ADD COLUMN IF NOT EXISTS bloqueado_ate TIMESTAMPTZ;
