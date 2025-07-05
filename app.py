from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps # <-- ADICIONADO: Importação necessária para o decorator
import re
from sqlalchemy import distinct

app = Flask(__name__) 

# Configuração da SECRET_KEY (essencial para sessões e mensagens flash)
app.secret_key = 'be6b8535e881eb6974fa7d60ff055c96ccf65f451edabd83' 

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DECORATOR DE ADMIN --- # <-- ADICIONADO: Bloco da função de segurança
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Se 'is_admin' não estiver na sessão ou for False, nega o acesso
        if not session.get('is_admin'):
            flash('Acesso negado. Você precisa ser um administrador para ver esta página.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- MODELO DO BANCO DE DADOS ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
    
class Estoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(100), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    imagem_url = db.Column(db.String(200), nullable=False)

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST']) 
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_senha(password):
            session['logged_in'] = True
            session['user_id'] = usuario.id
            session['user_name'] = usuario.nome
            session['is_admin'] = usuario.is_admin # Linha correta que já estava aqui
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['name']
        email = request.form['email']
        senha = request.form['password']
        confirm_senha = request.form['confirm_password']

        if senha != confirm_senha:
            flash('As senhas não coincidem!', 'error')
            return redirect(url_for('cadastro'))

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este e-mail já está cadastrado. Tente fazer login.', 'error')
            return redirect(url_for('cadastro'))

        novo_usuario = Usuario(nome=nome, email=email)
        novo_usuario.set_senha(senha)

        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash(f'Olá, {nome}! Cadastro realizado com sucesso. Faça o login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao realizar o cadastro: {e}', 'error')
            return redirect(url_for('cadastro'))
            
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

# --- Outras rotas do seu site ---

@app.route('/estoque')
def estoque():
    query = Estoque.query
    marca_filtro = request.args.get('marca')
    preco_min_filtro = request.args.get('preco_min', type=float)
    preco_max_filtro = request.args.get('preco_max', type=float)

    if marca_filtro:
        query = query.filter(Estoque.marca == marca_filtro)
    if preco_min_filtro is not None:
        query = query.filter(Estoque.preco >= preco_min_filtro)
    if preco_max_filtro is not None:
        query = query.filter(Estoque.preco <= preco_max_filtro)

    veiculos_filtrados = query.order_by(Estoque.ano.desc()).all()
    
    marcas_disponiveis = db.session.query(distinct(Estoque.marca)).all()

    return render_template(
        'estoque.html', 
        veiculos=veiculos_filtrados, 
        marcas=marcas_disponiveis, 
        search_params=request.args
    )

@app.route('/servicos')
def servicos():
    return render_template('servicos.html') 

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        flash('Sua mensagem foi enviada com sucesso!', 'success')
        return redirect(url_for('contato'))
    return render_template('contato.html') 

@app.route('/pagamento/<int:veiculo_id>')
@login_required
def pagamento(veiculo_id):
    veiculo = Estoque.query.get_or_404(veiculo_id)
    return render_template('pagamento.html', veiculo=veiculo)

@app.route('/processar_pagamento', methods=['POST'])
def processar_pagamento():
    # --- Pega todos os dados do formulário ---
    veiculo_id = request.form.get('veiculo_id')
    nome_cartao = request.form.get('card_holder')
    numero_cartao = request.form.get('card_number', '').replace(' ', '') # Remove espaços
    validade = request.form.get('expiry_date')
    cvv = request.form.get('cvv')
    if not nome_cartao or any(char.isdigit() for char in nome_cartao):
        flash('Nome no cartão inválido. Não são permitidos números.', 'error')
        return redirect(url_for('pagamento', veiculo_id=veiculo_id))

    if not numero_cartao.isdigit() or not (13 <= len(numero_cartao) <= 19):
        flash('Número do cartão inválido.', 'error')
        return redirect(url_for('pagamento', veiculo_id=veiculo_id))

    if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', validade):
        flash('Data de validade inválida. Use o formato MM/AA.', 'error')
        return redirect(url_for('pagamento', veiculo_id=veiculo_id))
    
    if not cvv.isdigit() or not (len(cvv) in [3, 4]):
        flash('CVV inválido. Deve conter 3 ou 4 dígitos.', 'error')
        return redirect(url_for('pagamento', veiculo_id=veiculo_id))

    flash('Pagamento processado com sucesso! (Simulação)', 'success')
    return redirect(url_for('index'))

# --- Rota de Administrador ---
@app.route('/painel-admin')
@admin_required
def painel_admin():
    # Busca todos os veículos no banco
    veiculos = Estoque.query.order_by(Estoque.id.desc()).all()
    # Envia a lista de veículos para a página
    return render_template('painelAdmin.html', veiculos=veiculos)
    return render_template('painelAdmin.html')


# Em app.py, adicione esta nova rota

@app.route('/admin/veiculos/novo', methods=['GET', 'POST'])
@admin_required
def adicionar_veiculo():
    if request.method == 'POST':
        # Pega os dados do formulário
        marca = request.form['marca']
        modelo = request.form['modelo']
        ano = request.form['ano']
        preco = request.form['preco']
        descricao = request.form['descricao']
        imagem_url = request.form['imagem_url'] # Por simplicidade, vamos pegar o caminho da imagem como texto

        # Cria um novo objeto Estoque
        novo_veiculo = Estoque(
            marca=marca, 
            modelo=modelo, 
            ano=int(ano), 
            preco=float(preco), 
            descricao=descricao,
            imagem_url=imagem_url
        )

        # Salva no banco de dados
        db.session.add(novo_veiculo)
        db.session.commit()
        
        flash('Veículo adicionado com sucesso!', 'success')
        return redirect(url_for('painel_admin'))

    # Se for um GET, apenas mostra o formulário
    return render_template('adicionar_veiculo.html')

@app.route('/admin/veiculos/deletar/<int:veiculo_id>', methods=['POST'])
@admin_required
def deletar_veiculo(veiculo_id):
    # Encontra o veículo pelo ID ou retorna um erro 404 se não existir
    veiculo_para_deletar = Estoque.query.get_or_404(veiculo_id)
    
    try:
        db.session.delete(veiculo_para_deletar)
        db.session.commit()
        flash('Veículo excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir o veículo: {e}', 'error')
        
    return redirect(url_for('painel_admin'))

@app.route('/admin/veiculos/editar/<int:veiculo_id>', methods=['GET', 'POST'])
@admin_required
def editar_veiculo(veiculo_id):
    veiculo = Estoque.query.get_or_404(veiculo_id)
    
    if request.method == 'POST':
        # Pega os dados do formulário e atualiza o objeto 'veiculo'
        veiculo.marca = request.form['marca']
        veiculo.modelo = request.form['modelo']
        veiculo.ano = int(request.form['ano'])
        veiculo.preco = float(request.form['preco'])
        veiculo.descricao = request.form['descricao']
        veiculo.imagem_url = request.form['imagem_url']
        
        db.session.commit()
        flash('Veículo atualizado com sucesso!', 'success')
        return redirect(url_for('painel_admin'))
    
    # Se for um GET, apenas mostra o formulário preenchido com os dados do veículo
    return render_template('editar_veiculo.html', veiculo=veiculo)


# Bloco para rodar a aplicação
if __name__ == '__main__':
    app.run(debug=True)