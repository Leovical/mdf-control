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

if __name__ == '__main__':
    app.run(debug=True)