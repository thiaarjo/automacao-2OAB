import time
import sys
import os
import database
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# 1. ARRAYS DE CONFIGURAÇÃO (FLUXOS)
# ==========================================
FLUXOS_AUTOMACAO = [
    {"nome": "Direito Administrativo", "texto_link": "Direito Administrativo - 2ª Fase OAB"},
    {"nome": "Direito Civil", "texto_link": "Direito Civil - 2ª Fase OAB"},
    {"nome": "Direito Constitucional", "texto_link": "Direito Constitucional - 2ª Fase OAB"},
    {"nome": "Direito Empresarial", "texto_link": "Direito Empresarial - 2ª Fase OAB"},
    {"nome": "Direito Penal", "texto_link": "Direito Penal - 2ª Fase OAB"},
    {"nome": "Direito do Trabalho", "texto_link": "Direito do Trabalho - 2ª Fase OAB"},
    {"nome": "Direito Tributário", "texto_link": "Direito Tributário - 2ª Fase OAB"}
]

# Textos indesejados que devem ser filtrados do enunciado e gabarito
TEXTOS_LIXO = [
    "O(A) examinando(a) deve fundamentar suas respostas",
    "A mera citação do dispositivo legal",
    "Qualquer semelhança nominal e/ou situacional",
    "mera coincidência",
    "Descobrir mais",
    "Suco",
    "Resumos Direito",
    "Livros OAB 2ª"
]

URL_BASE = "https://www.jurisway.org.br/provasoab/oab2afase.asp"

# ==========================================
# 2. FUNÇÕES DE INTERFACE DO TERMINAL
# ==========================================
def limpar_terminal():
    """Limpa a tela do terminal para manter a organização."""
    os.system('cls' if os.name == 'nt' else 'clear')

def menu_selecao(lista_opcoes, titulo_menu, chave_exibicao):
    """
    Exibe um menu interativo dinâmico e retorna a opção escolhida.
    """
    print(f"\n{'='*70}")
    print(f"  {titulo_menu}")
    print(f"{'='*70}")
    
    for idx, item in enumerate(lista_opcoes):
        texto = item[chave_exibicao]
        if len(texto) > 60:
            texto = texto[:57] + "..."
        print(f"[{idx + 1:02d}] {texto}")
        
    print(f"[{0:02d}] Sair do Robô")
    print(f"{'='*70}")
    
    while True:
        try:
            opcao = int(input("=> Digite o número da sua escolha: "))
            if opcao == 0:
                print("\n[ENCERRANDO] Robô finalizado pelo usuário.")
                sys.exit()
            if 1 <= opcao <= len(lista_opcoes):
                return lista_opcoes[opcao - 1]
            print("Opção inválida! Tente novamente.")
        except ValueError:
            print("Por favor, digite apenas números.")

def menu_fila(lista_opcoes, titulo_menu, chave_exibicao):
    """
    Exibe o menu e permite selecionar MÚLTIPLAS questões de uma vez.
    Ex: 2,3,4,7 ou 1-5 ou 2,4,6-10
    Retorna uma lista de itens selecionados.
    """
    print(f"\n{'='*70}")
    print(f"  {titulo_menu}")
    print(f"{'='*70}")
    
    for idx, item in enumerate(lista_opcoes):
        texto = item[chave_exibicao]
        if len(texto) > 60:
            texto = texto[:57] + "..."
        print(f"[{idx + 1:02d}] {texto}")
        
    print(f"[{0:02d}] Sair do Robô")
    print(f"{'='*70}")
    print("  DICA: Selecione várias! Ex: 2,3,4,7 ou 1-5 ou digite 'todas'")
    print(f"{'='*70}")
    
    while True:
        entrada = input("=> Digite os números da fila (ou 'todas'): ").strip().lower()
        
        if entrada == "0":
            print("\n[ENCERRANDO] Robô finalizado pelo usuário.")
            sys.exit()
        
        if entrada == "todas":
            return lista_opcoes
        
        # Processar a entrada (aceita: 2,3,4 ou 1-5 ou 2,4,6-10)
        indices = set()
        try:
            partes = entrada.split(",")
            for parte in partes:
                parte = parte.strip()
                if "-" in parte:
                    inicio, fim = parte.split("-")
                    for i in range(int(inicio), int(fim) + 1):
                        indices.add(i)
                else:
                    indices.add(int(parte))
            
            # Validar se todos os índices são válidos
            selecionados = []
            for idx in sorted(indices):
                if 1 <= idx <= len(lista_opcoes):
                    selecionados.append(lista_opcoes[idx - 1])
                else:
                    print(f"[AVISO] Número {idx} fora do intervalo. Ignorado.")
            
            if selecionados:
                return selecionados
            print("Nenhuma opção válida selecionada. Tente novamente.")
        except ValueError:
            print("Formato inválido! Use: 2,3,4 ou 1-5 ou 2,4,6-10")

# ==========================================
# 3. FUNÇÕES DE EXTRAÇÃO DE DADOS (SCRAPING)
# ==========================================
def extrair_exames(driver):
    """
    Varre a pagina usando JavaScript puro para velocidade extrema.
    Retorna arrays agrupados por Exame, incluindo tipo de gabarito.
    """
    script = """
    const exames_mapeados = [];
    const cabecalhos = document.querySelectorAll("#conteudo_total h3");
    
    for (const h3 of cabecalhos) {
        let tituloCompleto = h3.innerText.split('\\n')[0].trim();
        if (!tituloCompleto) continue;
        
        // Detectar tipo de gabarito
        let tipo_gabarito = "desconhecido";
        if (tituloCompleto.toLowerCase().includes("definitivo")) {
            tipo_gabarito = "definitivo";
        } else if (tituloCompleto.toLowerCase().includes("preliminar")) {
            tipo_gabarito = "preliminar";
        }
        
        let lista = h3.nextElementSibling;
        while(lista && lista.tagName !== 'UL' && lista.tagName !== 'H3') {
            lista = lista.nextElementSibling;
        }
        
        if (lista && lista.tagName === 'UL') {
            const links = Array.from(lista.querySelectorAll(':scope > li > a'));
            const questoes = links.map(link => ({
                texto: link.innerText.trim(),
                url: link.href
            }));
            
            if (questoes.length > 0) {
                exames_mapeados.push({
                    titulo: tituloCompleto,
                    tipo_gabarito: tipo_gabarito,
                    questoes: questoes
                });
            }
        }
    }
    return exames_mapeados;
    """
    return driver.execute_script(script)

def extrair_conteudo_discursiva(driver):
    """
    Extrai o conteúdo da questão discursiva separando:
    - Enunciado: tudo (incluindo perguntas A e B) até 'Resposta FGV'
    - Resposta A: texto após 'A)' no Padrão de Resposta
    - Resposta B: texto após 'B)' no Padrão de Resposta
    Filtra textos genéricos indesejados (Obs., coincidência, etc.)
    """
    # Passa os textos lixo como parâmetro para o JS
    textos_lixo_js = TEXTOS_LIXO
    
    script = """
    function extrair(filtros) {
        const contentDiv = document.querySelector("#conteudo_total");
        if (!contentDiv) return {erro: "Conteúdo não encontrado"};
        
        let fase = "ENUNCIADO";
        let enunciado_parts = [];
        let gabarito_parts = [];
        
        const elements = Array.from(contentDiv.children);
        
        for (const el of elements) {
            const tagName = el.tagName.toUpperCase();
            const text = el.innerText ? el.innerText.trim() : "";
            
            // Marcadores de parada global (agora NAO para em Distribuicao)
            if (text.includes("Voltar para lista") || 
                text.includes("Questao Anterior") ||
                text.includes("Questão Anterior") || 
                text.includes("Proxima Questao") ||
                text.includes("Próxima Questão") || 
                text.includes("Achou esta pagina util") ||
                text.includes("Achou esta página útil")) {
                break;
            }
            
            // Pular a secao de Distribuicao (sera extraida separadamente)
            if (text.includes("Distribuicao dos Pontos") || text.includes("Distribuição dos Pontos") || text.includes("Distribuição de Pontos")) {
                continue;
            }
            
            // Pular tabelas (TableGrid sera extraida separadamente)
            if (tagName === 'TABLE') continue;
            
            // Filtrar textos lixo
            let isLixo = false;
            for (const filtro of filtros) {
                if (text.includes(filtro)) {
                    isLixo = true;
                    break;
                }
            }
            if (isLixo) continue;
            
            // Transições de fase
            const isMarker = tagName === 'B' || tagName === 'STRONG' || el.querySelector('b') || el.querySelector('strong');
            if (isMarker) {
                const markerText = el.innerText || "";
                if (markerText.includes("Resposta FGV")) {
                    fase = "ESPERANDO_GABARITO";
                    continue;
                }
                if (markerText.includes("Padrão de Resposta") || markerText.includes("Espelho de Correção")) {
                    fase = "GABARITO";
                    continue;
                }
            }
            
            // Espaçamento: tags vazias viram quebra de linha
            if (text.length === 0) {
                if (tagName === 'BR' || tagName === 'P' || tagName === 'DIV') {
                    if (fase === "ENUNCIADO") enunciado_parts.push("");
                    else if (fase === "GABARITO") gabarito_parts.push("");
                }
                continue;
            }
            
            // Coleta de conteúdo
            if (fase === "ENUNCIADO") {
                if (tagName === 'P' || tagName === 'SPAN' || tagName === 'DIV') {
                    enunciado_parts.push(text);
                }
            } else if (fase === "GABARITO") {
                if (tagName === 'P' || tagName === 'SPAN' || tagName === 'DIV') {
                    if (!text.includes("Para ver a resposta da FGV") && 
                        !text.includes("gabarito preliminar da prova")) {
                        gabarito_parts.push(text);
                    }
                }
            }
        }
        
        // Limpeza de linhas vazias
        function limpar(arr) {
            let txt = arr.join('\\n');
            txt = txt.replace(/^\\n+/, '');
            txt = txt.replace(/\\n+$/, '');
            txt = txt.replace(/\\n{3,}/g, '\\n\\n');
            return txt;
        }
        
        // Separar gabarito em Resposta A e Resposta B
        const gabarito_texto = limpar(gabarito_parts);
        let resposta_a = "";
        let resposta_b = "";
        
        const matchB = gabarito_texto.search(/\\nB\\)|^B\\)/m);
        
        if (matchB !== -1) {
            resposta_a = gabarito_texto.substring(0, matchB).trim();
            resposta_b = gabarito_texto.substring(matchB).trim();
        } else {
            resposta_a = gabarito_texto;
        }
        
        // Remove prefixos A) e B)
        resposta_a = resposta_a.replace(/^A\\)\\s*/, '').trim();
        resposta_b = resposta_b.replace(/^B\\)\\s*/, '').trim();
        
        // Extrair tabela de Distribuicao de Pontos (TableGrid)
        let dist_pontos = "";
        let pontuacao_a = "";
        let pontuacao_b = "";
        const tabela = contentDiv.querySelector("table.TableGrid");
        if (tabela) {
            const linhas = tabela.querySelectorAll("tr");
            const partes = [];
            for (const tr of linhas) {
                const colunas = tr.querySelectorAll("td, th");
                const textos = Array.from(colunas).map(td => td.innerText.trim());
                partes.push(textos.join(" | "));
                
                // Extrair pontuacao por letra
                if (colunas.length >= 2) {
                    const itemText = colunas[0].innerText.trim();
                    const pontoText = colunas[colunas.length - 1].innerText.trim();
                    
                    if (itemText.match(/^A[\\.\\)\\s]/)) {
                        pontuacao_a = pontoText;
                    } else if (itemText.match(/^B[\\.\\)\\s]/)) {
                        pontuacao_b = pontoText;
                    }
                }
            }
            dist_pontos = partes.join('\\n');
        }
        
        return {
            enunciado: limpar(enunciado_parts),
            resposta_a: resposta_a,
            resposta_b: resposta_b,
            pontuacao_a: pontuacao_a,
            pontuacao_b: pontuacao_b,
            distribuicao_pontos: dist_pontos
        };
    }
    return extrair(arguments[0]);
    """
    return driver.execute_script(script, textos_lixo_js)

# ==========================================
# 4. FLUXO PRINCIPAL DA AUTOMAÇÃO
# ==========================================
def iniciar_robo():
    # Inicializa o banco de dados
    database.conectar()
    
    limpar_terminal()
    
    # --- PASSO 1: Escolha da Área ---
    area_escolhida = menu_selecao(FLUXOS_AUTOMACAO, "ROBÔ OAB [DISCURSIVAS] - SELECIONE A ÁREA DO DIREITO", "nome")
    
    print(f"\n[AGUARDE] Abrindo navegador e acessando: {area_escolhida['nome']}...")
    
    driver = None
    
    chrome_options = Options()
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_page_load_timeout(30)  # Máximo 30s para carregar uma página
    driver.set_script_timeout(15)     # Máximo 15s para executar JavaScript
    
    try:
        # Acessa a página principal e clica na área
        driver.get(URL_BASE)
        time.sleep(1)
        elemento_link = driver.find_element(By.PARTIAL_LINK_TEXT, area_escolhida['texto_link'])
        elemento_link.click()
        time.sleep(2)
        
        print("[AGUARDE] Lendo e organizando os exames da página...")
        exames = extrair_exames(driver)
        
        if not exames:
            print("\n[AVISO] Nenhum exame foi encontrado para esta área.")
            return
        
        # Filtrar por tipo de gabarito
        definitivos = [e for e in exames if e.get('tipo_gabarito') == 'definitivo']
        preliminares = [e for e in exames if e.get('tipo_gabarito') == 'preliminar']
        
        print(f"\n[INFO] Encontrados: {len(definitivos)} definitivo(s) | {len(preliminares)} preliminar(es)")
        
        incluir_preliminar = input("=> Incluir exames com gabarito preliminar? (s/N): ").strip().lower()
        
        if incluir_preliminar == 's':
            exames_filtrados = exames
        else:
            exames_filtrados = definitivos if definitivos else exames
            if not definitivos:
                print("[AVISO] Nenhum definitivo encontrado. Mostrando todos.")
            
        limpar_terminal()
        
        # --- PASSO 2: Escolha do Exame ---
        titulo_menu_exames = f"EXAMES DISPONIVEIS - {area_escolhida['nome'].upper()}"
        exames_escolhidos = menu_fila(exames_filtrados, titulo_menu_exames, "titulo")
        
        limpar_terminal()
        
        # --- PASSO 3: Filtrar apenas DISCURSIVAS (SP) e montar fila ---
        todas_questoes = []
        for exame in exames_escolhidos:
            for q in exame["questoes"]:
                if q['texto'].lower().startswith('sp'):
                    q['exame_titulo'] = exame['titulo']
                    q['exibicao'] = f"[{exame['titulo'][:15]}...] {q['texto']}"
                    todas_questoes.append(q)
        
        if not todas_questoes:
            print("\n[AVISO] Nenhuma questão discursiva (SP) encontrada nestes exames.")
            return
        
        titulo_menu_questoes = f"DISCURSIVAS DOS EXAMES SELECIONADOS"
        fila_questoes = menu_fila(todas_questoes, titulo_menu_questoes, "exibicao")
        
        print(f"\n[FILA] {len(fila_questoes)} questão(ões) na fila de extração.")
        print(f"{'='*70}")
        
        # --- PASSO 4: Processar fila sequencialmente ---
        sucesso_count = 0
        erro_count = 0
        pular_count = 0
        
        for i, questao in enumerate(fila_questoes):
            posicao = f"[{i+1}/{len(fila_questoes)}]"
            titulo_curto = questao['texto'][:50] + "..." if len(questao['texto']) > 50 else questao['texto']
            
            # Verifica se já existe no banco antes de acessar a página
            if database.ja_existe(questao['url']):
                pular_count += 1
                print(f"\n{posicao} ⏭ JÁ EXISTE: {titulo_curto}")
                continue
            
            try:
                print(f"\n{posicao} Acessando: {titulo_curto}")
                driver.get(questao['url'])
                time.sleep(3)
                
                print(f"{posicao} Extraindo dados...")
                dados = extrair_conteudo_discursiva(driver)
                
                if dados and isinstance(dados, dict) and "erro" not in dados:
                    dist = dados.get('distribuicao_pontos', '')
                    pont_a = dados.get('pontuacao_a', '')
                    pont_b = dados.get('pontuacao_b', '')
                    sucesso = database.salvar_discursiva(
                        area=area_escolhida['nome'],
                        exame=questao['exame_titulo'],
                        titulo=questao['texto'],
                        url=questao['url'],
                        enunciado=dados['enunciado'],
                        resposta_a=dados['resposta_a'],
                        resposta_b=dados['resposta_b'],
                        pontuacao_a=pont_a,
                        pontuacao_b=pont_b,
                        distribuicao_pontos=dist
                    )
                    if sucesso:
                        sucesso_count += 1
                        pt_info = f" | Pt.A: {pont_a} | Pt.B: {pont_b}" if pont_a else ""
                        print(f"{posicao} Salvo! (Enun: {len(dados['enunciado'])}c | A: {len(dados['resposta_a'])}c | B: {len(dados['resposta_b'])}c{pt_info})")
                    else:
                        erro_count += 1
                        print(f"{posicao} ✗ Erro ao salvar no banco.")
                else:
                    erro_count += 1
                    print(f"{posicao} ✗ Conteúdo não encontrado.")
            except Exception as e:
                erro_count += 1
                print(f"{posicao} ✗ ERRO (pulando): {str(e)[:80]}")
                continue
        
        # Resumo final
        print(f"\n{'='*70}")
        print(f"  FILA CONCLUÍDA!")
        print(f"  ✓ Salvas: {sucesso_count} | ⏭ Já existiam: {pular_count} | ✗ Erros: {erro_count}")
        print(f"{'='*70}")
        
    except KeyboardInterrupt:
        print(f"\n\n[CANCELADO] Automacao interrompida pelo usuario (Ctrl+C).")
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um problema durante a automacao:\n{e}")
    finally:
        print("\n[FINALIZADO] Encerrando navegador...")
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    iniciar_robo()

