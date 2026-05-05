// ============================================================================
// FUNCIONALIDADES DE NAVEGAÇÃO
// ============================================================================

/**
 * Mostra a tela de login
 */
function mostrarLogin() {
    document.getElementById('telaLogin').classList.remove('hidden');
    document.getElementById('telaCadastro').classList.add('hidden');
    document.getElementById('telaDashboard').classList.add('hidden');
}

/**
 * Mostra a tela de cadastro
 */
function mostrarCadastro() {
    document.getElementById('telaLogin').classList.add('hidden');
    document.getElementById('telaCadastro').classList.remove('hidden');
    document.getElementById('telaDashboard').classList.add('hidden');
}

/**
 * Mostra o dashboard
 */
function mostrarDashboard() {
    document.getElementById('telaLogin').classList.add('hidden');
    document.getElementById('telaCadastro').classList.add('hidden');
    document.getElementById('telaDashboard').classList.remove('hidden');
}

const authState = {
    logado: false,
    tentandoAutoLogin: false,
    tokenPresente: false
};

/**
 * Mostra uma aba específica do dashboard
 */
function mostrarAba(abaName) {
    // Esconde todas as abas
    const abas = document.querySelectorAll('.aba-conteudo');
    abas.forEach(aba => aba.classList.add('hidden'));

    // Remove a classe ativa de todos os botões
    const botoes = document.querySelectorAll('.aba-btn');
    botoes.forEach(btn => btn.classList.remove('bg-blue-600'));
    botoes.forEach(btn => btn.classList.add('bg-gray-400'));

    // Mostra a aba selecionada
    document.getElementById('aba' + abaName.charAt(0).toUpperCase() + abaName.slice(1)).classList.remove('hidden');

    // Ativa o botão correto (verifica se existe para evitar erro)
    const btn = document.querySelector(`[data-aba="${abaName}"]`);
    if (btn) {
        btn.classList.remove('bg-gray-400');
        btn.classList.add('bg-blue-600');
    }

    // Se for o histórico, carrega os dados
    if (abaName === 'historico') {
        carregarHistorico();
    }
    // Se for o admin, carrega os dados
    if (abaName === 'admin') {
        carregarAdmin();
    }
    // Se for ficha médica, carrega os dados
    if (abaName === 'fichaMedica') {
        // Pequeno delay para garantir que o DOM esteja pronto
        setTimeout(() => {
            carregarFichaMedica();
        }, 50);
    }
}

// ============================================================================
// FUNCIONALIDADE 1: VERIFICAÇÃO DE LOGIN AUTOMÁTICO AO CARREGAR PÁGINA
// ============================================================================

/**
 * Verifica se existe token salvo e tenta login automático
 */
async function verificarLoginAutomatico() {
    const token = localStorage.getItem('auth_token');
    authState.tokenPresente = !!token;
    authState.tentandoAutoLogin = true;
    
    if (!token) {
        console.log('🔍 Nenhum token encontrado no localStorage');
        authState.tentandoAutoLogin = false;
        return false;
    }
    
    try {
        console.log('🔄 Tentando login automático com token...');
        const response = await fetch(`/auto-login?token=${encodeURIComponent(token)}`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            authState.logado = true;
            console.log('✅ Login automático realizado:', data.nome);
            
            // Define o nome do usuário logado
            document.getElementById('nomeUsuarioSpan').textContent = data.nome;
            
            if (data.is_admin) {
                document.getElementById('btnAdmin').classList.remove('hidden');
                document.getElementById('btnHistorico').classList.add('hidden');
                mostrarDashboard();
                mostrarAba('admin');
            } else {
                document.getElementById('btnAdmin').classList.add('hidden');
                document.getElementById('btnHistorico').classList.remove('hidden');
                mostrarDashboard();
                // Usuário comum: vai direto para dashboard principal (acionar serviço)
                mostrarAba('acionarServico');
            }
            authState.tentandoAutoLogin = false;
            return true;
        } else {
            console.log('❌ Token inválido, removendo do localStorage');
            localStorage.removeItem('auth_token');
            authState.logado = false;
            authState.tentandoAutoLogin = false;
            return false;
        }
    } catch (erro) {
        console.error('Erro no login automático:', erro);
        localStorage.removeItem('auth_token');
        authState.logado = false;
        authState.tentandoAutoLogin = false;
        return false;
    }
}

// ============================================================================
// AUTENTICAÇÃO
// ============================================================================

/**
 * Faz login do usuário
 */
document.getElementById('formLogin').addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const senha = document.getElementById('loginSenha').value;
    const msgDiv = document.getElementById('mensagemLogin');

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, senha })
        });

        const data = await response.json();

        if (data.sucesso) {
            msgDiv.textContent = '✅ ' + data.mensagem;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-green-700 bg-green-100';
            msgDiv.classList.remove('hidden');

            // =====================================================================
            // FUNCIONALIDADE 1: SALVAR TOKEN NO LOCALSTORAGE PARA LOGIN PERSISTENTE
            // =====================================================================
            if (data.token) {
                localStorage.setItem('auth_token', data.token);
                console.log('🔑 Token salvo no localStorage para login persistente');
            }

            // Limpa campos de login por segurança
            document.getElementById('loginEmail').value = '';
            document.getElementById('loginSenha').value = '';

            // AGORA: chama /me para obter dados do usuário logado
            await processarLogin();
        } else {
            msgDiv.textContent = '❌ ' + data.erro;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
            msgDiv.classList.remove('hidden');
        }
    } catch (erro) {
        msgDiv.textContent = '❌ Erro na conexão';
        msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
        msgDiv.classList.remove('hidden');
    }
});

/**
 * Processa o login após autenticação bem-sucedida
 * Chama /me para determinar se é admin ou usuário comum
 */
async function processarLogin() {
    try {
        const meResponse = await fetch('/me', {
            credentials: 'include'
        });
        const meData = await meResponse.json();

        if (meData.sucesso) {
            // Define o nome do usuário logado
            document.getElementById('nomeUsuarioSpan').textContent = meData.nome;

            if (meData.is_admin) {
                // É admin - mostra botão admin e vai direto para aba admin
                document.getElementById('btnAdmin').classList.remove('hidden');
                document.getElementById('btnHistorico').classList.add('hidden');
                mostrarDashboard();
                mostrarAba('admin');
            } else {
                // Usuário comum - mostra botão histórico
                document.getElementById('btnAdmin').classList.add('hidden');
                document.getElementById('btnHistorico').classList.remove('hidden');
                mostrarDashboard();
                // Carrega histórico ao fazer login (usuário comum)
                carregarHistorico();
                // Pequeno delay para garantir que a aba foi exibida
                setTimeout(() => {
                    // Mostra aba Acionar Serviço por padrão para usuário comum
                    mostrarAba('acionarServico');
                    // Também carrega a ficha médica em background para estar pronta
                    carregarFichaMedica();
                }, 100);
            }
        } else {
            mostrarLogin();
        }
    } catch (erro) {
        console.error('Erro ao processar login:', erro);
        mostrarLogin();
    }
}

/**
 * Faz cadastro de novo usuário
 */
document.getElementById('formCadastro').addEventListener('submit', async (e) => {
    e.preventDefault();

    const dados = {
        nome: document.getElementById('cadastroNome').value,
        cpf: document.getElementById('cadastroCpf').value,
        data_nascimento: document.getElementById('cadastroDataNascimento').value,
        genero: document.getElementById('cadastroGenero').value,
        telefone_principal: document.getElementById('cadastroTelefone1').value,
        telefone_alternativo: document.getElementById('cadastroTelefone2').value,
        // Endereço detalhado
        estado: document.getElementById('cadastroEstado').value,
        municipio: document.getElementById('cadastroMunicipio').value,
        cep: document.getElementById('cadastroCep').value,
        rua: document.getElementById('cadastroRua').value,
        numero: document.getElementById('cadastroNumero').value,
        bairro: document.getElementById('cadastroBairro').value,
        complemento: document.getElementById('cadastroComplemento').value,
        // Campos legacy para compatibilidade
        endereco: '', // Será preenchido pelo backend
        email: document.getElementById('cadastroEmail').value,
        email_confirmacao: document.getElementById('cadastroEmailConfirmacao').value,
        senha: document.getElementById('cadastroSenha').value,
        senha_confirmacao: document.getElementById('cadastroSenhaConfirmacao').value,
        lgpd_consentimento: document.getElementById('cadastroLGPD').checked
    };

    const msgDiv = document.getElementById('mensagemCadastro');

    try {
        const response = await fetch('/cadastro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (data.sucesso) {
            msgDiv.textContent = '✅ ' + data.mensagem;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-green-700 bg-green-100';
            msgDiv.classList.remove('hidden');

            setTimeout(() => {
                document.getElementById('formCadastro').reset();
                mostrarLogin();
            }, 1500);
        } else {
            msgDiv.textContent = '❌ ' + data.erro;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
            msgDiv.classList.remove('hidden');
        }
    } catch (erro) {
        msgDiv.textContent = '❌ Erro na conexão';
        msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
        msgDiv.classList.remove('hidden');
    }
});

/**
 * Faz logout
 */
function logout() {
    // Remove o token persistente para evitar auto-login após logout explícito
    localStorage.removeItem('auth_token');
    authState.logado = false;
    authState.tokenPresente = false;
    window.location.href = '/logout';
}

// ============================================================================
// ENDEREÇO INTELIGENTE (IBGE + ViaCEP)
// ============================================================================

/**
 * Carrega todos os estados do Brasil ao iniciar o formulário de cadastro
 */
async function carregarEstados() {
    const estadoSelect = document.getElementById('cadastroEstado');
    
    try {
        const response = await fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados');
        const estados = await response.json();

        // Ordena por nome
        estados.sort((a, b) => a.nome.localeCompare(b.nome));

        // Popula o select
        estadoSelect.innerHTML = '<option value="">Selecione o Estado</option>';
        
        estados.forEach(estado => {
            const option = document.createElement('option');
            option.value = estado.sigla;
            option.textContent = `${estado.sigla} - ${estado.nome}`;
            option.dataset.nome = estado.nome;
            estadoSelect.appendChild(option);
        });

        // Adiciona evento de busca por texto
        estadoSelect.addEventListener('input', function() {
            const termo = this.value.toLowerCase();
            if (termo.length >= 2) {
                // Busca por sigla ou nome
                Array.from(this.options).forEach(option => {
                    if (option.value && option.textContent.toLowerCase().includes(termo)) {
                        option.style.display = '';
                    } else if (option.value) {
                        option.style.display = 'none';
                    }
                });
            } else {
                // Restaura todas as opções visíveis
                Array.from(this.options).forEach(option => {
                    option.style.display = '';
                });
            }
        });

    } catch (erro) {
        console.error('Erro ao carregar estados:', erro);
        estadoSelect.innerHTML = '<option value="">Erro ao carregar estados</option>';
    }
}

/**
 * Carrega os municípios do estado selecionado
 */
async function carregarMunicipios(uf) {
    const municipioSelect = document.getElementById('cadastroMunicipio');
    
    if (!uf) {
        municipioSelect.innerHTML = '<option value="">Selecione o estado primeiro</option>';
        return;
    }

    municipioSelect.innerHTML = '<option value="">Carregando municípios...</option>';

    try {
        const response = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf}/municipios`);
        const municipios = await response.json();

        // Ordena por nome
        municipios.sort((a, b) => a.nome.localeCompare(b.nome));

        // Popula o select
        municipioSelect.innerHTML = '<option value="">Selecione o Município</option>';
        
        municipios.forEach(municipio => {
            const option = document.createElement('option');
            option.value = municipio.nome;
            option.textContent = municipio.nome;
            municipioSelect.appendChild(option);
        });

    } catch (erro) {
        console.error('Erro ao carregar municípios:', erro);
        municipioSelect.innerHTML = '<option value="">Erro ao carregar municípios</option>';
    }
}

/**
 * Busca endereço pelo CEP usando a API do ViaCEP
 */
async function buscarCep() {
    const cepInput = document.getElementById('cadastroCep');
    const statusDiv = document.getElementById('cepStatus');
    
    // Limpa o CEP (remove máscara)
    let cep = cepInput.value.replace(/\D/g, '');
    
    if (cep.length !== 8) {
        statusDiv.textContent = '⚠️ CEP inválido. Digite 8 dígitos.';
        statusDiv.className = 'text-xs text-red-600 mt-1';
        return;
    }

    statusDiv.textContent = '🔍 Buscando CEP...';
    statusDiv.className = 'text-xs text-blue-600 mt-1';

    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();

        if (data.erro) {
            statusDiv.textContent = '⚠️ CEP não encontrado. Preencha manualmente.';
            statusDiv.className = 'text-xs text-orange-600 mt-1';
            return;
        }

        // Preenche os campos automaticamente
        // Estado
        const estadoSelect = document.getElementById('cadastroEstado');
        const estadoEncontrado = Array.from(estadoSelect.options).find(
            option => option.value.toUpperCase() === data.uf
        );
        if (estadoEncontrado) {
            estadoSelect.value = data.uf;
            // Carrega municípios do estado encontrado
            await carregarMunicipios(data.uf);
        }

        // Município (pode demorar um pouco para carregar)
        setTimeout(() => {
            const municipioSelect = document.getElementById('cadastroMunicipio');
            const municipioEncontrado = Array.from(municipioSelect.options).find(
                option => option.value.toLowerCase() === data.localidade.toLowerCase()
            );
            if (municipioEncontrado) {
                municipioSelect.value = municipioEncontrado.value;
            } else {
                // Se não encontrar na lista, permite seleção manual
                municipioSelect.value = data.localidade;
            }
        }, 500);

        // Rua
        document.getElementById('cadastroRua').value = data.logradouro || '';
        
        // Bairro
        document.getElementById('cadastroBairro').value = data.bairro || '';
        
        // Complemento
        document.getElementById('cadastroComplemento').value = data.complemento || '';

        statusDiv.textContent = '✅ CEP encontrado! Endereço preenchido automaticamente.';
        statusDiv.className = 'text-xs text-green-600 mt-1';

    } catch (erro) {
        console.error('Erro ao buscar CEP:', erro);
        statusDiv.textContent = '⚠️ Erro ao buscar CEP. Preencha manualmente.';
        statusDiv.className = 'text-xs text-red-600 mt-1';
    }
}

/**
 * Formata o CEP enquanto o usuário digita
 */
function formatarCep(input) {
    let valor = input.value.replace(/\D/g, '');
    if (valor.length > 5) {
        valor = valor.slice(0, 5) + '-' + valor.slice(5, 8);
    }
    input.value = valor;
}

// Adiciona listener para formatar CEP automaticamente
document.addEventListener('DOMContentLoaded', function() {
    const cepInput = document.getElementById('cadastroCep');
    if (cepInput) {
        cepInput.addEventListener('input', function() {
            formatarCep(this);
        });

        // Busca automática ao digitar 8 dígitos
        cepInput.addEventListener('blur', function() {
            const cep = this.value.replace(/\D/g, '');
            if (cep.length === 8) {
                buscarCep();
            }
        });
    }

    // Carrega estados quando a tela de cadastro for mostrada
    const originalMostrarCadastro = window.mostrarCadastro;
    window.mostrarCadastro = function() {
        originalMostrarCadastro();
        carregarEstados();
    };
});

// Adiciona evento ao selecionar estado
document.addEventListener('DOMContentLoaded', function() {
    const estadoSelect = document.getElementById('cadastroEstado');
    if (estadoSelect) {
        estadoSelect.addEventListener('change', function() {
            carregarMunicipios(this.value);
        });
    }
});

// ============================================================================
// DENÚNCIA (com suporte a upload de imagem)
// ============================================================================

/**
 * Submete uma denúncia com texto e/ou imagem
 */
document.getElementById('formDenuncia').addEventListener('submit', async (e) => {
    e.preventDefault();

    const descricao = document.getElementById('denunciaTexto').value;
    const fileInput = document.getElementById('denunciaFoto');
    const msgDiv = document.getElementById('mensagemDenuncia');

    // Validação de texto (mínimo 10 caracteres)
    if (!descricao || descricao.trim().length < 10) {
        msgDiv.textContent = '❌ Denúncia deve ter pelo menos 10 caracteres';
        msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
        msgDiv.classList.remove('hidden');
        return;
    }

    // Cria FormData para enviar texto + arquivo
    const formData = new FormData();
    formData.append('descricao', descricao);
    
    // Adiciona foto se selecionada
    if (fileInput.files.length > 0) {
        formData.append('foto', fileInput.files[0]);
    }

    try {
        const response = await fetch('/denuncia', {
            method: 'POST',
            credentials: 'include',
            body: formData
            // Não define Content-Type - o navegador define automaticamente com boundary
        });

        const data = await response.json();

        if (data.sucesso) {
            msgDiv.textContent = '✅ ' + data.mensagem;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-green-700 bg-green-100';
            msgDiv.classList.remove('hidden');

            // Limpa campos
            document.getElementById('denunciaTexto').value = '';
            removerFoto();
            
            setTimeout(() => msgDiv.classList.add('hidden'), 3000);
        } else {
            msgDiv.textContent = '❌ ' + data.erro;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
            msgDiv.classList.remove('hidden');
        }
    } catch (erro) {
        msgDiv.textContent = '❌ Erro ao enviar denúncia';
        msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
        msgDiv.classList.remove('hidden');
    }
});

/**
 * Preview da imagem selecionada
 */
document.getElementById('denunciaFoto').addEventListener('change', function(e) {
    if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImg').src = e.target.result;
            document.getElementById('previewFoto').classList.remove('hidden');
        };
        reader.readAsDataURL(this.files[0]);
    }
});

/**
 * Remove a foto selecionada
 */
function removerFoto() {
    const fileInput = document.getElementById('denunciaFoto');
    const previewDiv = document.getElementById('previewFoto');
    
    fileInput.value = ''; // Limpa o input
    previewDiv.classList.add('hidden');
    document.getElementById('previewImg').src = '';
}

// ============================================================================
// ACIONAMENTO DE SERVIÇOS
// ============================================================================

/**
 * Aciona um serviço de emergência com geolocalização
 */
function acionarServico(servico) {
    const statusDiv = document.getElementById('statusGeolocation');
    const msgDiv = document.getElementById('mensagemServico');

    // Evita múltiplos cliques simultâneos
    if (window.servicoEmAndamento) {
        statusDiv.textContent = '⏳ Aguarde o acionamento anterior...';
        return;
    }
    window.servicoEmAndamento = true;

    statusDiv.textContent = '📍 Capturando localização...';

    // Tenta obter geolocalização
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                statusDiv.textContent = `📍 Localização: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;

                // Envia para o backend
                try {
                    const response = await fetch('/servico', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                            servico,
                            latitude,
                            longitude
                        })
                    });

                    const data = await response.json();

                    if (data.sucesso) {
                        // =====================================================================
                        // FUNCIONALIDADE 2: MOSTRAR LOCALIZAÇÃO NA TELA
                        // =====================================================================
                        let mensagemLocalizacao = '';
                        if (data.cidade && data.estado && data.cidade !== 'Não identificado' && data.estado !== 'Não identificado') {
                            mensagemLocalizacao = ` Localização: ${data.cidade} - ${data.estado}`;
                        } else {
                            mensagemLocalizacao = ' Localização: Não identificada';
                        }
                        
                        msgDiv.textContent = '✅ ' + data.mensagem + mensagemLocalizacao;
                        msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-green-700 bg-green-100';
                        msgDiv.classList.remove('hidden');
                    } else {
                        msgDiv.textContent = '❌ ' + data.erro;
                        msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
                        msgDiv.classList.remove('hidden');
                    }
                    
                    // Libera flag anti-duplicação
                    window.servicoEmAndamento = false;
                } catch (erro) {
                    msgDiv.textContent = '❌ Erro ao acionar serviço';
                    msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
                    msgDiv.classList.remove('hidden');
                    
                    // Libera flag anti-duplicação
                    window.servicoEmAndamento = false;
                }
            },
            (erro) => {
                // Erro ao obter localização - envia mesmo assim
                console.log('Erro de geolocalização:', erro);
                statusDiv.textContent = '⚠️ Localização não disponível - enviando mesmo assim...';

                enviarServicoSemGeo(servico, msgDiv);
            }
        );
    } else {
        statusDiv.textContent = '⚠️ Navegador não suporta geolocalização';
        enviarServicoSemGeo(servico, msgDiv);
    }
}

/**
 * Envia o acionamento de serviço sem geolocalização
 */
async function enviarServicoSemGeo(servico, msgDiv) {
    try {
        const response = await fetch('/servico', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                servico,
                latitude: null,
                longitude: null
            })
        });

        const data = await response.json();

        if (data.sucesso) {
            msgDiv.textContent = '✅ ' + data.mensagem;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-green-700 bg-green-100';
            msgDiv.classList.remove('hidden');
        } else {
            msgDiv.textContent = '❌ ' + data.erro;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
            msgDiv.classList.remove('hidden');
        }
        
        // Libera flag anti-duplicação
        window.servicoEmAndamento = false;
    } catch (erro) {
        msgDiv.textContent = '❌ Erro ao acionar serviço';
        msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
        msgDiv.classList.remove('hidden');
        
        // Libera flag anti-duplicação
        window.servicoEmAndamento = false;
    }
}

// ============================================================================
// HISTÓRICO
// ============================================================================

/**
 * Carrega o histórico do usuário
 */
async function carregarHistorico() {
    try {
        const response = await fetch('/historico', {
            credentials: 'include'
        });
        
        // Verifica se a resposta é válida antes de parsear JSON
        if (!response.ok) {
            console.error('Erro HTTP:', response.status, response.statusText);
            return;
        }
        
        const data = await response.json();

        if (data.sucesso) {
            // Preenche denúncias
            const listaDenuncias = document.getElementById('listaDenuncias');
            if (data.denuncias.length > 0) {
                listaDenuncias.innerHTML = data.denuncias.map(d => `
                    <div class="bg-gray-100 p-4 rounded-lg border-l-4 border-blue-600">
                        <p class="font-semibold text-gray-800">${d.descricao}</p>
                        ${d.foto ? `<img src="/uploads/${d.foto}" class="mt-2 max-h-32 rounded-lg" alt="Evidência">` : ''}
                        <p class="text-sm text-gray-600 mt-2">📅 ${new Date(d.data).toLocaleString('pt-BR')}</p>
                    </div>
                `).join('');
            } else {
                listaDenuncias.innerHTML = '<p class="text-gray-500">Nenhuma denúncia registrada</p>';
            }

            // Preenche serviços acionados
            const listaServicos = document.getElementById('listaServicos');
            if (data.servicos.length > 0) {
                listaServicos.innerHTML = data.servicos.map(s => {
                    const icon = {
                        'Polícia': '🚔',
                        'SAMU': '🚑',
                        'Bombeiros': '🚒',
                        'Defesa Civil': '🛡️'
                    }[s.tipo] || '📍';

                    return `
                        <div class="bg-gray-100 p-4 rounded-lg border-l-4 border-green-600">
                            <p class="font-semibold text-gray-800">${icon} ${s.tipo}</p>
                            <p class="text-sm text-gray-600 mt-2">
                                📍 Localização: ${
                                    (s.rua || s.bairro || s.cidade || s.estado) 
                                        ? [
                                            s.rua,
                                            s.bairro,
                                            s.cidade && s.estado ? `${s.cidade} - ${s.estado}` : (s.cidade || s.estado),
                                            s.cep ? `CEP: ${s.cep}` : null
                                        ].filter(Boolean).join(', ')
                                        : (s.latitude && s.longitude ? `${s.latitude.toFixed(4)}, ${s.longitude.toFixed(4)}` : 'Não capturada')
                                }
                            </p>
                            <p class="text-sm text-gray-600">🕐 ${new Date(s.data).toLocaleString('pt-BR')}</p>
                        </div>
                    `;
                }).join('');
            } else {
                listaServicos.innerHTML = '<p class="text-gray-500">Nenhum serviço acionado</p>';
            }
        } else {
            console.error('Erro ao carregar histórico:', data.erro);
        }
    } catch (erro) {
        console.error('Erro na requisição de histórico:', erro);
    }
}

// ============================================================================
// ADMIN
// ============================================================================

/**
 * Carrega os dados do painel administrativo
 */
async function carregarAdmin() {
    console.log('🔄 Carregando dados do admin...');
    
    try {
        const response = await fetch('/admin/dados', {
            credentials: 'include'
        });
        
        // Verifica se a resposta é válida antes de parsear JSON
        if (!response.ok) {
            console.error('Erro HTTP:', response.status, response.statusText);
            alert('Erro ao carregar dados admin: ' + response.status);
            return;
        }
        
        const data = await response.json();
        
        // DEBUG: Log dos dados recebidos do admin
        console.log('📥 Dados recebidos do admin:', data);
        console.log('📊 Estatísticas:', data.estatisticas);
        console.log('🩸 Primeiro serviço - tipo sanguíneo:', data.servicos.length > 0 ? data.servicos[0].ficha_tipo_sanguineo : 'N/A');

        if (data.sucesso) {
            // USA DADOS DO ADMIN LOGADO (não da lista de serviços)
            if (data.usuario && data.usuario.nome) {
                document.getElementById('nomeUsuarioSpan').textContent = data.usuario.nome;
            }

            // Atualiza estatísticas
            document.getElementById('totalDenuncias').textContent = data.estatisticas.total_denuncias;
            document.getElementById('totalServicos').textContent = data.estatisticas.total_servicos;
            document.getElementById('totalUsuarios').textContent = data.estatisticas.total_usuarios;

            // Preenche denúncias de todos os usuários
            const listaAdminDenuncias = document.getElementById('listaAdminDenuncias');
            if (data.denuncias.length > 0) {
                listaAdminDenuncias.innerHTML = data.denuncias.filter(d => !d.finalizado).map(d => `
                    <div class="bg-red-50 p-4 rounded-lg border-l-4 border-red-600">
                        <p class="font-semibold text-gray-800">${d.descricao}</p>
                        ${d.foto ? `<img src="/uploads/${d.foto}" class="mt-2 max-h-40 rounded-lg cursor-pointer" alt="Evidência" onclick="window.open('/uploads/${d.foto}', '_blank')">` : ''}
                        <p class="text-sm text-gray-600 mt-2">👤 Usuário: <span class="font-semibold">${d.usuario_nome}</span> (${d.usuario_email})</p>
                        <p class="text-sm text-gray-600">📍 Endereço: ${d.usuario_endereco || 'Não cadastrado'}</p>
                        <p class="text-sm text-gray-600">📅 ${new Date(d.data).toLocaleString('pt-BR')}</p>
                        <div class="mt-2 flex gap-2">
                            ${d.usuario_telefone ? `<button onclick="enviarWhatsApp('${d.usuario_telefone}', '${d.usuario_nome}')" class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-lg text-sm">📲 WhatsApp</button>` : ''}
                            <button onclick="finalizarDenuncia(${d.id})" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-lg text-sm">✔ Finalizar</button>
                        </div>
                    </div>
                `).join('');
            } else {
                listaAdminDenuncias.innerHTML = '<p class="text-gray-500">Nenhuma denúncia registrada no sistema</p>';
            }

            // Preenche serviços de todos os usuários
            const listaAdminServicos = document.getElementById('listaAdminServicos');
            const servicosAtivos = data.servicos.filter(s => !s.finalizado);
            if (servicosAtivos.length > 0) {
                listaAdminServicos.innerHTML = servicosAtivos.map(s => {
                    const icon = {
                        'Polícia': '🚔',
                        'SAMU': '🚑',
                        'Bombeiros': '🚒',
                        'Defesa Civil': '🛡️'
                    }[s.tipo] || '📍';
                    const colorClass = {
                        'Polícia': 'border-blue-600',
                        'SAMU': 'border-yellow-600',
                        'Bombeiros': 'border-orange-600',
                        'Defesa Civil': 'border-purple-600'
                    }[s.tipo] || 'border-green-600';

                    // Formata localização completa
                    const localizacao = s.latitude && s.longitude 
                        ? `${s.latitude.toFixed(4)}, ${s.longitude.toFixed(4)}` 
                        : 'Não capturada';
                    
                    // Exibe endereço completo se disponível
                    const localizacaoExibir = (s.rua || s.bairro || s.cidade || s.estado) 
                        ? [
                            s.rua,
                            s.bairro,
                            s.cidade && s.estado ? `${s.cidade} - ${s.estado}` : (s.cidade || s.estado),
                            s.cep ? `CEP: ${s.cep}` : null
                        ].filter(Boolean).join(', ')
                        : localizacao;

                    // =====================================================================
                    // DADOS DA FICHA MÉDICA - COMPARAÇÃO ATUAL VS SNAPSHOT
                    // =====================================================================
                    
                    // Status da ficha baseado na comparação de campos
                    let fichaStatusBadge = '';
                    let statusCor = '';
                    
                    if (s.ficha_status === 'atualizada') {
                        fichaStatusBadge = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">🟢 Ficha atualizada</span>';
                        statusCor = 'border-green-600';
                    } else if (s.ficha_status === 'alterada') {
                        fichaStatusBadge = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800">🟡 Ficha alterada depois do chamado</span>';
                        statusCor = 'border-yellow-600';
                    } else {
                        fichaStatusBadge = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">🔴 Sem ficha</span>';
                        statusCor = 'border-red-600';
                    }

                    // Dados ATUAIS da ficha (de ficha_medica)
                    const atual = s.ficha_atual || {};
                    const snapshot = s.ficha_snapshot || {};
                    
                    // Dados atuais
                    const tipoSanguineoAtual = atual.tipo_sanguineo || '-';
                    const alergiasAtual = atual.alergias || '-';
                    const doencasAtual = atual.doencas || '-';
                    const medicamentosAtual = atual.medicamentos || '-';
                    const contatoNomeAtual = atual.contato_nome || '-';
                    const contatoTelefoneAtual = atual.contato_telefone || '-';
                    
                    // Snapshot (dados no momento do acionamento)
                    const tipoSanguineoSnapshot = snapshot.ficha_tipo_sanguineo || '-';
                    const alergiasSnapshot = snapshot.ficha_alergias || '-';
                    const doencasSnapshot = snapshot.ficha_doencas || '-';
                    const medicamentosSnapshot = snapshot.ficha_medicamentos || '-';
                    const contatoNomeSnapshot = snapshot.ficha_contato_nome || '-';
                    const contatoTelefoneSnapshot = snapshot.ficha_contato_telefone || '-';
                    
                    // Formatar datas
                    const fichaDataFormatada = s.ficha_atualizado_em 
                        ? new Date(s.ficha_atualizado_em).toLocaleDateString('pt-BR')
                        : 'Não informada';
                    const servicoDataFormatada = new Date(s.data).toLocaleString('pt-BR');

                    // Se não tiver ficha médica
                    const fichaHtml = (s.ficha_status === 'sem_ficha')
                        ? `<div class="mt-3 p-3 bg-yellow-50 border border-yellow-300 rounded-lg">
                            <p class="text-sm text-yellow-800">⚠️ Usuário sem ficha médica cadastrada</p>
                           </div>`
                        : `<div class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <div class="grid grid-cols-2 gap-2 text-sm">
                                <div><span class="font-semibold">🩺 Tipo sanguíneo:</span> ${tipoSanguineoAtual}</div>
                                <div><span class="font-semibold">⚠️ Alergias:</span> ${alergiasAtual}</div>
                                <div><span class="font-semibold">💊 Medicamentos:</span> ${medicamentosAtual}</div>
                                <div><span class="font-semibold">🏥 Doenças:</span> ${doencasAtual}</div>
                                <div><span class="font-semibold">👤 Contato emergência:</span> ${contatoNomeAtual}</div>
                                <div><span class="font-semibold">📞 Telefone:</span> ${contatoTelefoneAtual}</div>
                            </div>
                            <div class="mt-2 pt-2 border-t border-blue-200 flex justify-between items-center text-xs">
                                <span class="text-gray-600">📅 Ficha atualizada em: ${fichaDataFormatada}</span>
                                <span class="text-gray-600">🚑 Emergência em: ${servicoDataFormatada}</span>
                            </div>
                            <div class="mt-2">${fichaStatusBadge}</div>
                           </div>`;

                    return `
                        <div class="bg-green-50 p-4 rounded-lg border-l-4 ${colorClass}">
                            <p class="font-semibold text-gray-800">${icon} ${s.tipo}</p>
                            <p class="text-sm text-gray-600 mt-2">👤 Usuário: <span class="font-semibold">${s.usuario_nome}</span> (${s.usuario_email})</p>
                            <p class="text-sm text-gray-600">📍 Endereço: ${s.usuario_endereco || 'Não cadastrado'}</p>
                            <p class="text-sm text-gray-600">📍 Localização: ${localizacaoExibir}</p>
                            <p class="text-sm text-gray-600">🕐 ${servicoDataFormatada}</p>
                            ${fichaHtml}
                            <div class="mt-2 flex gap-2">
                                ${s.usuario_telefone ? `<button onclick="enviarWhatsApp('${s.usuario_telefone}', '${s.usuario_nome}')" class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-lg text-sm">📲 WhatsApp</button>` : ''}
                                <button onclick="finalizarServico(${s.id})" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-lg text-sm">✔ Finalizar</button>
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                listaAdminServicos.innerHTML = '<p class="text-gray-500">Nenhum serviço ativo no sistema</p>';
            }
        } else {
            alert('Erro ao carregar dados admin: ' + data.erro);
        }
    } catch (erro) {
        console.error('Erro na requisição admin:', erro);
        alert('Erro na conexão com o servidor');
    }
}

// ============================================================================
// FICHA MÉDICA
// ============================================================================

/**
 * Carrega a ficha médica do usuário logado
 */
async function carregarFichaMedica() {
    try {
        const response = await fetch('/ficha-medica', {
            credentials: 'include'
        });
        
        // Verifica se a resposta é válida antes de parsear JSON
        if (!response.ok) {
            console.error('Erro HTTP:', response.status, response.statusText);
            return;
        }
        
        const data = await response.json();

        const formDiv = document.getElementById('formFichaMedica');
        const visualizacaoDiv = document.getElementById('fichaVisualizacao');
        const msgDiv = document.getElementById('mensagemFicha');

        // Esconde mensagens anteriores
        msgDiv.classList.add('hidden');

        if (data.sucesso && data.ficha) {
            // Já tem ficha - mostra modo visualização
            formDiv.classList.add('hidden');
            visualizacaoDiv.classList.remove('hidden');

            // Preenche os dados na visualização
            document.getElementById('fichaTipoSanguineoDisplay').textContent = data.ficha.tipo_sanguineo || '-';
            document.getElementById('fichaAlergias').textContent = data.ficha.alergias || '-';
            document.getElementById('fichaDoencas').textContent = data.ficha.doencas || '-';
            document.getElementById('fichaMedicamentos').textContent = data.ficha.medicamentos || '-';
            document.getElementById('fichaContatoNome').textContent = data.ficha.contato_nome || '-';
            document.getElementById('fichaContatoTelefone').textContent = data.ficha.contato_telefone || '-';
            
            // =====================================================================
            // CORREÇÃO: Exibir data atualizada corretamente
            // =====================================================================
            const dataAtualizacao = data.ficha.atualizado_em 
                ? new Date(data.ficha.atualizado_em).toLocaleString('pt-BR')
                : 'Não informada';
            document.getElementById('fichaDataAtualizacao').textContent = dataAtualizacao;
            
            // DEBUG: Log dos dados recebidos
            console.log('📥 Dados recebidos do backend (ficha médica):', data.ficha);
            console.log('🩸 Tipo sanguíneo:', data.ficha.tipo_sanguineo);
            console.log('📅 Data atualização:', dataAtualizacao);
            
            const obsContainer = document.getElementById('fichaObservacoesContainer');
            const obsText = document.getElementById('fichaObservacoes');
            if (data.ficha.observacoes) {
                obsText.textContent = data.ficha.observacoes;
                obsContainer.classList.remove('hidden');
            } else {
                obsContainer.classList.add('hidden');
            }
        } else {
            // Não tem ficha - mostra formulário vazio
            formDiv.classList.remove('hidden');
            visualizacaoDiv.classList.add('hidden');
            
            // Limpa o formulário
            document.getElementById('fichaTipoSanguineoInput').value = '';
            document.getElementById('fichaAlergiasInput').value = '';
            document.getElementById('fichaDoencasInput').value = '';
            document.getElementById('fichaMedicamentosInput').value = '';
            document.getElementById('fichaContatoNomeInput').value = '';
            document.getElementById('fichaContatoTelefoneInput').value = '';
            document.getElementById('fichaObservacoesInput').value = '';
            
            // DEBUG: Log quando não tem ficha
            console.log('ℹ️ Usuário sem ficha médica cadastrada');
            
            // Esconde botão cancelar se estiver visível
            document.getElementById('btnCancelarEdicao').classList.add('hidden');
        }
    } catch (erro) {
        console.error('Erro ao carregar ficha médica:', erro);
    }
}

/**
 * Ativa o modo de edição da ficha médica
 */
function editarFicha() {
    const formDiv = document.getElementById('formFichaMedica');
    const visualizacaoDiv = document.getElementById('fichaVisualizacao');
    const btnCancelar = document.getElementById('btnCancelarEdicao');

    // Primeiro carrega os dados atuais no formulário
    carregarDadosFormulario();

    // Mostra formulário e esconde visualização
    visualizacaoDiv.classList.add('hidden');
    formDiv.classList.remove('hidden');
    btnCancelar.classList.remove('hidden');
}

/**
 * Carrega os dados da ficha para o formulário (modo edição)
 */
function carregarDadosFormulario() {
    fetch('/ficha-medica', {
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso && data.ficha) {
            document.getElementById('fichaTipoSanguineoInput').value = data.ficha.tipo_sanguineo || '';
            document.getElementById('fichaAlergiasInput').value = data.ficha.alergias || '';
            document.getElementById('fichaDoencasInput').value = data.ficha.doencas || '';
            document.getElementById('fichaMedicamentosInput').value = data.ficha.medicamentos || '';
            document.getElementById('fichaContatoNomeInput').value = data.ficha.contato_nome || '';
            document.getElementById('fichaContatoTelefoneInput').value = data.ficha.contato_telefone || '';
            document.getElementById('fichaObservacoesInput').value = data.ficha.observacoes || '';
            
            // DEBUG: Log dos dados carregados no formulário
            console.log('📝 Dados carregados no formulário de edição:', data.ficha);
        }
    })
    .catch(erro => {
        console.error('Erro ao carregar dados para edição:', erro);
    });
}

/**
 * Recarrega os dados da ficha médica E atualiza a interface imediatamente
 * Resolve o problema da data não atualizar
 */
async function carregarDadosFichaMedicaEAtualizarInterface() {
    try {
        const response = await fetch('/ficha-medica', {
            credentials: 'include'
        });
        const data = await response.json();

        const formDiv = document.getElementById('formFichaMedica');
        const visualizacaoDiv = document.getElementById('fichaVisualizacao');

        if (data.sucesso && data.ficha) {
            // Preenche os dados na visualização
            document.getElementById('fichaTipoSanguineoDisplay').textContent = data.ficha.tipo_sanguineo || '-';
            document.getElementById('fichaAlergias').textContent = data.ficha.alergias || '-';
            document.getElementById('fichaDoencas').textContent = data.ficha.doencas || '-';
            document.getElementById('fichaMedicamentos').textContent = data.ficha.medicamentos || '-';
            document.getElementById('fichaContatoNome').textContent = data.ficha.contato_nome || '-';
            document.getElementById('fichaContatoTelefone').textContent = data.ficha.contato_telefone || '-';
            
            // =====================================================================
            // CORREÇÃO: Formatar data no padrão brasileiro (dd/mm/yyyy)
            // =====================================================================
            const dataAtualizacao = data.ficha.atualizado_em 
                ? new Date(data.ficha.atualizado_em).toLocaleString('pt-BR')
                : 'Não informada';
            document.getElementById('fichaDataAtualizacao').textContent = dataAtualizacao;
            
            console.log('🔄 Dados atualizados - Data:', dataAtualizacao);

            // Observações
            const obsContainer = document.getElementById('fichaObservacoesContainer');
            const obsText = document.getElementById('fichaObservacoes');
            if (data.ficha.observacoes) {
                obsText.textContent = data.ficha.observacoes;
                obsContainer.classList.remove('hidden');
            } else {
                obsContainer.classList.add('hidden');
            }

            // Mostra visualização e esconde formulário
            formDiv.classList.add('hidden');
            visualizacaoDiv.classList.remove('hidden');
            
            // Esconde botão cancelar
            document.getElementById('btnCancelarEdicao').classList.add('hidden');
        }
    } catch (erro) {
        console.error('Erro ao atualizar interface:', erro);
    }
}

/**
 * Verifica se o usuário está logado ao carregar a página
 * Se estiver autenticado, vai direto para o dashboard
 */
async function verificarLoginAoCarregar() {
    try {
        const meResponse = await fetch('/me', {
            credentials: 'include'
        });
        const meData = await meResponse.json();

        if (meData.sucesso) {
            // Usuário está logado - vai direto para dashboard
            document.getElementById('nomeUsuarioSpan').textContent = meData.nome;

            if (meData.is_admin) {
                document.getElementById('btnAdmin').classList.remove('hidden');
                document.getElementById('btnHistorico').classList.add('hidden');
                mostrarDashboard();
                mostrarAba('admin');
            } else {
                document.getElementById('btnAdmin').classList.add('hidden');
                document.getElementById('btnHistorico').classList.remove('hidden');
                mostrarDashboard();
                carregarHistorico();
                setTimeout(() => {
                    mostrarAba('acionarServico');
                    carregarFichaMedica();
                }, 100);
            }
            console.log('✅ Usuário já logado - redirecionado para dashboard');
        } else {
            // Não está logado - mostra tela de login
            mostrarLogin();
            console.log('ℹ️ Usuário não logado - mostrando login');
        }
    } catch (erro) {
        console.error('Erro ao verificar login:', erro);
        mostrarLogin();
    }
}

/**
 * Envia o formulário da ficha médica
 */
document.getElementById('formFichaMedica').addEventListener('submit', async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const dados = {
        tipo_sanguineo: document.getElementById('fichaTipoSanguineoInput').value,
        alergias: document.getElementById('fichaAlergiasInput').value,
        doencas: document.getElementById('fichaDoencasInput').value,
        medicamentos: document.getElementById('fichaMedicamentosInput').value,
        contato_nome: document.getElementById('fichaContatoNomeInput').value,
        contato_telefone: document.getElementById('fichaContatoTelefoneInput').value,
        observacoes: document.getElementById('fichaObservacoesInput').value
    };
    
    // DEBUG: Log dos dados enviados
    console.log('📤 Enviando dados da ficha médica:', dados);

    const msgDiv = document.getElementById('mensagemFicha');

    try {
        const response = await fetch('/ficha-medica', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(dados)
        });

        const data = await response.json();
        console.log('📥 Resposta do servidor:', data);

        if (data.sucesso) {
            msgDiv.textContent = '✅ ' + data.mensagem;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-green-700 bg-green-100';
            msgDiv.classList.remove('hidden');

            // =====================================================================
            // CORREÇÃO: Recarrega dados E atualiza interface imediatamente
            // =====================================================================
            carregarDadosFichaMedicaEAtualizarInterface();
        } else {
            msgDiv.textContent = '❌ ' + data.erro;
            msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
            msgDiv.classList.remove('hidden');
        }
    } catch (erro) {
        console.error('Erro ao salvar ficha:', erro);
        msgDiv.textContent = '❌ Erro na conexão';
        msgDiv.className = 'mt-4 p-3 rounded-lg text-center text-red-700 bg-red-100';
        msgDiv.classList.remove('hidden');
    }
});

/**
 * Verifica se o usuário tem ficha médica antes de acionar serviço
 */
async function verificarFichaAntesEmergencia(servico) {
    try {
        const response = await fetch('/ficha-existe', {
            credentials: 'include'
        });
        const data = await response.json();

        if (data.sucesso && !data.tem_ficha) {
            // Não tem ficha - mostra alerta mas permite continuar
            const confirmar = confirm(
                '⚠️ Recomendamos preencher sua ficha médica antes de acionar emergência.\n\n' +
                'Deseja continuar mesmo assim?'
            );
            if (!confirmar) {
                return false; // Usuário cancelou
            }
        }
        return true; // Pode prosseguir
    } catch (erro) {
        console.error('Erro ao verificar ficha:', erro);
        return true; // Em caso de erro, permite continuar
    }
}

// Modifica a função acionarServico para verificar ficha
const acionarServicoOriginal = window.acionarServico;
window.acionarServico = async function(servico) {
    // Verifica se tem ficha antes de continuar
    const podeContinuar = await verificarFichaAntesEmergencia(servico);
    if (!podeContinuar) {
        return;
    }
    // Chama a função original
    if (acionarServicoOriginal) {
        acionarServicoOriginal(servico);
    }
};

// ============================================================================
// FUNCIONALIDADE WHATSAPP PARA USUÁRIO E ADMIN
// ============================================================================

/**
 * Abre WhatsApp para falar com o atendimento (admin)
 */
function abrirWhatsApp() {
    const mensagem = encodeURIComponent('Olá, sou usuário do sistema de emergência e preciso de atendimento.');
    const link = `https://wa.me/5511999999999?text=${mensagem}`;
    window.open(link, '_blank');
}

/**
 * Abre WhatsApp para admin (mesmo número, mas talvez mensagem diferente)
 */
function abrirWhatsAppAdmin() {
    const mensagem = encodeURIComponent('Olá, sou administrador do sistema de emergência.');
    const link = `https://wa.me/5511999999999?text=${mensagem}`;
    window.open(link, '_blank');
}

// ============================================================================
// FUNCIONALIDADE ABA ADMIN ATIVOS/FINALIZADOS
// ============================================================================

/**
 * Mostra aba específica no admin
 */
function mostrarAdminAba(aba) {
    // Esconde todas as abas admin
    const abas = document.querySelectorAll('.admin-conteudo');
    abas.forEach(a => a.classList.add('hidden'));

    // Remove ativa de todos os botões
    const botoes = document.querySelectorAll('.admin-aba-btn');
    botoes.forEach(btn => btn.classList.remove('bg-blue-600'));
    botoes.forEach(btn => btn.classList.add('bg-gray-400'));

    // Mostra aba selecionada
    document.getElementById('admin' + aba.charAt(0).toUpperCase() + aba.slice(1)).classList.remove('hidden');

    // Ativa botão
    const btn = document.querySelector(`[data-admin-aba="${aba}"]`);
    if (btn) {
        btn.classList.remove('bg-gray-400');
        btn.classList.add('bg-blue-600');
    }

    // Carrega dados se necessário
    if (aba === 'finalizados') {
        carregarAdminFinalizados();
    }
}

/**
 * Carrega dados dos finalizados
 */
async function carregarAdminFinalizados() {
    try {
        const response = await fetch('/admin/dados', {
            credentials: 'include'
        });
        const data = await response.json();

        if (data.sucesso) {
            // Filtra apenas finalizados
            const denunciasFinalizadas = data.denuncias.filter(d => d.finalizado);
            const servicosFinalizados = data.servicos.filter(s => s.finalizado);

            // Renderiza denuncias finalizadas
            const listaDenuncias = document.getElementById('listaAdminDenunciasFinalizadas');
            if (denunciasFinalizadas.length > 0) {
                listaDenuncias.innerHTML = denunciasFinalizadas.map(d => {
                    const dataFormatada = new Date(d.data).toLocaleString('pt-BR');
                    const fotoHtml = d.foto ? `<br><img src="/uploads/${d.foto}" alt="Foto" class="max-w-xs rounded-lg mt-2">` : '';
                    return `
                        <div class="bg-green-50 p-4 rounded-lg border-l-4 border-green-600">
                            <p class="font-semibold text-gray-800">📋 ${d.descricao}</p>
                            <p class="text-sm text-gray-600 mt-2">👤 Usuário: <span class="font-semibold">${d.usuario_nome}</span> (${d.usuario_email})</p>
                            <p class="text-sm text-gray-600">📍 Endereço: ${d.usuario_endereco || 'Não cadastrado'}</p>
                            <p class="text-sm text-gray-600">🕐 ${dataFormatada}</p>
                            ${fotoHtml}
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 mt-2">✔ Finalizada</span>
                        </div>
                    `;
                }).join('');
            } else {
                listaDenuncias.innerHTML = '<p class="text-gray-500">Nenhuma denúncia finalizada</p>';
            }

            // Renderiza servicos finalizados
            const listaServicos = document.getElementById('listaAdminServicosFinalizados');
            if (servicosFinalizados.length > 0) {
                listaServicos.innerHTML = servicosFinalizados.map(s => {
                    const colorClass = s.tipo === 'Polícia' ? 'border-red-600' :
                                     s.tipo === 'SAMU' ? 'border-yellow-600' :
                                     s.tipo === 'Bombeiros' ? 'border-orange-600' : 'border-purple-600';
                    const icon = s.tipo === 'Polícia' ? '🚔' :
                               s.tipo === 'SAMU' ? '🚑' :
                               s.tipo === 'Bombeiros' ? '🚒' : '🛡️';
                    const servicoDataFormatada = new Date(s.data).toLocaleString('pt-BR');

                    return `
                        <div class="bg-green-50 p-4 rounded-lg border-l-4 ${colorClass}">
                            <p class="font-semibold text-gray-800">${icon} ${s.tipo}</p>
                            <p class="text-sm text-gray-600 mt-2">👤 Usuário: <span class="font-semibold">${s.usuario_nome}</span> (${s.usuario_email})</p>
                            <p class="text-sm text-gray-600">📍 Endereço: ${s.usuario_endereco || 'Não cadastrado'}</p>
                            <p class="text-sm text-gray-600">🕐 ${servicoDataFormatada}</p>
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 mt-2">✔ Finalizado</span>
                        </div>
                    `;
                }).join('');
            } else {
                listaServicos.innerHTML = '<p class="text-gray-500">Nenhum serviço finalizado</p>';
            }
        }
    } catch (erro) {
        console.error('Erro ao carregar finalizados:', erro);
    }
}

/**
 * Finaliza uma denúncia
 */
async function finalizarDenuncia(id) {
    if (!confirm('Tem certeza que deseja marcar esta denúncia como finalizada?')) return;

    try {
        const response = await fetch(`/admin/finalizar-denuncia/${id}`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        if (data.sucesso) {
            alert('Denúncia finalizada com sucesso!');
            carregarAdmin();
        } else {
            alert('Erro: ' + data.erro);
        }
    } catch (erro) {
        alert('Erro na conexão');
    }
}

/**
 * Finaliza um serviço
 */
async function finalizarServico(id) {
    if (!confirm('Tem certeza que deseja marcar este serviço como finalizado?')) return;

    try {
        const response = await fetch(`/admin/finalizar-servico/${id}`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        if (data.sucesso) {
            alert('Serviço finalizado com sucesso!');
            carregarAdmin();
        } else {
            alert('Erro: ' + data.erro);
        }
    } catch (erro) {
        alert('Erro na conexão');
    }
}

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

/**
 * Verifica se o usuário está logado ao carregar a página
 * Primeiro tenta login automático com token, depois verifica sessão normal
 */
window.addEventListener('load', async () => {
    try {
        // Sempre mostra a tela de login primeiro. O auto-login só deve ocorrer se houver token persistente.
        mostrarLogin();
        
        const token = localStorage.getItem('auth_token');
        if (!token) {
            console.log('ℹ️ Sem token persistente, exibindo login.');
            return;
        }

        const loginAutomaticoSucesso = await verificarLoginAutomatico();
        if (!loginAutomaticoSucesso) {
            mostrarLogin();
        }
    } catch (erro) {
        console.error('Erro na inicialização:', erro);
        mostrarLogin();
    }
});

