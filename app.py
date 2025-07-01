from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__) 

# Configuração da SECRET_KEY (essencial para sessões e mensagens flash)
# EM PRODUÇÃO, NUNCA DEIXE UMA CHAVE ASSIM. GERE UMA CHAVE SEGURA E LONGA!
# Exemplo de como gerar uma chave segura (execute no Python Shell):
# import os
# os.urandom(24)
app.secret_key = 'be6b8535e881eb6974fa7d60ff055c96ccf65f451edabd83' 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # **Lógica de Autenticação Simplificada (APENAS PARA TESTE)**
        # Em um sistema real, você faria:
        # 1. Consultar o banco de dados para encontrar o usuário pelo email.
        # 2. Verificar se a senha fornecida corresponde à senha (hashed) armazenada no DB.
        if email == 'teste@exemplo.com' and password == '12345':
            session['logged_in'] = True  # Marca o usuário como logado na sessão
            session['email'] = email     # Armazena o email na sessão
            flash('Login bem-sucedido!', 'success') # Mensagem de sucesso para o usuário
            return redirect(url_for('index')) # Redireciona para a página inicial
        else:
            flash('Email ou senha inválidos.', 'error') # Mensagem de erro
            return render_template('login.html') # Mantém na página de login para tentar novamente

    # Se a requisição for GET (acesso inicial à página), simplesmente renderiza o formulário de login
    return render_template('login.html')

# Rota para a página de cadastro
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # **Lógica de Cadastro Simplificada (APENAS PARA TESTE)**
        # Em um sistema real, você faria:
        # 1. Validar os dados de entrada (formato do email, complexidade da senha).
        # 2. Verificar se o e-mail já existe no banco de dados para evitar duplicidade.
        # 3. Fazer HASH da senha (MUITO IMPORTANTE para segurança!) antes de armazenar.
        # 4. Salvar o novo usuário no banco de dados.

        if password != confirm_password:
            flash('As senhas não coincidem!', 'error')
            return render_template('cadastro.html')
        
        # Simulação de sucesso de cadastro
        flash(f'Olá, {name}! Seu cadastro foi simulado com sucesso. Use teste@exemplo.com e 12345 para login temporário.', 'success')
        return redirect(url_for('login')) # Redireciona para a página de login após o cadastro
        
    return render_template('cadastro.html')

# Rota para a página de Estoque de Veículos
@app.route('/estoque')
def estoque():
    # Aqui, futuramente, você buscará os dados dos veículos do banco de dados
    # e passará para o template. Ex: return render_template('estoque.html', veiculos=lista_de_veiculos)
    return render_template('estoque.html') 

# Rota para a página de Serviços
@app.route('/servicos')
def servicos():
    return render_template('servicos.html') 

# Rota para a página de Contato
@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        # **Lógica de Processamento do Formulário de Contato (APENAS PARA TESTE)**
        # Em um sistema real, você faria:
        # 1. Validar os dados do formulário.
        # 2. Salvar a mensagem no banco de dados.
        # 3. Opcionalmente, enviar um e-mail para a concessionária com a mensagem.
        print(f"Nova mensagem de contato de {name} ({email}) - Assunto: {subject}\nMensagem: {message}")
        flash('Sua mensagem foi enviada com sucesso! Em breve entraremos em contato.', 'success')
        return redirect(url_for('contato'))
    return render_template('contato.html') 

# Rota de Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Remove a variável que indica que o usuário está logado
    session.pop('email', None)     # Remove o email da sessão
    flash('Você foi desconectado.', 'info') # Mensagem informativa
    return redirect(url_for('index'))


# Bloco para rodar a aplicação
if __name__ == '__main__':
    # app.run(debug=True) ativa o modo de depuração:
    # - Servidor recarrega automaticamente ao detectar mudanças no código.
    # - Exibe informações de depuração no navegador em caso de erro.
    # DESATIVE debug=True EM AMBIENTES DE PRODUÇÃO POR SEGURANÇA!
    app.run(debug=True)