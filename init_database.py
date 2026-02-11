#!/usr/bin/env python3
"""
Script per inizializzare il database con i prezzi base
ATTENZIONE: Usa SOLO i prezzi reali menzionati dall'utente!
"""

import sys
import os

# Aggiungi backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from server import app, db, Voce

def init_database():
    """Inizializza database con prezzi base (SOLO quelli reali!)"""
    with app.app_context():
        # Crea tabelle se non esistono
        db.create_all()
        print("✅ Tabelle database create")

        # Verifica se ci sono già voci
        count = Voce.query.count()
        if count > 0:
            print(f"⚠️  Database già contiene {count} voci")
            risposta = input("Vuoi sovrascrivere? (s/N): ")
            if risposta.lower() != 's':
                print("❌ Annullato")
                return

            # Cancella tutto
            Voce.query.delete()
            db.session.commit()
            print("🗑️  Voci precedenti cancellate")

        # PREZZI REALI menzionati dall'utente (IVA INCLUSA al 10%)
        voci_base = [
            # L'utente ha detto: "4 caffè = 6€ totale" → €1.50 cad
            {"gruppo": "BAR", "nome": "Caffè", "prezzo": 1.50, "stampa": "bancone"},

            # L'utente ha detto: "l'aperitivo costa 2,5"
            {"gruppo": "BAR", "nome": "Aperitivo Analcolico", "prezzo": 2.50, "stampa": "bancone"},
        ]

        for voce_data in voci_base:
            voce = Voce(
                gruppo=voce_data["gruppo"],
                nome=voce_data["nome"],
                prezzo=voce_data["prezzo"],
                destinazione_stampa=voce_data["stampa"]
            )
            db.session.add(voce)
            print(f"✅ Aggiunto: {voce_data['nome']} - €{voce_data['prezzo']:.2f}")

        db.session.commit()

        print("\n✅ Database inizializzato!")
        print("📝 IMPORTANTE: Aggiungi gli altri articoli del menù via Admin Panel!")
        print("   http://localhost:5000/admin")

if __name__ == "__main__":
    print("🔧 Inizializzazione database con prezzi reali...")
    print("   - Caffè: €1.50 (IVA inclusa)")
    print("   - Aperitivo Analcolico: €2.50 (IVA inclusa)")
    print()

    init_database()
