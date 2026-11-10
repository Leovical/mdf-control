from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from database.db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = 'chave_secreta_mdf_control_dev'

init_db()

@app.route('/')
def index():
    return redirect(url_for('gerenciar_produtos'))

@app.route('/produtos', methods=['GET', 'POST'])
def gerenciar_produtos():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        codigo_sku = request.form['codigo_sku'].strip().upper()
        nome = request.form['nome'].strip()
        categoria = request.form['categoria']
        espessura_mm = int(request.form['espessura_mm'])
        largura_mm = int(request.form['largura_mm'])
        comprimento_mm = int(request.form['comprimento_mm'])
        acabamento = request.form['acabamento'].strip()
        estoque_minimo = int(request.form['estoque_minimo'])
        preco_custo = float(request.form['preco_custo'])
        localizacao = request.form['localizacao'].strip()

        try:
            cursor.execute(
                '''INSERT INTO produtos (codigo_sku, nome, categoria, espessura_mm, largura_mm, comprimento_mm, acabamento, estoque_minimo, preco_custo, localizacao) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (codigo_sku, nome, categoria, espessura_mm, largura_mm, comprimento_mm, acabamento, estoque_minimo, preco_custo, localizacao)
            )
        
            conn.commit()
            flash(f'Produto {codigo_sku} cadastrado com sucesso!', 'success')
        except sqlite3.IntegrityError:
            flash(f'Erro: Já existe um produto com o código SKU {codigo_sku}!', 'danger')
        finally:
            conn.close()

        return redirect(url_for('gerenciar_produtos'))

    cursor.execute('SELECT * FROM produtos ORDER BY nome ASC')
    
    produtos = cursor.fetchall()
    conn.close()

    return render_template('produtos.html', produtos=produtos)

@app.route('/fornecedores', methods=['GET', 'POST'])
def gerenciar_fornecedores():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        razao_social = request.form['razao_social'].strip()
        cnpj = request.form['cnpj'].strip()
        telefone = request.form['telefone'].strip()
        email = request.form['email'].strip().lower()

        cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
        tel_numeros = ''.join(filter(str.isdigit, telefone))

        if len(cnpj_numeros) != 14:
            flash('Erro: O CNPJ deve conter exatamente 14 dígitos numéricos!', 'danger')
            conn.close()
            return redirect(url_for('gerenciar_fornecedores'))

        if len(tel_numeros) not in [10, 11]: # 10 (Fixo com DDD) ou 11 (Celular com DDD)
            flash('Erro: O Telefone deve conter DDD + número (10 ou 11 dígitos)!', 'danger')
            conn.close()
            return redirect(url_for('gerenciar_fornecedores'))

        if '@' not in email or '.' not in email:
            flash('Erro: Informe um endereço de e-mail válido!', 'danger')
            conn.close()
            return redirect(url_for('gerenciar_fornecedores'))

        try:
            cursor.execute(
                'INSERT INTO fornecedores (razao_social, cnpj, telefone, email) VALUES (?, ?, ?, ?)',
                (razao_social, cnpj, telefone, email)
            )

            conn.commit()
            flash(f'Fornecedor {razao_social} cadastrado com sucesso!', 'success')
        except sqlite3.IntegrityError:
            flash(f'Erro: Já existe um fornecedor cadastrado com o CNPJ {cnpj}!', 'danger')
        finally:
            conn.close()

        return redirect(url_for('gerenciar_fornecedores'))

    cursor.execute(
        '''SELECT
            f.id,
            f.razao_social,
            f.cnpj,
            f.telefone,
            f.email,
            f.data_cadastro,
            COUNT(m.id) AS total_entregas,
            COALESCE(SUM(m.quantidade), 0) AS total_itens_fornecidos
           FROM fornecedores f
           LEFT JOIN movimentacoes m ON f.id = m.fornecedor_id AND m.tipo_movimentacao = 'ENTRADA' 
           GROUP BY f.id
           ORDER BY f.razao_social ASC'''
    )

    fornecedores = cursor.fetchall()
    conn.close()

    return render_template('fornecedores.html', fornecedores=fornecedores)

@app.route('/movimentacoes', methods=['GET', 'POST'])
def gerenciar_movimentacoes():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        produto_id = int(request.form['produto_id'])
        tipo_movimentacao = request.form['tipo_movimentacao']
        quantidade = int(request.form['quantidade'])
        motivo = request.form['motivo'].strip()
        
        # usuário seleciona um fornecedor no formulário = int; se deixou em branco, vira none (null no banco)
        fornecedor_id_raw = request.form.get('fornecedor_id')
        fornecedor_id = int(fornecedor_id_raw) if fornecedor_id_raw else None
        
        # usuário padrão logado (analista/operador id = 1)
        usuario_id = 1

        if quantidade <= 0:
            flash('Erro: A quantidade movimentada deve ser maior que zero!', 'danger')
            conn.close()
            return redirect(url_for('gerenciar_movimentacoes'))

        if tipo_movimentacao == 'ENTRADA' and not fornecedor_id:
            flash('Erro: Para registrar uma ENTRADA, selecione o Fornecedor!', 'danger')
            conn.close()
            return redirect(url_for('gerenciar_movimentacoes'))

        cursor.execute('SELECT nome, codigo_sku, estoque_atual FROM produtos WHERE id = ?', (produto_id,))
        produto = cursor.fetchone()
        saldo_atual = produto['estoque_atual']

        # validação do saldo disponível
        if tipo_movimentacao == 'ENTRADA':
            novo_saldo = saldo_atual + quantidade
        elif tipo_movimentacao in ['SAIDA', 'AJUSTE']:
            if quantidade > saldo_atual:
                flash(f'Operação Bloqueada: Estoque insuficiente para {produto["codigo_sku"]}! Saldo disponível: {saldo_atual} un.', 'danger')
                conn.close()
                return redirect(url_for('gerenciar_movimentacoes'))
            else:
                novo_saldo = saldo_atual - quantidade
                fornecedor_id = None

        # acid - atomicidade: tudo ou nada
        try:
            cursor.execute(
                '''INSERT INTO movimentacoes 
                   (produto_id, usuario_id, fornecedor_id, tipo_movimentacao, quantidade, motivo) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (produto_id, usuario_id, fornecedor_id, tipo_movimentacao, quantidade, motivo)
            )

            cursor.execute(
                'UPDATE produtos SET estoque_atual = ? WHERE id = ?',
                (novo_saldo, produto_id)
            )

            # confirma as duas operações juntas no banco de dados
            conn.commit()
            flash(f'Movimentação ({tipo_movimentacao}) de {quantidade} un. do produto {produto["codigo_sku"]} registrada! Novo saldo: {novo_saldo} un.', 'success')
        except Exception as e:
            # desfaz qualquer alteração parcial caso ocorra falha
            conn.rollback()
            flash(f'Erro crítico na transação de estoque (Rollback executado): {str(e)}', 'danger')
        finally:
            conn.close()

        return redirect(url_for('gerenciar_movimentacoes'))

    # método get: busca produtos e fornecedores para preencher os <select> do formulário
    cursor.execute('SELECT id, codigo_sku, nome, estoque_atual FROM produtos ORDER BY nome ASC')
    produtos = cursor.fetchall()

    cursor.execute('SELECT id, razao_social FROM fornecedores ORDER BY razao_social ASC')
    fornecedores = cursor.fetchall()

    # busca o histórico de movimentações cruzando 4 tabelas
    cursor.execute(
        '''SELECT 
            m.id,
            m.tipo_movimentacao,
            m.quantidade,
            m.motivo,
            strftime('%d/%m/%Y %H:%M:%S', m.data_movimentacao, 'localtime') AS data_movimentacao,
            p.codigo_sku,
            p.nome AS produto_nome,
            u.nome AS usuario_nome,
            f.razao_social AS fornecedor_nome
           FROM movimentacoes m
           INNER JOIN produtos p ON m.produto_id = p.id
           INNER JOIN usuarios u ON m.usuario_id = u.id
           LEFT JOIN fornecedores f ON m.fornecedor_id = f.id
           ORDER BY m.data_movimentacao DESC, m.id DESC'''
    )
    movimentacoes = cursor.fetchall()
    conn.close()

    return render_template(
        'movimentacoes.html',
        produtos=produtos,
        fornecedores=fornecedores,
        movimentacoes=movimentacoes
    )

@app.route('/relatorios')
def relatorios_gerenciais():
    conn = get_db_connection()
    cursor = conn.cursor()

    # kpis gerais 
    cursor.execute(
        '''SELECT 
            COUNT(id) AS total_skus,
            COALESCE(SUM(estoque_atual), 0) AS total_pecas,
            COALESCE(SUM(estoque_atual * preco_custo), 0.0) AS valor_total_estoque,
            SUM(CASE WHEN estoque_atual < estoque_minimo THEN 1 ELSE 0 END) AS total_alertas
           FROM produtos'''
    )
    kpis = cursor.fetchone()

    # produtos abaixo do estoque mínimo
    cursor.execute(
        '''SELECT 
            p.codigo_sku,
            p.nome,
            p.categoria, 
            p.localizacao,
            p.estoque_atual,
            p.estoque_minimo,
            (p.estoque_minimo - p.estoque_atual) AS deficit_reposicao,
            ((p.estoque_minimo - p.estoque_atual) * p.preco_custo) AS custo_estimado_reposicao
           FROM produtos p
           WHERE p.estoque_atual < p.estoque_minimo
           ORDER BY deficit_reposicao DESC'''
    )
    produtos_criticos = cursor.fetchall()

    # ranking de produtos com maior movimentação / giro 
    cursor.execute(
        '''SELECT 
            p.codigo_sku,
            p.nome,
            p.categoria,
            COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'ENTRADA' THEN m.quantidade ELSE 0 END), 0) AS total_entradas,
            COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'SAIDA' THEN m.quantidade ELSE 0 END), 0) AS total_saidas,
            COALESCE(SUM(CASE WHEN m.tipo_movimentacao = 'AJUSTE' THEN m.quantidade ELSE 0 END), 0) AS total_ajustes,
            COALESCE(SUM(m.quantidade), 0) AS volume_total_movimentado
           FROM produtos p
           LEFT JOIN movimentacoes m ON p.id = m.produto_id
           GROUP BY p.id
           ORDER BY volume_total_movimentado DESC'''
    )
    ranking_giro = cursor.fetchall()

    # balanço por tipo de movimentação (entradas vs saídas vs ajustes)
    cursor.execute(
        '''SELECT 
            m.tipo_movimentacao,
            COUNT(m.id) AS total_operacoes,
            SUM(m.quantidade) AS volume_total
           FROM movimentacoes m
           GROUP BY m.tipo_movimentacao'''
    )
    resumo_movimentacoes = cursor.fetchall()

    # valor financeiro por produto em estoque (usando a view)
    cursor.execute('SELECT * FROM vw_posicao_estoque ORDER BY valor_total_estoque DESC')
    estoque_valorizado = cursor.fetchall()

    conn.close()

    return render_template(
        'relatorios.html',
        kpis=kpis,
        produtos_criticos=produtos_criticos,
        ranking_giro=ranking_giro,
        resumo_movimentacoes=resumo_movimentacoes,
        estoque_valorizado=estoque_valorizado
    )

if __name__ == '__main__':
    app.run(debug=True)