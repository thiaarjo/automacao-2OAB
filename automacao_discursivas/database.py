import sqlite3
import os

DB_NAME = "oab_discursivas.db"

def conectar():
    """Cria a conexão com o banco de dados e cria as tabelas se não existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela para questões discursivas com respostas A e B separadas
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
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def ja_existe(url):
    """Verifica se uma questão com essa URL já foi salva no banco."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM discursivas_fgv WHERE url_questao = ?", (url,))
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado > 0

def salvar_discursiva(area, exame, titulo, url, enunciado, resposta_a, resposta_b):
    """Salva os dados da questão discursiva no banco de dados."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO discursivas_fgv (area_direito, exame_nome, titulo_questao, url_questao, enunciado, resposta_a, resposta_b)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (area, exame, titulo, url, enunciado, resposta_a, resposta_b))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")
        return False

