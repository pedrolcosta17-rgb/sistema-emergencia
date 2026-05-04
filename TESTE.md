# 🧪 Guia de Teste - Sistema de Emergência e Denúncias

Este documento fornece um passo-a-passo para testar todas as funcionalidades do sistema.

## ✅ Pré-requisitos

- [x] Python 3.7+
- [x] Dependências instaladas (`pip install -r requirements.txt`)
- [x] Flask rodando em `http://127.0.0.1:5000`

---

## 🔍 Teste 1: Página de Login

**Objetivo**: Verificar se a página inicial mostra o formulário de login

**Passos**:
1. Abra `http://127.0.0.1:5000` no navegador
2. Você deve ver a tela de login com título "🚨 Emergência"

**Resultado esperado**: ✅ Página carrega corretamente

---

## 📝 Teste 2: Cadastro de Novo Usuário

**Objetivo**: Criar uma nova conta com validações

**Passos**:
1. Na tela de login, clique em "Cadastre-se"
2. Preencha os campos:
   - **Nome**: João Silva (mínimo 3 caracteres)
   - **CPF**: 123.456.789-09 (formato correto)
   - **Data de Nascimento**: 01/01/1990
   - **Gênero**: Masculino
   - **Telefone Principal**: (11) 99999-9999
   - **Telefone Alternativo**: (11) 98888-8888
   - **Email**: joao@example.com
   - **Confirmar Email**: joao@example.com
   - **Senha**: senha123 (mínimo 6 caracteres)
   - **Confirmar Senha**: senha123
   - **LGPD**: Marque o checkbox
3. Clique em "Cadastrar"

**Resultado esperado**: ✅ Mensagem "Cadastro realizado com sucesso!"

**Teste de Validação**: Tente cadastrar com:
- Nome muito curto (ex: "ab") → Erro: "Nome deve ter pelo menos 3 caracteres"
- CPF inválido (ex: "000") → Erro: "CPF inválido"
- Emails diferentes → Erro: "Emails não conferem"
- Senhas diferentes → Erro: "Senhas não conferem"
- Sem aceitar LGPD → Erro: "Consentimento LGPD é obrigatório"

---

## 🔐 Teste 3: Login com Credenciais

**Objetivo**: Fazer login com a conta criada

**Passos**:
1. Volte para a tela de login
2. Digite:
   - **Email**: joao@example.com
   - **Senha**: senha123
3. Clique em "Entrar"

**Resultado esperado**: ✅ Dashboard carrega com mensagem "Bem-vindo, João Silva"

**Teste de Erro**: Tente login com:
- Email errado → Erro: "Email ou senha inválidos"
- Senha errada → Erro: "Email ou senha inválidos"
- Campos vazios → Erro: "Email e senha são obrigatórios"

---

## 🚑 Teste 4: Acionar Serviço de Emergência

**Objetivo**: Testar acionamento de serviços com geolocalização

**Passos**:
1. Após fazer login, você estará na aba "Acionar Serviço"
2. Clique em um dos botões:
   - 🚔 Polícia
   - 🚑 SAMU
   - 🚒 Bombeiros
   - 🛡️ Defesa Civil
3. O navegador pode pedir permissão para acessar a localização
4. Clique em "Permitir" (ou "Negar" para testar fallback)

**Resultado esperado**:
- ✅ Se permitir localização: "Localização capturada: [lat], [lon]"
- ✅ Se negar: "Localização não disponível - enviando mesmo assim..."
- ✅ Mensagem: "✅ Serviço de [Serviço] acionado com sucesso! Aguarde contato."

**Notas**: 
- A geolocalização só funciona em HTTPS ou localhost
- Os valores de lat/lon são armazenados no banco de dados

---

## 📋 Teste 5: Fazer Denúncia

**Objetivo**: Registrar uma denúncia

**Passos**:
1. Clique na aba "📋 Fazer Denúncia"
2. Digite uma denúncia:
   - **Descrição**: "Situação suspeita na rua X, altura do número Y, com possível envolvimento de atividade criminosa que necessita investigação imediata"
3. Clique em "Enviar Denúncia"

**Resultado esperado**: ✅ Mensagem "Denúncia registrada com sucesso!"

**Teste de Validação**: Tente enviar com:
- Menos de 10 caracteres (ex: "Teste") → Erro: "Denúncia deve ter pelo menos 10 caracteres"
- Campo vazio → Erro: "Denúncia deve ter pelo menos 10 caracteres"

**Verificar**: O campo se limpa após o envio

---

## 📜 Teste 6: Visualizar Histórico

**Objetivo**: Verificar histórico de denúncias e serviços

**Passos**:
1. Clique na aba "📜 Histórico"
2. Você deve ver:
   - **Seção Denúncias**: Lista de denúncias registradas
     - Cada item mostra descrição e data/hora
   - **Seção Serviços Acionados**: Lista de serviços
     - Cada item mostra serviço, coordenadas GPS e data/hora

**Resultado esperado**: ✅ Aparecem as denúncias e serviços que você registrou anteriormente

**Dados Exibidos**:
- Denúncias: texto completo + data
- Serviços: ícone + nome + coordenadas + data

---

## 🚪 Teste 7: Logout

**Objetivo**: Fazer logout e voltar ao login

**Passos**:
1. No header azul, clique no botão "Sair"

**Resultado esperado**: ✅ Retorna à tela de login

**Verificar**: Sessão foi encerrada (não consegue acessar /dashboard)

---

## 🔄 Teste 8: Múltiplas Contas

**Objetivo**: Verificar isolamento entre usuários

**Passos**:
1. Faça logout
2. Cadastre uma nova conta:
   - **Email**: maria@example.com
   - **Senha**: senha456
3. Após login, faça uma denúncia ou acione um serviço
4. Faça logout
5. Faça login com a primeira conta (joao@example.com)
6. Vá ao histórico

**Resultado esperado**: ✅ Cada usuário só vê seus próprios dados

---

## 💾 Teste 9: Verificar Banco de Dados

**Objetivo**: Confirmar que dados estão sendo salvos corretamente

**Passos**:
1. Abra o banco de dados com:
   ```bash
   sqlite3 database.db
   ```

2. Execute os comandos SQL:
   ```sql
   -- Ver usuários
   SELECT id, nome, email FROM usuarios;
   
   -- Ver denúncias
   SELECT usuario_id, descricao FROM denuncias;
   
   -- Ver histórico
   SELECT usuario_id, servico, latitude, longitude FROM historico;
   ```

**Resultado esperado**: ✅ Dados de seus testes aparecem no banco de dados

---

## 🌐 Teste 10: Responsividade

**Objetivo**: Verificar interface em diferentes tamanhos

**Passos**:
1. Faça login
2. Abra o DevTools (F12)
3. Teste em diferentes tamanhos:
   - Mobile: 375x667 (iPhone)
   - Tablet: 768x1024 (iPad)
   - Desktop: 1920x1080

**Resultado esperado**: 
- ✅ Layout se adapta
- ✅ Botões são clicáveis
- ✅ Texto é legível
- ✅ Sem overflow ou scroll horizontal desnecessário

---

## ⚠️ Testes de Segurança

### SQL Injection
**Teste**: Tente cadastrar com email: `' OR '1'='1`
**Resultado**: ✅ Email inválido (validação simples)

### XSS (Cross-Site Scripting)
**Teste**: Tente fazer denúncia com: `<script>alert('xss')</script>`
**Resultado**: ✅ Deveria ser armazenado como texto (sem execução)

### CSRF (Cross-Site Request Forgery)
**Teste**: Formulários devem ter proteção
**Resultado**: ✅ Flask session + JSON API = protegido

---

## 📊 Relatório de Teste

Ao completar todos os testes, você deve ter confirmado:

- [x] Página de login carrega corretamente
- [x] Cadastro funciona com validações
- [x] Login funciona com verificação de credenciais
- [x] Serviços de emergência podem ser acionados
- [x] Geolocalização é capturada (ou fallback funciona)
- [x] Denúncias podem ser registradas
- [x] Histórico mostra dados corretos
- [x] Logout funciona
- [x] Isolamento de dados entre usuários
- [x] Dados são persistidos no banco de dados
- [x] Interface é responsiva
- [x] Validações estão funcionando
- [x] Segurança básica está implementada

---

## 🐛 Resolução de Problemas

### Erro: "Conexão recusada"
**Solução**: Verifique se Flask está rodando: `python app.py`

### Erro: "ModuleNotFoundError: No module named 'flask'"
**Solução**: Instale dependências: `pip install -r requirements.txt`

### Erro: "Permissão negada ao acessar database.db"
**Solução**: Verifique permissões do arquivo e pasta

### Geolocalização não funciona
**Solução**: 
- Só funciona em HTTPS ou localhost
- Verifique permissões do navegador
- Teste em modo incógnito

### Dados não aparecem no histórico
**Solução**:
- Verifique se está logado
- Limpe cache do navegador (Ctrl+F5)
- Verifique console (F12) para erros

---

## 📝 Notas Adicionais

1. **Banco de Dados**: `database.db` é criado automaticamente na primeira execução
2. **Senhas**: São armazenadas com hash (não em texto plano)
3. **Sessão**: Armazenada em memória (não persiste após restart)
4. **Desenvolvimento**: Use `debug=True` (já habilitado)
5. **Produção**: Configure adequadamente antes de publicar

---

**Desenvolvido com ❤️ para Sistema de Emergência**
