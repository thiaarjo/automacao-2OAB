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
        # Limita o tamanho do texto para não quebrar a tela do terminal
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

# ==========================================
# 3. FUNÇÕES DE EXTRAÇÃO DE DADOS (SCRAPING)
# ==========================================
def extrair_exames(driver):
    """
    Varre a página usando JavaScript puro para velocidade extrema.
    Retorna arrays agrupados por Exame.
    """
    script = """
    const exames_mapeados = [];
    const cabecalhos = document.querySelectorAll("#conteudo_total h3");
    
    for (const h3 of cabecalhos) {
        let titulo = h3.innerText.split('\\n')[0].trim();
        if (!titulo) continue;
        
        let lista = h3.nextElementSibling;
        // Pula elementos até achar a lista ou o próximo H3
        while(lista && lista.tagName !== 'UL' && lista.tagName !== 'H3') {
            lista = lista.nextElementSibling;
        }
        
        if (lista && lista.tagName === 'UL') {
            const links = Array.from(lista.querySelectorAll('a'));
            const questoes = links.map(link => ({
                texto: link.innerText.trim(),
                url: link.href
            }));
            
            if (questoes.length > 0) {
                exames_mapeados.push({
                    titulo: titulo,
                    questoes: questoes
                });
            }
        }
    }
    return exames_mapeados;
    """
    return driver.execute_script(script)

def extrair_conteudo_questao(driver):
    """
    Injeta JavaScript para separar inteligentemente o Enunciado do Gabarito.
    Para o Enunciado quando encontra 'Resposta FGV'.
    Começa o Gabarito quando encontra 'Padrão de Resposta'.
    """
    script = """
    function extrair() {
        const contentDiv = document.querySelector("#conteudo_total");
        if (!contentDiv) return {erro: "Conteúdo não encontrado"};
        
        let fase = "ENUNCIADO"; 
        let enunciado_parts = [];
        let gabarito_parts = [];
        
        const elements = Array.from(contentDiv.children);
        
        for (const el of elements) {
            const tagName = el.tagName.toUpperCase();
            const text = el.innerText ? el.innerText.trim() : "";
            
            // Identifica marcadores de parada global (Fim da questão)
            if (text.includes("Distribuição de Pontos") || 
                text.includes("Voltar para lista") || 
                text.includes("Questão Anterior") || 
                text.includes("Próxima Questão") || 
                text.includes("Achou esta página útil")) {
                break;
            }
            
            // Identifica marcadores de transição
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
            
            // Lógica de Espaçamento: Se a tag for vazia (BR, P vazio, DIV vazio), adicionamos uma quebra
            if (text.length === 0) {
                if (tagName === 'BR' || tagName === 'P' || tagName === 'DIV') {
                    if (fase === "ENUNCIADO") enunciado_parts.push("");
                    else if (fase === "GABARITO") gabarito_parts.push("");
                }
                continue;
            }
            
            // Coleta de Conteúdo
            if (fase === "ENUNCIADO") {
                if (tagName === 'P' || tagName === 'SPAN' || tagName === 'DIV') {
                    enunciado_parts.push(text);
                }
            } else if (fase === "GABARITO") {
                if (tagName === 'P' || tagName === 'SPAN' || tagName === 'DIV') {
                    if (!text.includes("Para ver a resposta da FGV")) {
                        gabarito_parts.push(text);
                    }
                }
            }
        }
        
        // Limpa linhas vazias no início e fim, e colapsa múltiplas linhas vazias seguidas
        function limpar(arr) {
            let txt = arr.join('\\n');
            txt = txt.replace(/^\\n+/, '');   // Remove linhas vazias no início
            txt = txt.replace(/\\n+$/, '');   // Remove linhas vazias no fim
            txt = txt.replace(/\\n{3,}/g, '\\n\\n'); // Máximo 1 linha em branco entre parágrafos
            return txt;
        }
        
        return {
            enunciado: limpar(enunciado_parts),
            gabarito: limpar(gabarito_parts)
        };
    }
    return extrair();
    """
    return driver.execute_script(script)

# ==========================================
# 4. FLUXO PRINCIPAL DA AUTOMAÇÃO
# ==========================================
def iniciar_robo():
    # Inicializa o banco de dados (cria o arquivo .db se não existir)
    database.conectar()
    
    limpar_terminal()
    
    # --- PASSO 1: Escolha da Área ---
    area_escolhida = menu_selecao(FLUXOS_AUTOMACAO, "ROBÔ OAB - SELECIONE A ÁREA DO DIREITO", "nome")
    
    print(f"\n[AGUARDE] Abrindo navegador e acessando: {area_escolhida['nome']}...")
    
    chrome_options = Options()
    chrome_options.page_load_strategy = 'eager' # Carrega o DOM sem esperar por anúncios pesados
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Acessa a página principal e clica na área
        driver.get(URL_BASE)
        time.sleep(1)
        elemento_link = driver.find_element(By.PARTIAL_LINK_TEXT, area_escolhida['texto_link'])
        elemento_link.click()
        time.sleep(2) # Espera a nova página carregar
        
        print("[AGUARDE] Lendo e organizando os exames da página...")
        exames = extrair_exames(driver)
        
        if not exames:
            print("\n[AVISO] Nenhum exame foi encontrado para esta área.")
            return
            
        limpar_terminal()
        
        # --- PASSO 2: Escolha do Exame ---
        titulo_menu_exames = f"EXAMES DISPONÍVEIS - {area_escolhida['nome'].upper()}"
        exame_escolhido = menu_selecao(exames, titulo_menu_exames, "titulo")
        
        limpar_terminal()
        
        # --- PASSO 3: Escolha da Peça/Questão ---
        titulo_menu_questoes = f"QUESTÕES DO {exame_escolhido['titulo']}"
        questao_escolhida = menu_selecao(exame_escolhido["questoes"], titulo_menu_questoes, "texto")
        
        # --- PASSO 4: Acessar link final e extrair ---
        print(f"\n[NAVEGANDO] Acessando a página da questão...")
        driver.get(questao_escolhida['url'])
        
        # Espera um pouco mais para garantir que o texto foi renderizado
        time.sleep(4) 
        
        print("\n[EXTRAINDO] Mapeando Enunciado e Padrão de Resposta...")
        dados = extrair_conteudo_questao(driver)
        
        if dados and isinstance(dados, dict) and "erro" not in dados:
            # Salva no banco de dados
            sucesso = database.salvar_peca(
                area=area_escolhida['nome'],
                exame=exame_escolhido['titulo'],
                titulo=questao_escolhida['texto'],
                url=questao_escolhida['url'],
                enunciado=dados['enunciado'],
                resposta=dados['gabarito']
            )
            if sucesso:
                print(f"\n[BD OK] Peça '{questao_escolhida['texto']}' salva com sucesso!")
                print(f"-> Enunciado: {len(dados['enunciado'])} caracteres capturados.")
                print(f"-> Gabarito: {len(dados['gabarito'])} caracteres capturados.")
            else:
                print(f"\n[ERRO BD] Falha ao tentar salvar no banco de dados.")
        else:
            erro_msg = dados.get("erro") if isinstance(dados, dict) else "Erro desconhecido"
            print(f"\n[AVISO] {erro_msg}. Nada foi salvo.")
        
        print("\n[FINALIZADO] Operação concluída. O navegador permanecerá aberto.")
        
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um problema durante a automação:\n{e}")

if __name__ == "__main__":
    iniciar_robo()
