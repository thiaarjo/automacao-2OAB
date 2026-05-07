import sqlite3
import os
import sys
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# ==========================================
# CONFIGURAÇÃO
# ==========================================
DB_PECAS = os.path.join("automacao_pecas", "oab_questoes.db")
DB_DISCURSIVAS = os.path.join("automacao_discursivas", "oab_discursivas.db")
ARQUIVO_SAIDA = "questoes_oab_2fase.xlsx"

# Cores do tema
COR_HEADER = "1F2937"       # Cinza escuro
COR_HEADER_FONT = "FFFFFF"  # Branco
COR_AREA = "E0E7FF"         # Azul claro (separador de área)
COR_ZEBRA_1 = "FFFFFF"      # Branco
COR_ZEBRA_2 = "F8FAFC"      # Cinza bem claro

# ==========================================
# FUNÇÕES DE ESTILO
# ==========================================
def estilo_header():
    """Retorna o estilo do cabeçalho."""
    return {
        "font": Font(name="Segoe UI", bold=True, color=COR_HEADER_FONT, size=11),
        "fill": PatternFill(start_color=COR_HEADER, end_color=COR_HEADER, fill_type="solid"),
        "alignment": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "border": Border(
            bottom=Side(style="thin", color="4B5563")
        )
    }

def estilo_celula(zebra=False):
    """Retorna o estilo de uma célula de dados."""
    fill_color = COR_ZEBRA_2 if zebra else COR_ZEBRA_1
    return {
        "font": Font(name="Segoe UI", size=10),
        "fill": PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid"),
        "alignment": Alignment(vertical="top", wrap_text=True),
        "border": Border(
            bottom=Side(style="hair", color="E5E7EB")
        )
    }

def aplicar_estilo(cell, estilo):
    """Aplica um dicionário de estilos a uma célula."""
    for attr, value in estilo.items():
        setattr(cell, attr, value)

# ==========================================
# LEITURA DO BANCO DE DADOS
# ==========================================
def ler_pecas():
    """Lê todas as peças do banco de dados."""
    if not os.path.exists(DB_PECAS):
        print(f"[AVISO] Banco de peças não encontrado: {DB_PECAS}")
        return []
    conn = sqlite3.connect(DB_PECAS)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT area_direito, exame_nome, titulo_peca, enunciado, resposta_padrao, url_peca
        FROM pecas_fgv
        ORDER BY area_direito, exame_nome
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados

def ler_discursivas():
    """Lê todas as discursivas do banco de dados."""
    if not os.path.exists(DB_DISCURSIVAS):
        print(f"[AVISO] Banco de discursivas não encontrado: {DB_DISCURSIVAS}")
        return []
    conn = sqlite3.connect(DB_DISCURSIVAS)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT area_direito, exame_nome, titulo_questao, enunciado, resposta_a, resposta_b, url_questao
        FROM discursivas_fgv
        ORDER BY area_direito, exame_nome
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados

# ==========================================
# CRIAÇÃO DAS ABAS DO EXCEL
# ==========================================
def criar_aba_pecas(wb, dados):
    """Cria a aba de Peças Profissionais."""
    ws = wb.active
    ws.title = "Peças Profissionais"
    
    # Cabeçalhos
    headers = ["Área", "Exame", "Enunciado", "Padrão de Resposta FGV"]
    larguras = [22, 40, 80, 80]
    
    header_style = estilo_header()
    for col, (header, largura) in enumerate(zip(headers, larguras), 1):
        cell = ws.cell(row=1, column=col, value=header)
        aplicar_estilo(cell, header_style)
        ws.column_dimensions[cell.column_letter].width = largura
    
    # Altura do cabeçalho
    ws.row_dimensions[1].height = 30
    
    # Dados
    for row_idx, (area, exame, titulo, enunciado, resposta, url) in enumerate(dados, 2):
        zebra = (row_idx % 2 == 0)
        celula_style = estilo_celula(zebra)
        
        valores = [area, exame, enunciado, resposta]
        for col, valor in enumerate(valores, 1):
            cell = ws.cell(row=row_idx, column=col, value=valor or "")
            aplicar_estilo(cell, celula_style)
    
    # Congelar cabeçalho
    ws.freeze_panes = "A2"
    
    # Filtro automático
    if dados:
        ws.auto_filter.ref = f"A1:D{len(dados) + 1}"
    
    return len(dados)

def criar_aba_discursivas(wb, dados):
    """Cria a aba de Questões Discursivas."""
    ws = wb.create_sheet("Questões Discursivas")
    
    # Cabeçalhos
    headers = ["Área", "Exame", "Título", "Enunciado", "Resposta A", "Resposta B", "URL"]
    larguras = [22, 40, 50, 80, 60, 60, 45]
    
    header_style = estilo_header()
    for col, (header, largura) in enumerate(zip(headers, larguras), 1):
        cell = ws.cell(row=1, column=col, value=header)
        aplicar_estilo(cell, header_style)
        ws.column_dimensions[cell.column_letter].width = largura
    
    ws.row_dimensions[1].height = 30
    
    # Dados
    for row_idx, (area, exame, titulo, enunciado, resp_a, resp_b, url) in enumerate(dados, 2):
        zebra = (row_idx % 2 == 0)
        celula_style = estilo_celula(zebra)
        
        valores = [area, exame, titulo, enunciado, resp_a, resp_b, url]
        for col, valor in enumerate(valores, 1):
            cell = ws.cell(row=row_idx, column=col, value=valor or "")
            aplicar_estilo(cell, celula_style)
    
    ws.freeze_panes = "A2"
    
    if dados:
        ws.auto_filter.ref = f"A1:G{len(dados) + 1}"
    
    return len(dados)

# ==========================================
# FLUXO PRINCIPAL
# ==========================================
def exportar():
    print(f"\n{'='*60}")
    print(f"  EXPORTADOR OAB 2a FASE -> EXCEL")
    print(f"{'='*60}")
    
    wb = Workbook()
    
    # Ler dados
    print("\n[1/4] Lendo banco de peças...")
    pecas = ler_pecas()
    print(f"      -> {len(pecas)} peça(s) encontrada(s).")
    
    print("[2/4] Lendo banco de discursivas...")
    discursivas = ler_discursivas()
    print(f"      -> {len(discursivas)} discursiva(s) encontrada(s).")
    
    if not pecas and not discursivas:
        print("\n[AVISO] Nenhum dado encontrado nos bancos. Execute os robôs primeiro!")
        return
    
    # Criar abas
    print("[3/4] Montando planilha...")
    total_pecas = criar_aba_pecas(wb, pecas)
    total_disc = criar_aba_discursivas(wb, discursivas)
    
    # Salvar
    print(f"[4/4] Salvando '{ARQUIVO_SAIDA}'...")
    wb.save(ARQUIVO_SAIDA)
    
    print(f"\n{'='*60}")
    print(f"  [OK] EXPORTACAO CONCLUIDA!")
    print(f"  Arquivo: {os.path.abspath(ARQUIVO_SAIDA)}")
    print(f"  Peças: {total_pecas} | Discursivas: {total_disc}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    exportar()
