from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash # Importa funções de segurança de senha

app = Flask(__name__) 

# Configuração da SECRET_KEY (essencial para sessões e mensagens flash)
app.secret_key = 'be6b8535e881eb6974fa7d60ff055c96ccf65f451edabd83' 

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DO BANCO DE DADOS ---
# Esta classe representa a nossa tabela 'usuario' no banco de dados.
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Chave primária, ID único para cada usuário
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False) # E-mail deve ser único
    senha_hash = db.Column(db.String(256), nullable=False) # Armazena a senha de forma segura

    # Método para definir a senha do usuário, gerando um hash seguro
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    # Método para verificar a senha fornecida pelo usuário no login
    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST']) 
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Procura o usuário no banco de dados pelo e-mail fornecido
        usuario = Usuario.query.filter_by(email=email).first()

        # Verifica se o usuário existe E se a senha está correta
        if usuario and usuario.check_senha(password):
            session['logged_in'] = True
            session['user_id'] = usuario.id
            session['user_name'] = usuario.nome
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

        # Verifica se as senhas coincidem
        if senha != confirm_senha:
            flash('As senhas não coincidem!', 'error')
            return redirect(url_for('cadastro'))

        # Verifica se o e-mail já está cadastrado
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este e-mail já está cadastrado. Tente fazer login.', 'error')
            return redirect(url_for('cadastro'))

        # Cria um novo objeto Usuario
        novo_usuario = Usuario(nome=nome, email=email)
        novo_usuario.set_senha(senha) # Define a senha de forma segura

        # Adiciona o novo usuário ao banco de dados
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
    session.clear() # Limpa toda a sessão
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

# --- Outras rotas do seu site (estoque, servicos, etc.) ---

@app.route('/estoque')
def estoque():
    return render_template('estoque.html') 

@app.route('/servicos')
def servicos():
    return render_template('servicos.html') 

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        # Lógica do formulário de contato aqui...
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

# Bloco para rodar a aplicação
if __name__ == '__main__':
    app.run(debug=True)
