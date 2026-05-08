import os
import re
import json
import secrets
import unicodedata
import sqlite3
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mude_em_producao'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')

# ============================================================================
# HELPERS
# ============================================================================

def normalize_text(value):
    if not value:
        return ''
    normalized = unicodedata.normalize('NFKD', str(value))
    normalized = normalized.encode('ASCII', 'ignore').decode('utf-8')
    normalized = re.sub(r'[^a-z0-9]', '', normalized.lower())
    return normalized


def map_service_name(tipo):
    if not tipo:
        return None
    mapping = {
        'policia': 'Polícia',
        'police': 'Polícia',
        'samu': 'SAMU',
        'bombeiros': 'Bombeiros',
        'defesacivil': 'Defesa Civil',
        'defesaciv': 'Defesa Civil'
    }
    return mapping.get(normalize_text(tipo))


def table_has_column(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def ensure_column(cursor, table, column, definition):
    if not table_has_column(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def reverse_geocode_server(latitude, longitude):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}&addressdetails=1"
        request = Request(url, headers={'User-Agent': 'EmergencySystem/1.0 (+https://example.com)'});
        with urlopen(request, timeout=10) as response:
            raw = response.read().decode('utf-8')
            data = json.loads(raw)
            address = data.get('address', {})
            return {
                'endereco_completo': data.get('display_name', ''),
                'rua': address.get('road', '') or address.get('pedestrian', '') or address.get('path', ''),
                'numero': address.get('house_number', ''),
                'bairro': address.get('neighbourhood', '') or address.get('suburb', '') or address.get('city_district', ''),
                'cidade': address.get('city', '') or address.get('town', '') or address.get('village', '') or address.get('county', ''),
                'estado': address.get('state', '') or address.get('region', ''),
                'cep': address.get('postcode', ''),
                'pais': address.get('country', ''),
                'precisao': None
            }
    except (HTTPError, URLError, ValueError, TimeoutError):
        return None


def get_user_by_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, nome, email, is_admin, ativo, endereco FROM usuarios WHERE id = ?', (user_id,))
    usuario = cursor.fetchone()
    db.close()
    return usuario


def get_ficha_medica(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM ficha_medica WHERE usuario_id = ?', (usuario_id,))
    ficha = cursor.fetchone()
    db.close()
    return ficha

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
            lgpd_consentimento INTEGER,
            endereco TEXT,
            is_admin INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS denuncias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            foto TEXT,
            finalizado INTEGER DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ficha_medica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expiracao TIMESTAMP,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            endereco_completo TEXT,
            rua TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT,
            pais TEXT,
            precisao REAL,
            ficha_tipo_sanguineo TEXT,
            ficha_alergias TEXT,
            ficha_doencas TEXT,
            ficha_medicamentos TEXT,
            ficha_contato_nome TEXT,
            ficha_contato_telefone TEXT,
            ficha_atualizado_em TEXT,
            finalizado INTEGER DEFAULT 0,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # Garante migração de colunas caso o banco tenha sido criado com versão anterior
    extras = [
        ('usuarios', 'endereco', 'TEXT'),
        ('usuarios', 'is_admin', 'INTEGER DEFAULT 0'),
        ('usuarios', 'ativo', 'INTEGER DEFAULT 1'),
        ('denuncias', 'foto', 'TEXT'),
        ('denuncias', 'finalizado', 'INTEGER DEFAULT 0'),
        ('ficha_medica', 'atualizado_em', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('tokens_login', 'expiracao', 'TIMESTAMP'),
        ('servicos', 'endereco_completo', 'TEXT'),
        ('servicos', 'rua', 'TEXT'),
        ('servicos', 'bairro', 'TEXT'),
        ('servicos', 'cidade', 'TEXT'),
        ('servicos', 'estado', 'TEXT'),
        ('servicos', 'cep', 'TEXT'),
        ('servicos', 'pais', 'TEXT'),
        ('servicos', 'precisao', 'REAL'),
        ('servicos', 'ficha_tipo_sanguineo', 'TEXT'),
        ('servicos', 'ficha_alergias', 'TEXT'),
        ('servicos', 'ficha_doencas', 'TEXT'),
        ('servicos', 'ficha_medicamentos', 'TEXT'),
        ('servicos', 'ficha_contato_nome', 'TEXT'),
        ('servicos', 'ficha_contato_telefone', 'TEXT'),
        ('servicos', 'ficha_atualizado_em', 'TEXT'),
        ('servicos', 'finalizado', 'INTEGER DEFAULT 0')
    ]

    for table, column, definition in extras:
        ensure_column(cursor, table, column, definition)

    db.commit()
    db.close()

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
        return render_template('index.html')

    if request.method == 'POST':
        data = request.get_json() or {}

        if not data.get('nome') or len(data['nome'].strip()) < 3:
            return jsonify({'sucesso': False, 'erro': 'Nome deve ter pelo menos 3 caracteres'}), 400

        if not validar_cpf(data.get('cpf', '')):
            return jsonify({'sucesso': False, 'erro': 'CPF inválido'}), 400

        if not data.get('data_nascimento'):
            return jsonify({'sucesso': False, 'erro': 'Data de nascimento é obrigatória'}), 400

        telefone_principal = data.get('telefone_principal') or ''
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

        endereco_parts = []
        if data.get('rua'):
            endereco_parts.append(data.get('rua').strip())
        if data.get('numero'):
            endereco_parts.append(data.get('numero').strip())
        if data.get('bairro'):
            endereco_parts.append(data.get('bairro').strip())
        if data.get('municipio'):
            endereco_parts.append(data.get('municipio').strip())
        if data.get('estado'):
            endereco_parts.append(data.get('estado').strip())
        if data.get('cep'):
            endereco_parts.append(data.get('cep').strip())
        endereco_completo = ', '.join([part for part in endereco_parts if part]) or None

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO usuarios
                (nome, email, senha, cpf, telefone, data_nascimento, genero, telefone_alternativo, lgpd_consentimento, endereco)
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
                1,
                endereco_completo
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
        cursor.execute('SELECT id, senha, is_admin, ativo FROM usuarios WHERE email = ?', (email,))
        user = cursor.fetchone()

        if not user:
            db.close()
            return jsonify({'sucesso': False, 'erro': 'Email ou senha inválidos'}), 401

        if not check_password_hash(user['senha'], senha):
            db.close()
            return jsonify({'sucesso': False, 'erro': 'Email ou senha inválidos'}), 401

        if user['ativo'] == 0:
            db.close()
            return jsonify({'sucesso': False, 'erro': 'Conta desativada. Entre em contato com o administrador.'}), 403

        session['user_id'] = user['id']

        token = secrets.token_urlsafe(32)
        expiracao = (datetime.utcnow() + timedelta(days=30)).isoformat()
        cursor.execute('INSERT INTO tokens_login (usuario_id, token, expiracao) VALUES (?, ?, ?)',
                       (user['id'], token, expiracao))
        db.commit()
        db.close()

        return jsonify({
            'sucesso': True,
            'mensagem': 'Login realizado com sucesso!',
            'token': token,
            'is_admin': bool(user['is_admin'])
        })

    return render_template('index.html')

@app.route('/me')
def me():
    if 'user_id' not in session:
        return jsonify({'sucesso': False}), 401

    usuario = get_user_by_id(session['user_id'])
    if not usuario:
        session.clear()
        return jsonify({'sucesso': False}), 401

    return jsonify({
        'sucesso': True,
        'nome': usuario['nome'],
        'email': usuario['email'],
        'is_admin': bool(usuario['is_admin'])
    })

@app.route('/auto-login')
def auto_login():
    token = request.args.get('token', '').strip()
    if not token:
        return jsonify({'sucesso': False, 'erro': 'Token ausente'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT usuario_id, expiracao FROM tokens_login WHERE token = ?', (token,))
    registro = cursor.fetchone()

    if not registro:
        db.close()
        return jsonify({'sucesso': False, 'erro': 'Token inválido'}), 401

    expiracao = registro['expiracao']
    if expiracao:
        try:
            expiracao_dt = datetime.fromisoformat(expiracao)
            if expiracao_dt < datetime.utcnow():
                cursor.execute('DELETE FROM tokens_login WHERE token = ?', (token,))
                db.commit()
                db.close()
                return jsonify({'sucesso': False, 'erro': 'Token expirado'}), 401
        except ValueError:
            pass

    usuario = get_user_by_id(registro['usuario_id'])
    db.close()

    if not usuario:
        return jsonify({'sucesso': False, 'erro': 'Usuário não encontrado'}), 401

    if usuario['ativo'] == 0:
        return jsonify({'sucesso': False, 'erro': 'Conta desativada'}), 403

    session['user_id'] = registro['usuario_id']
    return jsonify({'sucesso': True, 'nome': usuario['nome'], 'is_admin': bool(usuario['is_admin'])})

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/denuncia', methods=['POST'])
def denuncia():
    """Recebe e salva denúncia no banco de dados"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401
    
    data = request.get_json()
    descricao = data.get('descricao', '').strip()
    
    if not descricao or len(descricao) < 10:
        return jsonify({'sucesso': False, 'erro': 'Denúncia deve ter pelo menos 10 caracteres'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO denuncias (usuario_id, descricao)
            VALUES (?, ?)
        ''', (session['user_id'], descricao))
        db.commit()
        db.close()
        return jsonify({'sucesso': True, 'mensagem': 'Denúncia registrada com sucesso!'})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': 'Erro ao salvar denúncia'}), 500

@app.route('/servico', methods=['POST'])
def servico():
    """Aciona serviço de emergência e salva no banco de dados"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    data = request.get_json() or {}
    raw_tipo = data.get('servico', '')
    tipo = map_service_name(raw_tipo)

    if not tipo:
        app.logger.debug('Serviço inválido recebido: %s', raw_tipo)
        return jsonify({'sucesso': False, 'erro': 'Serviço inválido'}), 400

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    endereco_completo = data.get('endereco_completo') or data.get('endereco') or ''
    rua = data.get('rua', '')
    bairro = data.get('bairro', '')
    cidade = data.get('cidade', '')
    estado = data.get('estado', '')
    cep = data.get('cep', '')
    pais = data.get('pais', '')
    precisao = data.get('precisao')

    if not endereco_completo and latitude is not None and longitude is not None:
        geocode_data = reverse_geocode_server(latitude, longitude)
        if geocode_data:
            endereco_completo = endereco_completo or geocode_data.get('endereco_completo', '')
            rua = rua or geocode_data.get('rua', '')
            bairro = bairro or geocode_data.get('bairro', '')
            cidade = cidade or geocode_data.get('cidade', '')
            estado = estado or geocode_data.get('estado', '')
            cep = cep or geocode_data.get('cep', '')
            pais = pais or geocode_data.get('pais', '')

    try:
        ficha = get_ficha_medica(session['user_id'])
        ficha_tipo_sanguineo = ficha['tipo_sanguineo'] if ficha else None
        ficha_alergias = ficha['alergias'] if ficha else None
        ficha_doencas = ficha['doencas'] if ficha else None
        ficha_medicamentos = ficha['medicamentos'] if ficha else None
        ficha_contato_nome = ficha['contato_nome'] if ficha else None
        ficha_contato_telefone = ficha['contato_telefone'] if ficha else None
        ficha_atualizado_em = ficha['atualizado_em'] if ficha else None

        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO servicos (
                usuario_id, tipo, latitude, longitude, endereco_completo,
                rua, bairro, cidade, estado, cep, pais, precisao,
                ficha_tipo_sanguineo, ficha_alergias, ficha_doencas,
                ficha_medicamentos, ficha_contato_nome, ficha_contato_telefone,
                ficha_atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], tipo, latitude, longitude, endereco_completo,
            rua, bairro, cidade, estado, cep, pais, precisao,
            ficha_tipo_sanguineo, ficha_alergias, ficha_doencas,
            ficha_medicamentos, ficha_contato_nome, ficha_contato_telefone,
            ficha_atualizado_em
        ))
        db.commit()
        db.close()

        return jsonify({
            'sucesso': True,
            'mensagem': f'Serviço de {tipo} acionado com sucesso! Aguarde contato.',
            'cidade': cidade,
            'estado': estado
        })
    except Exception as e:
        app.logger.exception('Erro ao salvar serviço: %s', e)
        return jsonify({'sucesso': False, 'erro': 'Erro ao acionar serviço'}), 500

@app.route('/historico')
def historico():
    """Retorna o histórico do usuário logado"""
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT nome FROM usuarios WHERE id = ?', (session['user_id'],))
    usuario = cursor.fetchone()

    cursor.execute('SELECT id, descricao, data, foto, finalizado FROM denuncias WHERE usuario_id = ? ORDER BY data DESC',
                   (session['user_id'],))
    denuncias = [dict(row) for row in cursor.fetchall()]

    cursor.execute('''
        SELECT id, tipo, latitude, longitude, endereco_completo, rua, bairro,
               cidade, estado, cep, pais, precisao, data, finalizado
        FROM servicos
        WHERE usuario_id = ?
        ORDER BY data DESC
    ''', (session['user_id'],))
    servicos = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({
        'sucesso': True,
        'usuario': {'nome': usuario['nome'] if usuario else ''},
        'denuncias': denuncias,
        'servicos': servicos
    })

# ============================================================================
@app.route('/ficha-medica', methods=['GET', 'POST'])
def ficha_medica():
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    db = get_db()
    cursor = db.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM ficha_medica WHERE usuario_id = ?', (session['user_id'],))
        ficha = cursor.fetchone()
        db.close()
        return jsonify({'sucesso': True, 'ficha': dict(ficha) if ficha else None})

    data = request.get_json() or {}
    tipo_sanguineo = data.get('tipo_sanguineo', '').strip()
    alergias = data.get('alergias', '').strip()
    doencas = data.get('doencas', '').strip()
    medicamentos = data.get('medicamentos', '').strip()
    contato_nome = data.get('contato_nome', '').strip()
    contato_telefone = data.get('contato_telefone', '').strip()
    observacoes = data.get('observacoes', '').strip()
    atualizado_em = datetime.utcnow().isoformat()

    try:
        cursor.execute('SELECT id FROM ficha_medica WHERE usuario_id = ?', (session['user_id'],))
        ficha_existente = cursor.fetchone()

        if ficha_existente:
            cursor.execute('''
                UPDATE ficha_medica
                SET tipo_sanguineo = ?, alergias = ?, doencas = ?, medicamentos = ?,
                    contato_nome = ?, contato_telefone = ?, observacoes = ?, atualizado_em = ?
                WHERE usuario_id = ?
            ''', (
                tipo_sanguineo, alergias, doencas, medicamentos,
                contato_nome, contato_telefone, observacoes, atualizado_em,
                session['user_id']
            ))
        else:
            cursor.execute('''
                INSERT INTO ficha_medica (
                    usuario_id, tipo_sanguineo, alergias, doencas, medicamentos,
                    contato_nome, contato_telefone, observacoes, atualizado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'], tipo_sanguineo, alergias, doencas, medicamentos,
                contato_nome, contato_telefone, observacoes, atualizado_em
            ))
        db.commit()
        db.close()
        return jsonify({'sucesso': True, 'mensagem': 'Ficha médica salva com sucesso!'})
    except Exception as e:
        db.close()
        return jsonify({'sucesso': False, 'erro': f'Erro ao salvar ficha médica: {str(e)}'}), 500

@app.route('/ficha-existe')
def ficha_existe():
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(1) AS total FROM ficha_medica WHERE usuario_id = ?', (session['user_id'],))
    tem_ficha = cursor.fetchone()['total'] > 0
    db.close()
    return jsonify({'sucesso': True, 'tem_ficha': tem_ficha})

@app.route('/admin/dados')
def admin_dados():
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    usuario = get_user_by_id(session['user_id'])
    if not usuario or not usuario['is_admin']:
        return jsonify({'sucesso': False, 'erro': 'Acesso negado'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(1) AS total_denuncias FROM denuncias')
    total_denuncias = cursor.fetchone()['total_denuncias']
    cursor.execute('SELECT COUNT(1) AS total_servicos FROM servicos')
    total_servicos = cursor.fetchone()['total_servicos']
    cursor.execute('SELECT COUNT(1) AS total_usuarios FROM usuarios')
    total_usuarios = cursor.fetchone()['total_usuarios']

    cursor.execute('''
        SELECT d.id, d.descricao, d.data, d.foto, d.finalizado,
               u.nome AS usuario_nome, u.email AS usuario_email,
               u.telefone AS usuario_telefone, u.endereco AS usuario_endereco
        FROM denuncias d
        JOIN usuarios u ON u.id = d.usuario_id
        ORDER BY d.data DESC
    ''')
    denuncias = [dict(row) for row in cursor.fetchall()]

    cursor.execute('''
        SELECT s.id, s.tipo, s.latitude, s.longitude, s.endereco_completo, s.rua, s.bairro,
               s.cidade, s.estado, s.cep, s.pais, s.precisao, s.data, s.finalizado,
               u.nome AS usuario_nome, u.email AS usuario_email,
               u.telefone AS usuario_telefone, u.endereco AS usuario_endereco
        FROM servicos s
        JOIN usuarios u ON u.id = s.usuario_id
        ORDER BY s.data DESC
    ''')
    servicos = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT id, nome, email, cpf, telefone, criado_em, ativo FROM usuarios ORDER BY criado_em DESC')
    usuarios = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({
        'sucesso': True,
        'usuario': {'nome': usuario['nome']},
        'estatisticas': {
            'total_denuncias': total_denuncias,
            'total_servicos': total_servicos,
            'total_usuarios': total_usuarios
        },
        'denuncias': denuncias,
        'servicos': servicos,
        'usuarios': usuarios
    })

@app.route('/admin/usuario/<int:usuario_id>/status', methods=['POST'])
def admin_alterar_status_usuario(usuario_id):
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    usuario = get_user_by_id(session['user_id'])
    if not usuario or not usuario['is_admin']:
        return jsonify({'sucesso': False, 'erro': 'Acesso negado'}), 403

    data = request.get_json() or {}
    ativo = 1 if data.get('ativo') else 0

    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE usuarios SET ativo = ? WHERE id = ?', (ativo, usuario_id))
    db.commit()
    db.close()
    return jsonify({'sucesso': True, 'mensagem': 'Status do usuário atualizado com sucesso!'})

@app.route('/admin/finalizar-denuncia/<int:denuncia_id>', methods=['POST'])
def admin_finalizar_denuncia(denuncia_id):
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    usuario = get_user_by_id(session['user_id'])
    if not usuario or not usuario['is_admin']:
        return jsonify({'sucesso': False, 'erro': 'Acesso negado'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE denuncias SET finalizado = 1 WHERE id = ?', (denuncia_id,))
    db.commit()
    db.close()
    return jsonify({'sucesso': True, 'mensagem': 'Denúncia finalizada com sucesso!'})

@app.route('/admin/finalizar-servico/<int:servico_id>', methods=['POST'])
def admin_finalizar_servico(servico_id):
    if 'user_id' not in session:
        return jsonify({'sucesso': False, 'erro': 'Usuário não autenticado'}), 401

    usuario = get_user_by_id(session['user_id'])
    if not usuario or not usuario['is_admin']:
        return jsonify({'sucesso': False, 'erro': 'Acesso negado'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE servicos SET finalizado = 1 WHERE id = ?', (servico_id,))
    db.commit()
    db.close()
    return jsonify({'sucesso': True, 'mensagem': 'Serviço finalizado com sucesso!'})

# MAIN
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)