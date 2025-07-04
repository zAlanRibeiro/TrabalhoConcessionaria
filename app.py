from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps # <-- ADICIONADO: Importação necessária para o decorator

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
    return render_template('estoque.html') 

@app.route('/servicos')
def servicos():
    return render_template('servicos.html') 

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        flash('Sua mensagem foi enviada com sucesso!', 'success')
        return redirect(url_for('contato'))
    return render_template('contato.html') 

@app.route('/pagamento')
def pagamento():
    return render_template('pagamento.html')

@app.route('/processar_pagamento', methods=['POST'])
def processar_pagamento():
    flash('Pagamento processado com sucesso!', 'success')
    return redirect(url_for('index'))

# --- Rota de Administrador ---
@app.route('/painel-admin')
@admin_required
def painel_admin():
    return render_template('painelAdmin.html')

# Bloco para rodar a aplicação
if __name__ == '__main__':
    app.run(debug=True)