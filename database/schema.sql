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
    telefone TEXT NULL,
    email TEXT NOT NULL,
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

-- 5. view de posição de estoque valorizada e status de alerta (relatórios e power bi)
CREATE VIEW IF NOT EXISTS vw_posicao_estoque AS
SELECT 
    id,
    codigo_sku,
    nome,
    categoria,
    espessura_mm,
    largura_mm,
    comprimento_mm,
    acabamento,
    localizacao,
    estoque_atual,
    estoque_minimo,
    preco_custo,
    ROUND(estoque_atual * preco_custo, 2) AS valor_total_estoque,
    CASE 
        WHEN estoque_atual < estoque_minimo THEN 'ABAIXO DO MINIMO'
        ELSE 'NORMAL'
    END AS status_estoque
FROM produtos;

-- 6. view kardex completo desnormalizado (auditoria e importação no power bi)
CREATE VIEW IF NOT EXISTS vw_kardex_historico AS
SELECT 
    m.id AS movimentacao_id,
    m.tipo_movimentacao,
    m.quantidade,
    m.motivo,
    m.data_movimentacao,
    p.id AS produto_id,
    p.codigo_sku,
    p.nome AS produto_nome,
    p.categoria,
    p.preco_custo,
    ROUND(m.quantidade * p.preco_custo, 2) AS valor_movimentado,
    u.nome AS usuario_responsavel,
    COALESCE(f.razao_social, 'Movimentação Interna') AS fornecedor
FROM movimentacoes m
INNER JOIN produtos p ON m.produto_id = p.id
INNER JOIN usuarios u ON m.usuario_id = u.id
LEFT JOIN fornecedores f ON m.fornecedor_id = f.id;