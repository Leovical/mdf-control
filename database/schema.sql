PRAGMA foreign_keys = ON;

-- 1. tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cargo TEXTO NOT NULL, 
    ativo INTEGER NOT NULL DEFAULT 1 -- (1 = ativo, 0 = inativo)
);

-- 2. tabela de fornecedores 
CREATE TABLE IF NOT EXISTS fornecedores(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    razao_social TEXT NOT NULL, 
    cnpj TEXT NOT NULL UNIQUE,
    contato TEXT,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. tabela produtos 
CREATE TABLE IF NOT EXISTS produtos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_sku TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL, 
    categoria TEXT NOT NULL, 
    espessura_mm INTEGER NOT NULL,
    largura_mm INTEGER NOT NULL,
    comprimento_mm INTEGER NOT NULL,
    acabamento TEXT NOT NULL,
    estoque_atual INTEGER NOT NULL DEFAULT 0 CHECK (estoque_atual >= 0),
    estoque_minimo INTEGER NOT NULL CHECK (estoque_minimo >= 0),
    preco_custo REAL NOT NULL CHECK (preco_custo >= 0), 
    localizacao TEXT,
    ativo INTEGER NOT NULL DEFAULT 1
);

-- 4. tabela movimentações
CREATE TABLE IF NOT EXISTS movimentacoes(
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     produto_id INTEGER NOT NULL,
     usuario_id INTEGER NOT NULL,
     fornecedor_id INTEGER,
     tipo_movimentacao TEXT NOT NULL CHECK(tipo_movimentacao IN ('ENTRADA', 'SAIDA', 'AJUSTE')),
     quantidade INTEGER NOT NULL CHECK(quantidade > 0),
     motivo TEXT NOT NULL,
     data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES produtos(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
);