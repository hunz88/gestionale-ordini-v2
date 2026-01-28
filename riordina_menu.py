#!/usr/bin/env python3
import sqlite3
import os

# Percorso database
DB_PATH = "ordini.db"

def riordina_menu():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== RIORDINO MENU SUNSET BAR ===")
    
    # 1. AGGIUNGIAMO CAMPO ORDINE ALLE CATEGORIE
    try:
        cursor.execute("ALTER TABLE voce ADD COLUMN ordine_categoria INTEGER DEFAULT 999")
        conn.commit()
        print("✅ Aggiunto campo ordine_categoria")
    except sqlite3.OperationalError:
        print("⚠️  Campo ordine_categoria già esistente")
    
    # 2. AGGIUNGIAMO CAMPO ORDINE AGLI ARTICOLI
    try:
        cursor.execute("ALTER TABLE voce ADD COLUMN ordine_articolo INTEGER DEFAULT 999")
        conn.commit()
        print("✅ Aggiunto campo ordine_articolo")
    except sqlite3.OperationalError:
        print("⚠️  Campo ordine_articolo già esistente")
    
    # 3. DEFINIAMO ORDINE CATEGORIE (nomi ESATTI dal database)
    ordine_categorie = {
        "CAFFETTERIA": 1,
        "BIRRE & SPRITZ": 2, 
        "BEVANDE ANALCOLICHE": 3,
        "TOAST": 4,
        "BRUSCHETTE": 5,
        "PANINI A PANE MORBIDO": 6,
        "BURGER & SPECIALITA CALDE": 7,
        "PIADINE ARTIGIANALI": 8,
        "SALSE EXTRA": 9,
        "AMARI & GRAPPE": 10
    }
    
    print("\n=== AGGIORNO ORDINE CATEGORIE ===")
    for categoria, ordine in ordine_categorie.items():
        cursor.execute(
            "UPDATE voce SET ordine_categoria = ? WHERE gruppo = ?",
            (ordine, categoria)
        )
        rows = cursor.rowcount
        if rows > 0:
            print(f"✅ {categoria}: ordine {ordine} ({rows} articoli)")
    
    # 4. ORDINE SPECIFICO PER CAFFETTERIA (i più richiesti in cima)
    ordine_caffetteria = {
        "Espresso": 1,
        "Cappuccino": 2,
        "Macchiato": 3,
        "Lungo": 4,
        "Corretto": 5,
        "Latte": 6,
        "Decaffeinato": 7,
    }
    
    print("\n=== AGGIORNO ORDINE CAFFETTERIA ===")
    for articolo, ordine in ordine_caffetteria.items():
        cursor.execute(
            "UPDATE voce SET ordine_articolo = ? WHERE nome LIKE ? AND gruppo = 'CAFFETTERIA'",
            (ordine, f"%{articolo}%")
        )
        if cursor.rowcount > 0:
            print(f"✅ {articolo}: ordine {ordine}")
    
    # 5. ORDINE PER BIRRE (dalle più comuni)
    ordine_birre = {
        "Piccola": 1,
        "Media": 2,
        "Grande": 3,
        "Spina": 4,
        "Spritz": 5,
        "Aperol": 6
    }
    
    print("\n=== AGGIORNO ORDINE BIRRE ===")
    for articolo, ordine in ordine_birre.items():
        cursor.execute(
            "UPDATE voce SET ordine_articolo = ? WHERE nome LIKE ? AND gruppo = 'BIRRE & SPRITZ'",
            (ordine, f"%{articolo}%")
        )
        if cursor.rowcount > 0:
            print(f"✅ {articolo}: ordine {ordine}")
    
    conn.commit()
    
    # 6. VERIFICA RISULTATI
    print("\n=== VERIFICA NUOVO ORDINE ===")
    cursor.execute("""
        SELECT gruppo, ordine_categoria, COUNT(*) as articoli 
        FROM voce 
        GROUP BY gruppo, ordine_categoria 
        ORDER BY ordine_categoria, gruppo
    """)
    
    for row in cursor.fetchall():
        categoria, ordine, count = row
        print(f"{ordine:2d}. {categoria:<25} ({count} articoli)")
    
    print("\n=== TOP 10 CAFFETTERIA ===")
    cursor.execute("""
        SELECT nome, ordine_articolo 
        FROM voce 
        WHERE gruppo = 'CAFFETTERIA' 
        ORDER BY ordine_articolo, nome
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        nome, ordine = row
        print(f"{ordine:3d}. {nome}")
    
    conn.close()
    print("\n🎯 RIORDINO COMPLETATO!")

if __name__ == "__main__":
    riordina_menu()
