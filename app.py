from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
from sqlalchemy import distinct
from datetime import datetime

app = Flask(__name__) 

# Configuração da SECRET_KEY
app.secret_key = 'be6b8535e881eb6974fa7d60ff055c96ccf65f451edabd83' 

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DECORATORS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: # <-- MELHORIA: Verifica por user_id, mais específico
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        
        # <-- MELHORIA DE SEGURANÇA: Verifica se o usuário da sessão ainda existe no DB
        user = Usuario.query.get(session['user_id'])
        if user is None:
            session.clear()
            flash("Sua conta não foi encontrada. Por favor, faça login novamente.", "warning")
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Acesso negado. Você precisa ser um administrador para ver esta página.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- MODELOS DO BANCO DE DADOS ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    cpf = db.Column(db.String(20), unique=True, nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

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
    cor = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Disponível')

class TestDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_agendamento = db.Column(db.DateTime, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('estoque.id'), nullable=False)
    cliente = db.relationship('Usuario', backref=db.backref('test_drives', lazy=True))
    veiculo = db.relationship('Estoque', backref=db.backref('test_drives', lazy=True))

class Venda(db.Model): # <-- MELHORIA: Removido comentário desnecessário
    id = db.Column(db.Integer, primary_key=True)
    data_venda = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    preco_final = db.Column(db.Float, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('estoque.id'), nullable=False, unique=True)
    cliente = db.relationship('Usuario', backref='compras')
    veiculo = db.relationship('Estoque', backref='venda')

# --- ROTAS DA APLICAÇÃO ---

# ... (suas rotas de index, login, cadastro, logout, servicos, contato estão OK) ...

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
            session['is_admin'] = usuario.is_admin
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
        cpf = request.form.get('cpf')
        endereco = request.form.get('endereco')
        telefone = request.form.get('telefone')

        if senha != confirm_senha:
            flash('As senhas não coincidem!', 'error')
            return redirect(url_for('cadastro'))

        usuario_email = Usuario.query.filter_by(email=email).first()
        usuario_cpf = Usuario.query.filter_by(cpf=cpf).first()

        if usuario_email:
            flash('Este e-mail já está cadastrado. Tente fazer login.', 'error')
            return redirect(url_for('cadastro'))
        
        if usuario_cpf:
            flash('Este CPF já está cadastrado em outra conta.', 'error')
            return redirect(url_for('cadastro'))

        novo_usuario = Usuario(
            nome=nome, 
            email=email,
            cpf=cpf,
            endereco=endereco,
            telefone=telefone
        )
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

@app.route('/estoque')
def estoque():
    # COMEÇA A BUSCA JÁ FILTRANDO APENAS VEÍCULOS 'DISPONÍVEIS'
    query = Estoque.query.filter_by(status='Disponível')

    # Os outros filtros continuam funcionando normalmente sobre o resultado
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
    
    # A lógica para popular o dropdown de marcas continua a mesma
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
@login_required
def processar_pagamento():
    veiculo_id = request.form.get('veiculo_id')
    veiculo = Estoque.query.get_or_404(veiculo_id)

    if veiculo.status != 'Disponível':
        flash('Desculpe, este veículo não está mais disponível para venda.', 'error')
        return redirect(url_for('estoque'))

    nova_venda = Venda(
        preco_final=veiculo.preco,
        cliente_id=session['user_id'],
        veiculo_id=veiculo.id
    )
    veiculo.status = 'Vendido'
    try:
        db.session.add(nova_venda)
        db.session.add(veiculo) 
        db.session.commit()
        flash('Pagamento processado com sucesso! Seu contrato foi gerado.', 'success')
        return redirect(url_for('contrato', venda_id=nova_venda.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao processar a venda: {e}', 'error')
        return redirect(url_for('pagamento', veiculo_id=veiculo.id))
    
@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    # Busca o usuário logado no banco de dados
    usuario_id = session['user_id']
    usuario = Usuario.query.get_or_404(usuario_id)

    if request.method == 'POST':
        # Pega os dados do formulário
        usuario.nome = request.form['nome']
        usuario.email = request.form['email']
        usuario.cpf = request.form['cpf']
        usuario.endereco = request.form['endereco']
        usuario.telefone = request.form['telefone']

        # Validação para garantir que o novo e-mail ou CPF não pertençam a outro usuário
        email_existente = Usuario.query.filter(Usuario.email == usuario.email, Usuario.id != usuario_id).first()
        cpf_existente = Usuario.query.filter(Usuario.cpf == usuario.cpf, Usuario.id != usuario_id).first()

        if email_existente:
            flash('Este e-mail já está em uso por outra conta.', 'error')
            return redirect(url_for('perfil'))
        
        if cpf_existente:
            flash('Este CPF já está em uso por outra conta.', 'error')
            return redirect(url_for('perfil'))

        # Salva as alterações no banco
        db.session.commit()

        # Atualiza o nome do usuário na sessão, caso ele tenha mudado
        session['user_name'] = usuario.nome
        
        flash('Seu perfil foi atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))

    # Se a requisição for GET, apenas mostra a página com os dados do usuário
    return render_template('perfil.html', usuario=usuario)

# --- Rota de Administrador ---
@app.route('/painel-admin')
@admin_required
def painel_admin():
    veiculos = Estoque.query.order_by(Estoque.id.desc()).all()
    # A segunda linha era redundante e foi removida
    return render_template('painelAdmin.html', veiculos=veiculos)


@app.route('/admin/veiculos/novo', methods=['GET', 'POST'])
@admin_required
def adicionar_veiculo():
    if request.method == 'POST':
        marca = request.form['marca']
        modelo = request.form['modelo']
        cor = request.form['cor']
        ano = request.form['ano']
        preco = request.form['preco']
        descricao = request.form['descricao']
        imagem_url = request.form['imagem_url']
        novo_veiculo = Estoque(
            marca=marca, 
            modelo=modelo, 
            cor=cor,
            ano=int(ano), 
            preco=float(preco), 
            descricao=descricao,
            imagem_url=imagem_url
        )
        db.session.add(novo_veiculo)
        db.session.commit()
        flash('Veículo adicionado com sucesso!', 'success')
        return redirect(url_for('painel_admin'))
    return render_template('adicionar_veiculo.html')

@app.route('/admin/veiculos/deletar/<int:veiculo_id>', methods=['POST'])
@admin_required
def deletar_veiculo(veiculo_id):
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
        veiculo.marca = request.form['marca']
        veiculo.modelo = request.form['modelo']
        veiculo.cor = request.form['cor']
        veiculo.ano = int(request.form['ano'])
        veiculo.preco = float(request.form['preco'])
        veiculo.descricao = request.form['descricao']
        veiculo.imagem_url = request.form['imagem_url']
        db.session.commit()
        flash('Veículo atualizado com sucesso!', 'success')
        return redirect(url_for('painel_admin'))
    return render_template('editar_veiculo.html', veiculo=veiculo)

@app.route('/agendar-test-drive/<int:veiculo_id>', methods=['GET', 'POST'])
@login_required
def agendar_test_drive(veiculo_id):
    veiculo = Estoque.query.get_or_404(veiculo_id)
    if request.method == 'POST':
        data_str = request.form.get('data_agendamento')
        try:
            data_obj = datetime.strptime(data_str, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            flash('Formato de data e hora inválido.', 'error')
            return render_template('agendar_test_drive.html', veiculo=veiculo)
        
        agendamento_existente = TestDrive.query.filter_by(
            veiculo_id=veiculo.id,
            data_agendamento=data_obj
        ).first()

        if agendamento_existente:
            flash('Este horário já está reservado para este veículo. Por favor, escolha outro.', 'error')
            return redirect(url_for('agendar_test_drive', veiculo_id=veiculo.id))
        
        novo_agendamento = TestDrive(
            data_agendamento=data_obj,
            cliente_id=session['user_id'],
            veiculo_id=veiculo.id
        )
        db.session.add(novo_agendamento)
        db.session.commit()
        flash(f'Test drive para o {veiculo.marca} {veiculo.modelo} agendado com sucesso!', 'success')
        return redirect(url_for('estoque'))
    return render_template('agendar_test_drive.html', veiculo=veiculo)

@app.route('/contrato/<int:venda_id>')
@login_required
def contrato(venda_id):
    venda = Venda.query.get_or_404(venda_id)
    if venda.cliente_id != session['user_id']:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('index'))
    return render_template('contrato.html', venda=venda)

# Bloco para rodar a aplicação
if __name__ == '__main__':
    app.run(debug=True)