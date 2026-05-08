import sqlite3
import os

DB_NAME = "oab_questoes.db"

def conectar():
    """Cria a conexao com o banco de dados e cria as tabelas se nao existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pecas_fgv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_direito TEXT NOT NULL,
            exame_nome TEXT NOT NULL,
            titulo_peca TEXT NOT NULL,
            url_peca TEXT NOT NULL UNIQUE,
            enunciado TEXT,
            resposta_padrao TEXT NOT NULL,
            distribuicao_pontos TEXT,
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migrar banco existente: adicionar coluna se nao existir
    try:
        cursor.execute("ALTER TABLE pecas_fgv ADD COLUMN distribuicao_pontos TEXT")
    except sqlite3.OperationalError:
        pass  # Coluna ja existe
    
    conn.commit()
    return conn

def ja_existe(url):
    """Verifica se uma peca com essa URL ja foi salva no banco."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pecas_fgv WHERE url_peca = ?", (url,))
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado > 0

def salvar_peca(area, exame, titulo, url, enunciado, resposta, distribuicao_pontos=""):
    """Salva os dados da peca extraida no banco de dados."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO pecas_fgv (area_direito, exame_nome, titulo_peca, url_peca, enunciado, resposta_padrao, distribuicao_pontos)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (area, exame, titulo, url, enunciado, resposta, distribuicao_pontos))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")
        return False
