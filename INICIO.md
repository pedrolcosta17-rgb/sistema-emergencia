# 🎉 Sistema de Emergência e Denúncias - COMPLETO!

## 📦 O que foi criado

Um **sistema web completo e funcional** de gerenciamento de emergências e denúncias, com:

✅ **Backend Python/Flask** - Com autenticação, validações e API REST
✅ **Banco de Dados SQLite** - Criado automaticamente com 3 tabelas relacionadas
✅ **Frontend HTML/CSS/JavaScript** - Interface responsiva e intuitiva
✅ **Segurança** - Hashing de senhas, validações, proteção de sessão
✅ **Geolocalização** - Captura automática de coordenadas GPS
✅ **Responsividade** - Funciona em desktop, tablet e mobile

---

## 📁 Estrutura dos Arquivos

```
projeto/
├── 📄 app.py                    (Python Flask - Backend)
├── 📄 requirements.txt          (Dependências Python)
├── 📄 database.db              (SQLite - Criado automaticamente)
├── 📄 README.md                (Documentação completa)
├── 📄 TESTE.md                 (Guia de testes)
├── 📁 templates/
│   └── 📄 index.html           (HTML principal)
└── 📁 static/
    ├── 📄 script.js            (JavaScript do frontend)
    └── 📄 style.css            (CSS customizado)
```

---

## 🚀 Como Usar

### Iniciar a Aplicação
```bash
cd "c:\Users\sistema.not\Desktop\projeto"
python app.py
```

A aplicação estará em: **http://127.0.0.1:5000**

### Usuário de Teste
Você pode criar uma conta de teste seguindo as instruções na aplicação.

---

## ✨ Funcionalidades Implementadas

### 1️⃣ Autenticação
- ✅ Cadastro com validação completa
- ✅ Login com autenticação
- ✅ Logout
- ✅ Proteção de rotas

### 2️⃣ Cadastro de Usuários
Campos validados:
- Nome (mínimo 3 caracteres)
- CPF (11 dígitos)
- Data de Nascimento
- Telefone Principal (10+ dígitos)
- Telefone Alternativo (opcional)
- Gênero
- Email (formato válido)
- Confirmação de Email
- Senha (mínimo 6 caracteres)
- Confirmação de Senha
- Consentimento LGPD (obrigatório)

### 3️⃣ Denúncias
- Registro de texto com mínimo 10 caracteres
- Armazenamento seguro no banco
- Acesso apenas ao próprio histórico

### 4️⃣ Acionamento de Emergências
Serviços disponíveis:
- 🚔 Polícia
- 🚑 SAMU
- 🚒 Bombeiros
- 🛡️ Defesa Civil

Com:
- Captura automática de GPS
- Fallback se geolocalização não disponível
- Confirmação de acionamento

### 5️⃣ Histórico
- Denúncias com data/hora
- Serviços acionados com GPS
- Filtro por usuário logado
- Formatação de data em português

---

## 🗄️ Banco de Dados

### Tabela: `usuarios`
```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE NOT NULL,
    data_nascimento TEXT NOT NULL,
    telefone_principal TEXT NOT NULL,
    telefone_alternativo TEXT,
    genero TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    lgpd_consentimento INTEGER NOT NULL,
    data_criacao TIMESTAMP
);
```

### Tabela: `denuncias`
```sql
CREATE TABLE denuncias (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    data_criacao TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

### Tabela: `historico`
```sql
CREATE TABLE historico (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    servico TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    data_acionamento TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

---

## 🔧 Rotas da API

| Método | Rota | Descrição | Autenticado |
|--------|------|-----------|-------------|
| GET | `/` | Página principal | Não |
| GET | `/login` | Página de login | Não |
| POST | `/login` | Autenticar | Não |
| GET/POST | `/cadastro` | Cadastro | Não |
| GET | `/logout` | Deslogar | Sim |
| GET | `/dashboard` | Dashboard | Sim |
| POST | `/denuncia` | Registrar denúncia | Sim |
| POST | `/acionar-servico` | Acionar serviço | Sim |
| GET | `/historico` | Ver histórico | Sim |

---

## 💻 Tecnologias

- **Backend**: Python 3, Flask 2.3
- **Banco de Dados**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript puro
- **UI Framework**: Tailwind CSS (CDN)
- **Segurança**: werkzeug.security (hashing)
- **Autenticação**: Flask Sessions

---

## 🔐 Segurança Implementada

✅ **Senhas com Hash** - Usando werkzeug.security.generate_password_hash
✅ **Validação de Input** - Email, CPF, telefone, senhas
✅ **Proteção de Rota** - Verifica user_id em session
✅ **SQL Injection Prevention** - Usando parameterized queries
✅ **LGPD Compliance** - Consentimento obrigatório
✅ **CSRF Protection** - JSON API + Flask sessions

---

## 📱 Interface

### Telas Principais
1. **Login** - Email e senha
2. **Cadastro** - Formulário completo com validações
3. **Dashboard** - Menu com 3 abas:
   - Acionar Serviço (com botões de emergência)
   - Fazer Denúncia (textarea)
   - Histórico (lista de atividades)

### Design
- ✅ Responsivo (mobile, tablet, desktop)
- ✅ Cores intuitivas (vermelho=perigo, verde=sucesso)
- ✅ Ícones e emojis para melhor UX
- ✅ Mensagens de erro/sucesso claras
- ✅ Transições suaves

---

## 📊 Validações

### Cadastro
- ✅ Nome: 3+ caracteres
- ✅ CPF: 11 dígitos
- ✅ Email: formato válido
- ✅ Emails correspondem
- ✅ Senha: 6+ caracteres
- ✅ Senhas correspondem
- ✅ LGPD: checkbox marcado

### Denúncia
- ✅ 10+ caracteres
- ✅ Usuário autenticado

### Serviços
- ✅ Serviço válido
- ✅ Usuário autenticado

---

## 🧪 Como Testar

Veja `TESTE.md` para um guia completo de testes incluindo:
- Cadastro e login
- Acionamento de serviços
- Registro de denúncias
- Verificação de histórico
- Testes de validação
- Testes de segurança

---

## ⚙️ Próximos Passos (Sugestões para Produção)

1. **Servidor WSGI**
   ```bash
   pip install gunicorn
   gunicorn app:app
   ```

2. **HTTPS/SSL**
   - Usar nginx como proxy reverso
   - Certificado Let's Encrypt

3. **Melhorias de Segurança**
   - 2FA (Two-Factor Authentication)
   - Rate limiting
   - CORS configuration
   - API keys

4. **Funcionalidades Adicionais**
   - Dashboard administrativo
   - Notificações por email/SMS
   - Integração com serviços reais
   - API GraphQL
   - Testes automatizados

5. **Deployment**
   - Docker container
   - AWS/Azure/Heroku
   - CI/CD pipeline

---

## 📞 Suporte

Se encontrar problemas:

1. **Verifique logs** - Console do Flask mostra erros
2. **Browser DevTools** - F12 para ver erros do JavaScript
3. **Database** - `sqlite3 database.db` para verificar dados
4. **Dependências** - `pip install -r requirements.txt`

---

## 📄 Licença

Este projeto é fornecido como exemplo educacional e de demonstração.

---

## 🎓 Aprendizado

Este sistema demonstra:
- ✅ Arquitetura MVC com Flask
- ✅ Banco de dados relacional (SQLite)
- ✅ Autenticação e sessões
- ✅ Validação de dados
- ✅ API RESTful com JSON
- ✅ Frontend vanilla JavaScript
- ✅ Segurança básica
- ✅ Responsividade CSS
- ✅ Boas práticas de código

---

**Parabéns! 🎉 Seu sistema está completo e pronto para uso!**

Para iniciar: `python app.py`

Acesse: `http://127.0.0.1:5000`
