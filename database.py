import sqlite3
import os

DB_NAME = "oab_questoes.db"

def conectar():
    """Cria a conexão com o banco de dados e cria as tabelas se não existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Criando a tabela para armazenar as peças/questões
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pecas_fgv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_direito TEXT NOT NULL,
            exame_nome TEXT NOT NULL,
            titulo_peca TEXT NOT NULL,
            url_peca TEXT NOT NULL,
            enunciado TEXT,
            resposta_padrao TEXT NOT NULL,
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def salvar_peca(area, exame, titulo, url, enunciado, resposta):
    """Salva os dados da peça extraída no banco de dados."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Inserindo os dados
        cursor.execute("""
            INSERT INTO pecas_fgv (area_direito, exame_nome, titulo_peca, url_peca, enunciado, resposta_padrao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (area, exame, titulo, url, enunciado, resposta))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")
        return False
