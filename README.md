# 🚨 Sistema de Emergência e Denúncias

Um sistema web completo para gerenciar denúncias e acionamento de serviços de emergência, construído com Python Flask, SQLite e HTML/CSS/JavaScript puro.

## 📋 Características

- ✅ **Autenticação de Usuários** - Login e cadastro com validações
- ✅ **Gerenciamento de Dados** - Banco de dados SQLite com relacionamentos
- ✅ **Denúncias** - Sistema para registro de denúncias anônimas
- ✅ **Serviços de Emergência** - Acionamento de Polícia, SAMU, Bombeiros, Defesa Civil
- ✅ **Geolocalização** - Captura automática de coordenadas GPS
- ✅ **Histórico** - Rastreamento de denúncias e serviços acionados
- ✅ **Interface Responsiva** - Design mobile-friendly com Tailwind CSS
- ✅ **Segurança** - Hashing de senhas com werkzeug.security

## 🗂️ Estrutura do Projeto

```
projeto/
├── app.py                    # Backend Flask principal
├── requirements.txt          # Dependências Python
├── database.db              # Banco de dados SQLite (criado automaticamente)
├── templates/
│   └── index.html           # Template HTML principal
└── static/
    ├── script.js            # JavaScript do frontend
    └── style.css            # Estilos customizados
```

## 🚀 Como Usar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar a Aplicação

```bash
python app.py
```

A aplicação estará disponível em `http://127.0.0.1:5000`

### 3. Usar o Sistema

#### Cadastro
1. Clique em "Cadastre-se" na tela de login
2. Preencha todos os campos obrigatórios (marcados com *)
3. Aceite o consentimento LGPD
4. Clique em "Cadastrar"

#### Login
1. Digite seu email e senha
2. Clique em "Entrar"

#### Acionar Serviço de Emergência
1. Na aba "Acionar Serviço", escolha um dos serviços:
   - 🚔 Polícia
   - 🚑 SAMU
   - 🚒 Bombeiros
   - 🛡️ Defesa Civil
2. Sua localização será capturada automaticamente
3. O serviço será registrado no histórico

#### Fazer Denúncia
1. Na aba "Fazer Denúncia", descreva o fato
2. Mínimo de 10 caracteres
3. Clique em "Enviar Denúncia"

#### Visualizar Histórico
1. Na aba "Histórico", veja todas suas denúncias e serviços acionados
2. Cada registro mostra data/hora e localização (se capturada)

## 📊 Banco de Dados

O sistema cria automaticamente três tabelas:

### `usuarios`
- `id` - ID único (chave primária)
- `nome` - Nome completo
- `cpf` - CPF (único)
- `data_nascimento` - Data de nascimento
- `telefone_principal` - Telefone principal
- `telefone_alternativo` - Telefone alternativo (opcional)
- `genero` - Gênero
- `email` - Email (único)
- `senha` - Senha com hash
- `lgpd_consentimento` - Consentimento LGPD
- `data_criacao` - Data de criação da conta

### `denuncias`
- `id` - ID único (chave primária)
- `usuario_id` - FK para usuários
- `descricao` - Texto da denúncia
- `data_criacao` - Data da denúncia

### `historico`
- `id` - ID único (chave primária)
- `usuario_id` - FK para usuários
- `servico` - Tipo de serviço acionado
- `latitude` - Coordenada de latitude
- `longitude` - Coordenada de longitude
- `data_acionamento` - Data do acionamento

## 🔐 Segurança

- Senhas são armazenadas com hash (werkzeug.security)
- Validação de entrada em todos os formulários
- Proteção de rotas com session
- LGPD compliance obrigatório

## 🌐 Rotas da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Página principal (redireciona) |
| GET | `/login` | Página de login |
| POST | `/login` | Autenticar usuário |
| GET | `/cadastro` | Página de cadastro |
| POST | `/cadastro` | Registrar novo usuário |
| GET | `/logout` | Fazer logout |
| GET | `/dashboard` | Dashboard do usuário |
| POST | `/denuncia` | Registrar denúncia |
| POST | `/acionar-servico` | Acionar serviço emergência |
| GET | `/historico` | Obter histórico do usuário |

## 📱 Validações Implementadas

### Cadastro
- Nome: mínimo 3 caracteres
- CPF: formato correto (11 dígitos)
- Data de nascimento: obrigatória
- Telefone: mínimo 10 dígitos
- Email: formato válido
- Confirmação de email: deve corresponder
- Senha: mínimo 6 caracteres
- Confirmação de senha: deve corresponder
- LGPD: consentimento obrigatório

### Denúncia
- Mínimo 10 caracteres
- Obrigatório usuário autenticado

### Geolocalização
- Captura automática via Geolocation API
- Funciona em HTTPS ou localhost
- Graceful fallback se não disponível

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3, Flask 2.3
- **Banco de Dados**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript puro
- **Styling**: Tailwind CSS (CDN)
- **Segurança**: werkzeug.security
- **Autenticação**: Flask Sessions

## 📝 Notas Importantes

1. O arquivo `database.db` é criado automaticamente na primeira execução
2. Em produção, mude a chave secreta em `app.py`
3. Para HTTPS, use um proxy reverso como Nginx
4. A geolocalização requer HTTPS ou localhost
5. Este é um sistema de desenvolvimento, não use em produção sem melhorias de segurança

## 🤝 Próximos Passos

Para melhorar o sistema em produção:

1. Usar um servidor WSGI (Gunicorn, uWSGI)
2. Implementar autenticação 2FA
3. Adicionar rate limiting
4. Criptografar dados sensíveis
5. Implementar logs de auditoria
6. Adicionar testes automatizados
7. Documentação API (Swagger/OpenAPI)

## 📄 Licença

Este projeto é fornecido como exemplo educacional.

---

**Desenvolvido com ❤️ para Sistema de Emergência**
