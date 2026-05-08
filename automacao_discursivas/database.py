import sqlite3
import os

DB_NAME = "oab_discursivas.db"

def conectar():
    """Cria a conexao com o banco de dados e cria as tabelas se nao existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discursivas_fgv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_direito TEXT NOT NULL,
            exame_nome TEXT NOT NULL,
            titulo_questao TEXT NOT NULL,
            url_questao TEXT NOT NULL UNIQUE,
            enunciado TEXT,
            resposta_a TEXT,
            resposta_b TEXT,
            pontuacao_a TEXT,
            pontuacao_b TEXT,
            distribuicao_pontos TEXT,
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migrar banco existente: adicionar colunas se nao existirem
    for coluna in ['distribuicao_pontos', 'pontuacao_a', 'pontuacao_b']:
        try:
            cursor.execute(f"ALTER TABLE discursivas_fgv ADD COLUMN {coluna} TEXT")
        except sqlite3.OperationalError:
            pass
    
    conn.commit()
    return conn

def ja_existe(url):
    """Verifica se uma questao com essa URL ja foi salva no banco."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM discursivas_fgv WHERE url_questao = ?", (url,))
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado > 0

def salvar_discursiva(area, exame, titulo, url, enunciado, resposta_a, resposta_b, pontuacao_a="", pontuacao_b="", distribuicao_pontos=""):
    """Salva os dados da questao discursiva no banco de dados."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO discursivas_fgv (area_direito, exame_nome, titulo_questao, url_questao, enunciado, resposta_a, resposta_b, pontuacao_a, pontuacao_b, distribuicao_pontos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (area, exame, titulo, url, enunciado, resposta_a, resposta_b, pontuacao_a, pontuacao_b, distribuicao_pontos))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")
        return False
