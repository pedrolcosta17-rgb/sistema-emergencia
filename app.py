import os
import sqlite3
import re
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ============================================================================
# IMPORTAÇÃO DE REQUESTS COM FALLBACK PARA URILIB
# ============================================================================
try:
    import requests
    REQUESTS_DISPONIVEL = True
except ImportError:
    REQUESTS_DISPONIVEL = False
    import urllib.request
    import urllib.parse
    import urllib.error
    print("⚠️ Módulo 'requests' não encontrado. Usando urllib como fallback.")
    print("💡 Para melhor performance, instale: pip install requests")

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mude_em_producao'

# ============================================================================
# CONFIGURAÇÃO CORS PARA PERMITIR REQUISIÇÕES DO FRONTEND
# ============================================================================
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ============================================================================
# CONFIGURAÇÃO DE SESSÃO PERMANENTE
# ============================================================================
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 7 * 24 * 60 * 60  # 7 dias em segundos

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ============================================================================
# DATABASE SETUP
# ============================================================================

def get_db():
    """Conecta ao banco de dados SQLite"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            telefone TEXT NOT NULL,
            data_nascimento TEXT,
            genero TEXT,
            telefone_alternativo TEXT,
            endereco TEXT,
            lgpd_consentimento INTEGER,
            is_admin INTEGER DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Verificar se a coluna is_admin existe (para bancos existentes)
    cursor.execute("PRAGMA table_info(usuarios)")
    colunas = [col[1] for col in cursor.fetchall()]
    if 'is_admin' not in colunas:
        cursor.execute('ALTER TABLE usuarios ADD COLUMN is_admin INTEGER DEFAULT 0')
    if 'endereco' not in colunas:
        cursor.execute('ALTER TABLE usuarios ADD COLUMN endereco TEXT')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS denuncias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Snapshot da ficha médica no momento do acionamento
            ficha_tipo_sanguineo TEXT,
            ficha_alergias TEXT,
            ficha_doencas TEXT,
            ficha_medicamentos TEXT,
            ficha_contato_nome TEXT,
            ficha_contato_telefone TEXT,
            ficha_atualizado_em TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # Tabela de Ficha Médica
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ficha_medica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE,
            tipo_sanguineo TEXT,
            alergias TEXT,
            doencas TEXT,
            medicamentos TEXT,
            contato_nome TEXT,
            contato_telefone TEXT,
            observacoes TEXT,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # =====================================================================
    # FUNCIONALIDADE 1: LOGIN PERSISTENTE - Tabela de tokens
    # =====================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expiracao TIMESTAMP NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')
    print('✅ Tabela tokens_login criada/verificada para login persistente')

    # Migração: Adicionar coluna foto na tabela denuncias (se não existir)
    cursor.execute("PRAGMA table_info(denuncias)")
    colunas_denuncias = [col[1] for col in cursor.fetchall()]
    if 'foto' not in colunas_denuncias:
        cursor.execute('ALTER TABLE denuncias ADD COLUMN foto TEXT')
        print('✅ Coluna foto adicionada à tabela denuncias')

    # Migração: Adicionar coluna finalizado na tabela denuncias (se não existir)
    if 'finalizado' not in colunas_denuncias:
        cursor.execute('ALTER TABLE denuncias ADD COLUMN finalizado INTEGER DEFAULT 0')
        print('✅ Coluna finalizado adicionada à tabela denuncias')

    # Migração: Adicionar colunas de geocodificação na tabela servicos (se não existirem)
    cursor.execute("PRAGMA table_info(servicos)")
    colunas_servicos = [col[1] for col in cursor.fetchall()]
    colunas_geocode = ['rua', 'bairro', 'cidade', 'estado', 'cep']
    
    for coluna in colunas_geocode:
        if coluna not in colunas_servicos:
            cursor.execute(f'ALTER TABLE servicos ADD COLUMN {coluna} TEXT')
            print(f'✅ Coluna {coluna} adicionada à tabela servicos')

    # Migração: Adicionar coluna finalizado na tabela servicos (se não existir)
    if 'finalizado' not in colunas_servicos:
        cursor.execute('ALTER TABLE servicos ADD COLUMN finalizado INTEGER DEFAULT 0')
        print('✅ Coluna finalizado adicionada à tabela servicos')

    db.commit()
    db.close()

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_address_from_coords(lat, lon):
    """
    Converte coordenadas (lat, lon) em endereço completo usando Nominatim (OpenStreetMap)
    Retorna: {'rua': str, 'bairro': str, 'cidade': str, 'estado': str, 'cep': str} ou None em caso de erro
    """
    if lat is None or lon is None:
        return None
    
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {
            'User-Agent': 'EmergenciaApp/1.0'
        }
        
        if REQUESTS_DISPONIVEL:
            # Usa requests (recomendado)
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
        else:
            # Fallback: usa urllib (biblioteca padrão)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                import json
                data = json.loads(response.read().decode('utf-8'))
        
        if data:
            address = data.get('address', {})
            
            # Extrair todos os componentes do endereço
            rua = address.get('road') or address.get('street') or address.get('pedestrian') or address.get('path')
            bairro = address.get('suburb') or address.get('neighbourhood') or address.get('district')
            cidade = address.get('city') or address.get('town') or address.get('village') or address.get('municipality')
            estado = address.get('state')
            cep = address.get('postcode')
            
            # Se não encontrou estado, tenta obter do código do país (BR)
            if not estado and address.get('country_code') == 'br':
                # Para Brasil, usa o estado como referência regional
                estado = address.get('county', '').split(' ')[-1] if address.get('county') else None
            
            # Retorna apenas se tiver pelo menos cidade ou estado
            if cidade or estado:
                return {
                    'rua': rua,
                    'bairro': bairro,
                    'cidade': cidade,
                    'estado': estado,
                    'cep': cep
                }
        return None
    except Exception as e:
        print(f"Erro na geocodificação: {e}")
        return None

def save_uploaded_file(file):
    """
    Salva o arquivo上传 e retorna o nome único gerado.
    Retorna None se não houver arquivo ou erro.
    """
    if file and file.filename:
        # Gera nome único: timestamp_uuid.extensao
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
        
        # Garante que a pasta uploads existe
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        # Salva o arquivo
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        return unique_filename
    return None

# ============================================================================
# VALIDAÇÕES
# ============================================================================

def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_cpf(cpf):
    """Valida CPF básico (apenas formato)"""
    cpf = cpf.replace('.', '').replace('-', '')
    return len(cpf) == 11 and cpf.isdigit()

def validar_telefone(telefone):
    """Valida telefone básico"""
    telefone = telefone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
    return len(telefone) >= 10 and telefone.isdigit()

# ============================================================================
# ROTAS
# ============================================================================

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard do usuário autenticado"""
    if 'user_id' not in session:
        return render_template('index.html')

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT nome FROM usuarios WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    db.close()

    return render_template('index.html', user_nome=user['nome'])

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Rota para cadastro de usuário"""
    if request.method == 'GET':
        # GET retorna a página de cadastro
        return render_template('index.html')
    
    if request.method == 'POST':
        data = request.get_json() or {}

        if not data.get('nome') or len(data['nome'].strip()) < 3:
            return jsonify({'sucesso': False, 'erro': 'Nome deve ter pelo menos 3 caracteres'}), 400

        if not validar_cpf(data.get('cpf', '')):
            return jsonify({'sucesso': False, 'erro': 'CPF inválido'}), 400

        if not data.get('data_nascimento'):
            return jsonify({'sucesso': False, 'erro': 'Data de nascimento é obrigatória'}), 400

        telefone_principal = data.get('telefone_principal') or data.get('telefone', '')
        telefone_alternativo = data.get('telefone_alternativo', '')

        if not validar_telefone(telefone_principal):
            return jsonify({'sucesso': False, 'erro': 'Telefone principal inválido'}), 400

        if telefone_alternativo and not validar_telefone(telefone_alternativo):
            return jsonify({'sucesso': False, 'erro': 'Telefone alternativo inválido'}), 400

        if not validar_email(data.get('email', '')):
            return jsonify({'sucesso': False, 'erro': 'Email inválido'}), 400

        if data.get('email') != data.get('email_confirmacao'):
            return jsonify({'sucesso': False, 'erro': 'Emails não conferem'}), 400

        if data.get('senha') != data.get('senha_confirmacao'):
            return jsonify({'sucesso': False, 'erro': 'Senhas não conferem'}), 400

        if len(data.get('senha', '')) < 6:
            return jsonify({'sucesso': False, 'erro': 'Senha deve ter pelo menos 6 caracteres'}), 400

        if not data.get('lgpd_consentimento'):
            return jsonify({'sucesso': False, 'erro': 'Consentimento LGPD é obrigatório'}), 400

        # Monta o endereço completo a partir dos campos individuais
        estado = data.get('estado', '').strip()
        municipio = data.get('municipio', '').strip()
        cep = data.get('cep', '').strip()
        rua = data.get('rua', '').strip()
        numero = data.get('numero', '').strip()
        bairro = data.get('bairro', '').strip()
        complemento = data.get('complemento', '').strip()

        # Constrói a string de endereço no formato: Rua, Número - Bairro, Município - UF, CEP: XXXXX-XXX
        partes_endereco = []
        if rua:
            partes_endereco.append(rua)
        if numero:
            partes_endereco.append(numero)
        if bairro:
            partes_endereco.append(bairro)
        if municipio:
            partes_endereco.append(municipio)
        if estado:
            partes_endereco.append(estado)
        if cep:
            partes_endereco.append(f'CEP: {cep}')

        endereco_completo = ', '.join(partes_endereco) if partes_endereco else ''

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO usuarios 
                (nome, email, senha, cpf, telefone, data_nascimento, genero, telefone_alternativo, endereco, lgpd_consentimento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['nome'].strip(),
                data['email'].strip().lower(),
                generate_password_hash(data['senha']),
                data['cpf'].replace('.', '').replace('-', ''),
                telefone_principal.strip(),
                data.get('data_nascimento', ''),
                data.get('genero', ''),
                telefone_alternativo.strip() or None,
                endereco_completo,
                1
            ))
            db.commit()
            db.close()
            return jsonify({'sucesso': True, 'mensagem': 'Cadastro realizado com sucesso! Faça login.'})
        except sqlite3.IntegrityError:
            return jsonify({'sucesso': False, 'erro': 'CPF ou Email já cadastrado'}), 400
        except Exception as e:
            return jsonify({'sucesso': False, 'erro': f'Erro ao salvar cadastro: {str(e)}'}), 500

    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuário"""
    if request.method == 'POST':
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        senha = data.get('senha', '')
        
        if not email or not senha:
            return jsonify({'sucesso': False, 'erro': 'Email e senha são obrigatórios'}), 400
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, senha, is_admin FROM usuarios WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['senha'], senha):
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin'] if 'is_admin' in user.keys() else 0
            session.permanent = True  # Mantém sessão por 7 dias
            
            # =====================================================================
            # FUNCIONALIDADE 1: GERAR TOKEN PARA LOGIN PERSISTENTE
            # =====================================================================
            token = str(uuid.uuid4())
            expiracao = datetime.now() + timedelta(days=30)  # Token válido por 30 dias
            
            # Salvar token no banco
            cursor.execute('''
                INSERT OR REPLACE INTO tokens_login (usuario_id, token, expiracao)
                VALUES (?, ?, ?)
            ''', (user['id'], token, expiracao))
            db.commit()
            db.close()
            
            return jsonify({
                'sucesso': True, 
                'mensagem': 'Login realizado com sucesso!',
                'token': token  # Retorna token para o frontend salvar no localStorage
            })
        
        db.close()
        return jsonify({'sucesso': False, 'erro': 'Email ou senha inválidos'}), 401
    
    return render_template('index.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('is_admin', None)
    session.clear()
    return redirect(url_for('index'))

# =====================================================================
# FUNCIONALIDADE 1: ROTA PARA LOGIN AUTOMÁTICO VIA TOKEN
# =====================================================================
@app.route('/auto-login', methods=['GET'])
def auto_login():
    """Verifica token enviado pelo frontend e faz login automático"""
    token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'sucesso': False, 'erro': 'Token não fornecido'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # Buscar token válido (não expirado)
    cursor.execute('''
        SELECT t.usuario_id, u.is_admin, u.nome
        FROM tokens_login t
        JOIN usuarios u ON t.usuario_id = u.id
        WHERE t.token = ? AND t.expiracao > ?
    ''', (token, datetime.now()))
    
    token_data = cursor.fetchone()
    db.close()
    
    if token_data:
        # Token válido - criar sessão
        session['user_id'] = token_data['usuario_id']
        session['is_admin'] = token_data['is_admin']
        session.permanent = True
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Login automático realizado!',
            'nome': token_data['nome'],
            'is_admin': bool(token_data['is_admin'])
        })
    else:
        return jsonify({'sucesso': False, 'erro': 'Token inválido ou expirado'}), 401

@app.route('/denuncia', methods=['POST'])
def denuncia():
    """
    Recebe e salva denúncia no banco de dados.
    Suporta texto e/ou imagem (upload).
    """
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401
    
    # Suporta tanto JSON quanto FormData
    if request.content_type and 'multipart/form-data' in request.content_type:
        # FormData com arquivo
        descricao = request.form.get('descricao', '').strip()
        foto_file = request.files.get('foto')
        
        # Valida imagem se enviada
        foto_nome = None
        if foto_file and foto_file.filename:
            if not allowed_file(foto_file.filename):
                return jsonify({'sucesso': False, 'erro': 'Tipo de arquivo não permitido. Use: jpg, jpeg, png ou gif'}), 400
            foto_nome = save_uploaded_file(foto_file)
    else:
        # JSON tradicional
        data = request.get_json() or {}
        descricao = data.get('descricao', '').strip()
        foto_nome = None
    
    # Validação: texto mínimo 10 caracteres (obrigatório)
    if not descricao or len(descricao) < 10:
        return jsonify({'sucesso': False, 'erro': 'Denúncia deve ter pelo menos 10 caracteres'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO denuncias (usuario_id, descricao, foto)
            VALUES (?, ?, ?)
        ''', (session['user_id'], descricao, foto_nome))
        db.commit()
        db.close()
        
        mensagem = 'Denúncia registrada com sucesso!'
        if foto_nome:
            mensagem += ' (com imagem)'
        
        return jsonify({'sucesso': True, 'mensagem': mensagem})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': 'Erro ao salvar denúncia'}), 500

@app.route('/servico', methods=['POST'])
def servico():
    """Aciona serviço de emergência e salva no banco de dados com snapshot da ficha médica"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    data = request.get_json() or {}
    tipo = data.get('servico', '').strip()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    servicos_validos = ['Polícia', 'SAMU', 'Bombeiros', 'Defesa Civil']
    if tipo not in servicos_validos:
        return jsonify({'sucesso': False, 'erro': 'Serviço inválido'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        
        # =====================================================================
        # GEOCODIFICAÇÃO REVERSA - Converter lat/long em endereço completo
        # =====================================================================
        rua = None
        bairro = None
        cidade = None
        estado = None
        cep = None
        if latitude and longitude:
            endereco = get_address_from_coords(latitude, longitude)
            if endereco:
                rua = endereco.get('rua')
                bairro = endereco.get('bairro')
                cidade = endereco.get('cidade')
                estado = endereco.get('estado')
                cep = endereco.get('cep')
        
        # =====================================================================
        # SNAPSHOT DA FICHA MÉDICA NO MOMENTO DO ACIONAMENTO
        # =====================================================================
        # Buscar ficha médica do usuário para criar snapshot
        cursor.execute('''
            SELECT tipo_sanguineo, alergias, doencas, medicamentos, 
                   contato_nome, contato_telefone, atualizado_em
            FROM ficha_medica 
            WHERE usuario_id = ?
        ''', (session['user_id'],))
        ficha = cursor.fetchone()
        
        # Preparar valores do snapshot (None se não existir ficha)
        if ficha:
            ficha_tipo_sanguineo = ficha['tipo_sanguineo']
            ficha_alergias = ficha['alergias']
            ficha_doencas = ficha['doencas']
            ficha_medicamentos = ficha['medicamentos']
            ficha_contato_nome = ficha['contato_nome']
            ficha_contato_telefone = ficha['contato_telefone']
            ficha_atualizado_em = ficha['atualizado_em']
        else:
            ficha_tipo_sanguineo = None
            ficha_alergias = None
            ficha_doencas = None
            ficha_medicamentos = None
            ficha_contato_nome = None
            ficha_contato_telefone = None
            ficha_atualizado_em = None
        
        # Inserir serviço com snapshot da ficha médica + geocodificação completa
        cursor.execute('''
            INSERT INTO servicos 
            (usuario_id, tipo, latitude, longitude, rua, bairro, cidade, estado, cep,
             ficha_tipo_sanguineo, ficha_alergias, ficha_doencas, ficha_medicamentos,
             ficha_contato_nome, ficha_contato_telefone, ficha_atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], 
            tipo, 
            latitude, 
            longitude,
            rua,
            bairro,
            cidade,
            estado,
            cep,
            ficha_tipo_sanguineo,
            ficha_alergias,
            ficha_doencas,
            ficha_medicamentos,
            ficha_contato_nome,
            ficha_contato_telefone,
            ficha_atualizado_em
        ))
        db.commit()
        db.close()
        return jsonify({
            'sucesso': True, 
            'mensagem': f'Serviço de {tipo} acionado com sucesso! Aguarde contato.',
            'endereco': {
                'rua': rua,
                'bairro': bairro,
                'cidade': cidade,
                'estado': estado,
                'cep': cep
            }
        })
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': f'Erro ao acionar serviço: {str(e)}'}), 500

# ============================================================================
# FICHA MÉDICA
# ============================================================================

@app.route('/ficha-medica', methods=['GET'])
def ficha_medica_get():
    """Retorna dados da ficha médica do usuário logado"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, tipo_sanguineo, alergias, doencas, medicamentos, 
               contato_nome, contato_telefone, observacoes, atualizado_em
        FROM ficha_medica 
        WHERE usuario_id = ?
    ''', (session['user_id'],))
    ficha = cursor.fetchone()
    db.close()

    if ficha:
        return jsonify({
            'sucesso': True,
            'ficha': dict(ficha)
        })
    else:
        return jsonify({
            'sucesso': True,
            'ficha': None
        })

@app.route('/ficha-medica', methods=['POST'])
def ficha_medica_post():
    """Cria ou atualiza ficha médica do usuário logado"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    data = request.get_json() or {}

    # Validação de telefone (se fornecido)
    contato_telefone = data.get('contato_telefone', '').strip()
    if contato_telefone:
        telefone_limpo = contato_telefone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '').replace('.', '')
        if not telefone_limpo.isdigit() or len(telefone_limpo) < 10:
            return jsonify({'sucesso': False, 'erro': 'Telefone de emergência inválido'}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        # Verifica se já existe ficha
        cursor.execute('SELECT id FROM ficha_medica WHERE usuario_id = ?', (session['user_id'],))
        ficha_existente = cursor.fetchone()

        if ficha_existente:
            # UPDATE - atualiza ficha existente
            cursor.execute('''
                UPDATE ficha_medica SET
                    tipo_sanguineo = ?,
                    alergias = ?,
                    doencas = ?,
                    medicamentos = ?,
                    contato_nome = ?,
                    contato_telefone = ?,
                    observacoes = ?,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE usuario_id = ?
            ''', (
                data.get('tipo_sanguineo', '').strip() or None,
                data.get('alergias', '').strip() or None,
                data.get('doencas', '').strip() or None,
                data.get('medicamentos', '').strip() or None,
                data.get('contato_nome', '').strip() or None,
                contato_telefone or None,
                data.get('observacoes', '').strip() or None,
                session['user_id']
            ))
        else:
            # INSERT - cria nova ficha
            cursor.execute('''
                INSERT INTO ficha_medica 
                (usuario_id, tipo_sanguineo, alergias, doencas, medicamentos, 
                 contato_nome, contato_telefone, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'],
                data.get('tipo_sanguineo', '').strip() or None,
                data.get('alergias', '').strip() or None,
                data.get('doencas', '').strip() or None,
                data.get('medicamentos', '').strip() or None,
                data.get('contato_nome', '').strip() or None,
                contato_telefone or None,
                data.get('observacoes', '').strip() or None
            ))

        db.commit()
        db.close()
        return jsonify({'sucesso': True, 'mensagem': '✅ Ficha médica salva com sucesso!'})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': f'Erro ao salvar ficha médica: {str(e)}'}), 500

@app.route('/ficha-existe')
def ficha_existe():
    """Verifica se o usuário tem ficha médica (para alerta no acionamento de serviço)"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'tem_ficha': False})

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM ficha_medica WHERE usuario_id = ?', (session['user_id'],))
    tem_ficha = cursor.fetchone() is not None
    db.close()

    return jsonify({'sucesso': True, 'tem_ficha': tem_ficha})

@app.route('/historico')
def historico():
    """Retorna o histórico do usuário logado"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401
    
    # Admin não pode acessar o histórico de usuário comum
    if session.get('is_admin', 0):
        return jsonify({'sucesso': False, 'erro': 'Acesso negado. Use o painel Admin.'}), 403
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT nome FROM usuarios WHERE id = ?', (session['user_id'],))
    usuario = cursor.fetchone()

    cursor.execute('SELECT id, descricao, foto, data, finalizado FROM denuncias WHERE usuario_id = ? ORDER BY data DESC',
                   (session['user_id'],))
    denuncias = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT id, tipo, latitude, longitude, rua, bairro, cidade, estado, cep, data, finalizado FROM servicos WHERE usuario_id = ? ORDER BY data DESC',
                   (session['user_id'],))
    servicos = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({
        'sucesso': True,
        'usuario': {'nome': usuario['nome'] if usuario else ''},
        'denuncias': denuncias,
        'servicos': servicos
    })

# ============================================================================
# ROTAS ADMIN
# ============================================================================

@app.route('/admin')
def admin():
    """Página do painel administrativo"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if not session.get('is_admin', 0):
        return jsonify({'sucesso': False, 'erro': 'Acesso negado. Apenas administradores.'}), 403
    
    return render_template('index.html', admin=True)

@app.route('/me')
def me():
    """Retorna dados do usuário logado (nome e is_admin)"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT nome, is_admin FROM usuarios WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    db.close()
    
    return jsonify({
        'sucesso': True,
        'nome': user['nome'] if user else '',
        'is_admin': bool(user['is_admin']) if user else False
    })

@app.route('/admin/dados')
def admin_dados():
    """Retorna todos os dados de denúncias e serviços"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401
    
    if not session.get('is_admin', 0):
        return jsonify({'sucesso': False, 'erro': 'Acesso negado. Apenas administradores.'}), 403
    
    db = get_db()
    cursor = db.cursor()
    
    # Buscar dados do usuário admin logado
    cursor.execute('SELECT nome, email FROM usuarios WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    
    # Buscar todas as denúncias com nome do usuário e endereço (incluindo foto)
    cursor.execute('''
        SELECT d.id, d.descricao, d.foto, d.data, d.finalizado, u.nome as usuario_nome, u.email as usuario_email, u.endereco as usuario_endereco, u.telefone as usuario_telefone,
               f.tipo_sanguineo, f.alergias, f.doencas, f.medicamentos, f.contato_nome, f.contato_telefone
        FROM denuncias d
        JOIN usuarios u ON d.usuario_id = u.id
        LEFT JOIN ficha_medica f ON u.id = f.usuario_id
        ORDER BY d.data DESC
    ''')
    denuncias = [dict(row) for row in cursor.fetchall()]
    
    # =====================================================================
    # BUSCAR SERVIÇOS COM JOIN - dados atuais DA FICHA + snapshot
    # =====================================================================
    cursor.execute('''
        SELECT s.id, s.tipo, s.latitude, s.longitude, s.rua, s.bairro, s.cidade, s.estado, s.cep, s.data, s.finalizado, 
               u.nome as usuario_nome, u.email as usuario_email, u.endereco as usuario_endereco, u.telefone as usuario_telefone,
               -- Snapshot salvo no momento do acionamento
               s.ficha_tipo_sanguineo, s.ficha_alergias, s.ficha_doencas, s.ficha_medicamentos,
               s.ficha_contato_nome, s.ficha_contato_telefone, s.ficha_atualizado_em,
               -- Dados ATUAIS da ficha médica (tabela ficha_medica)
               f.tipo_sanguineo as atual_tipo_sanguineo,
               f.alergias as atual_alergias,
               f.doencas as atual_doencas,
               f.medicamentos as atual_medicamentos,
               f.contato_nome as atual_contato_nome,
               f.contato_telefone as atual_contato_telefone
        FROM servicos s
        JOIN usuarios u ON s.usuario_id = u.id
        LEFT JOIN ficha_medica f ON s.usuario_id = f.usuario_id
        ORDER BY s.data DESC
    ''')
    servicos_raw = cursor.fetchall()
    
    # =====================================================================
    # FUNÇÃO DE COMPARAÇÃO DE CAMPOS
    # =====================================================================
    def comparar_campos(atual, snapshot):
        """
        Compara campos atuais com snapshot.
        Retorna: 'atualizada', 'alterada' ou 'sem_ficha'
        """
        # Campos a comparar
        campos = ['tipo_sanguineo', 'alergias', 'doencas', 'medicamentos', 'contato_nome', 'contato_telefone']
        
        # Se não tem snapshot, não há o que comparar
        if not snapshot:
            return 'sem_ficha'
        
        # Verificar se tem algum dado atual na ficha_medica
        tem_ficha_atual = any([
            atual.get('atual_tipo_sanguineo'),
            atual.get('atual_alergias'),
            atual.get('atual_doencas'),
            atual.get('atual_medicamentos'),
            atual.get('atual_contato_nome'),
            atual.get('atual_contato_telefone')
        ])
        
        if not tem_ficha_atual:
            return 'sem_ficha'
        
        # Comparar cada campo
        for campo in campos:
            atual_valor = atual.get(f'atual_{campo}')
            snapshot_valor = snapshot.get(f'ficha_{campo}')
            
            # Normalizar para comparação (None ou vazio = vazio)
            atual_normalizado = (atual_valor or '').strip().lower()
            snapshot_normalizado = (snapshot_valor or '').strip().lower()
            
            # Se qualquer campo for diferente → alterada
            if atual_normalizado != snapshot_normalizado:
                return 'alterada'
        
        # Se todos os campos forem iguais → atualizada
        return 'atualizada'
    
    # =====================================================================
    # GEOCODIFICAÇÃO REVERSA COM FALLBACK - Converter lat/lon se necessário
    # =====================================================================
    def ensure_cidade_estado(servico):
        """
        Garante que cidade e estado existem.
        Se não existirem, tenta converter de lat/lon.
        """
        # Se já tem cidade ou estado, retorna como está
        if servico.get('cidade') or servico.get('estado'):
            return servico
        
        # Se não tem lat/lon, não há como converter
        if not servico.get('latitude') or not servico.get('longitude'):
            return servico
        
        # Tenta converter
        endereco = get_address_from_coords(servico['latitude'], servico['longitude'])
        if endereco:
            servico['cidade'] = endereco.get('cidade')
            servico['estado'] = endereco.get('estado')
        
        return servico
    
    # Processar cada serviço
    servicos = []
    for row in servicos_raw:
        servico = dict(row)
        
        # =====================================================================
        # APLICAR FALLBACK DE GEOCODIFICAÇÃO
        # =====================================================================
        servico = ensure_cidade_estado(servico)
        
        # Dados atuais da ficha (para retorno no JSON)
        dados_atuais = {
            'tipo_sanguineo': servico.get('atual_tipo_sanguineo'),
            'alergias': servico.get('atual_alergias'),
            'doencas': servico.get('atual_doencas'),
            'medicamentos': servico.get('atual_medicamentos'),
            'contato_nome': servico.get('atual_contato_nome'),
            'contato_telefone': servico.get('atual_contato_telefone')
        }
        
        # Snapshot (dados salvos no momento do acionamento)
        snapshot = {
            'ficha_tipo_sanguineo': servico.get('ficha_tipo_sanguineo'),
            'ficha_alergias': servico.get('ficha_alergias'),
            'ficha_doencas': servico.get('ficha_doencas'),
            'ficha_medicamentos': servico.get('ficha_medicamentos'),
            'ficha_contato_nome': servico.get('ficha_contato_nome'),
            'ficha_contato_telefone': servico.get('ficha_contato_telefone')
        }
        
        # Calcular status baseado na comparação de campos
        servico['ficha_status'] = comparar_campos(servico, snapshot)
        
        # Adicionar dados atuais e snapshot ao JSON de retorno
        servico['ficha_atual'] = dados_atuais
        servico['ficha_snapshot'] = snapshot
        
        # Remover campos duplicados que já estão em ficha_atual/ficha_snapshot
        for key in list(servico.keys()):
            if key.startswith('atual_'):
                del servico[key]
        
        servicos.append(servico)
    
    # Buscar total de usuários
    cursor.execute('SELECT COUNT(*) as total FROM usuarios')
    total_usuarios = cursor.fetchone()['total']
    
    db.close()
    
    return jsonify({
        'sucesso': True,
        'usuario': {
            'nome': admin_user['nome'] if admin_user else '',
            'email': admin_user['email'] if admin_user else ''
        },
        'denuncias': denuncias,
        'servicos': servicos,
        'estatisticas': {
            'total_denuncias': len(denuncias),
            'total_servicos': len(servicos),
            'total_usuarios': total_usuarios
        }
    })

@app.route('/admin/finalizar-denuncia/<int:denuncia_id>', methods=['POST'])
def finalizar_denuncia(denuncia_id):
    """Marca uma denúncia como finalizada"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401
    
    if not session.get('is_admin', 0):
        return jsonify({'sucesso': False, 'erro': 'Acesso negado. Apenas administradores.'}), 403
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE denuncias SET finalizado = 1 WHERE id = ?', (denuncia_id,))
        db.commit()
        db.close()
        return jsonify({'sucesso': True, 'mensagem': 'Denúncia marcada como finalizada'})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': f'Erro ao finalizar denúncia: {str(e)}'}), 500

@app.route('/admin/finalizar-servico/<int:servico_id>', methods=['POST'])
def finalizar_servico(servico_id):
    """Marca um serviço como finalizado"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401
    
    if not session.get('is_admin', 0):
        return jsonify({'sucesso': False, 'erro': 'Acesso negado. Apenas administradores.'}), 403
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE servicos SET finalizado = 1 WHERE id = ?', (servico_id,))
        db.commit()
        db.close()
        return jsonify({'sucesso': True, 'mensagem': 'Serviço marcado como finalizado'})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': f'Erro ao finalizar serviço: {str(e)}'}), 500

# ============================================================================
# ROTAS DE ARQUIVOS (UPLOADS)
# ============================================================================

@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve arquivos上传 da pasta uploads"""
    return send_from_directory(UPLOAD_FOLDER, filename)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        init_db()
        
        # Criar usuário admin padrão se não existir
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM usuarios WHERE email = ?', ('admin@emergencia.com',))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO usuarios 
                (nome, email, senha, cpf, telefone, data_nascimento, genero, lgpd_consentimento, is_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'Administrador',
                'admin@emergencia.com',
                generate_password_hash('admin123'),
                '00000000000',
                '11999999999',
                '1990-01-01',
                'Masculino',
                1,
                1
            ))
            db.commit()
            print('✅ Usuário admin criado: admin@emergencia.com / admin123')
        db.close()
        
    app.run(debug=True)