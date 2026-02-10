#!/usr/bin/env python3
"""
Script di test per verificare il setup della fatturazione elettronica
"""

import sys
import os

# Aggiungi backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test import moduli"""
    print("1️⃣ Test import moduli...")
    try:
        from backend.fatture.fattura_elettronica import FatturaElettronicaXML
        from backend.fatture.config_cedente import DATI_CEDENTE, valida_configurazione
        print("   ✅ Moduli importati correttamente")
        return True
    except Exception as e:
        print(f"   ❌ Errore import: {e}")
        return False


def test_configurazione():
    """Test configurazione cedente"""
    print("\n2️⃣ Test configurazione cedente...")
    try:
        from backend.fatture.config_cedente import DATI_CEDENTE, valida_configurazione

        errori = valida_configurazione()
        if errori:
            print("   ⚠️ Configurazione da completare:")
            for err in errori:
                print(f"      {err}")
            print("\n   📝 Modifica backend/fatture/config_cedente.py")
            return False
        else:
            print("   ✅ Configurazione valida")
            print(f"      Denominazione: {DATI_CEDENTE['denominazione']}")
            print(f"      P.IVA: {DATI_CEDENTE['partita_iva']}")
            return True
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False


def test_database():
    """Test creazione tabelle database"""
    print("\n3️⃣ Test database...")
    try:
        from server import app, db, Cliente, Fattura, RigaFattura

        with app.app_context():
            # Crea tabelle
            db.create_all()
            print("   ✅ Tabelle database create/verificate")

            # Verifica tabelle esistano
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            required_tables = ['clienti', 'fatture', 'righe_fattura']
            missing = [t for t in required_tables if t not in tables]

            if missing:
                print(f"   ⚠️ Tabelle mancanti: {missing}")
                return False
            else:
                print(f"   ✅ Tutte le tabelle presenti: {required_tables}")
                return True

    except Exception as e:
        print(f"   ❌ Errore database: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generatore_xml():
    """Test generatore XML"""
    print("\n4️⃣ Test generatore XML...")
    try:
        from backend.fatture.fattura_elettronica import FatturaElettronicaXML
        from datetime import datetime

        gen = FatturaElettronicaXML()

        # Verifica che il cedente sia configurato
        if not gen.CEDENTE.get('partita_iva'):
            print("   ⚠️ Cedente non configurato")
            return False

        print("   ✅ Generatore XML inizializzato")
        return True

    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False


def test_api_endpoints():
    """Test che gli endpoint API siano registrati"""
    print("\n5️⃣ Test API endpoints...")
    try:
        from server import app

        required_endpoints = [
            '/api/clienti',
            '/api/fatture',
            '/api/fatture/da-ordine'
        ]

        with app.app_context():
            rules = [str(rule) for rule in app.url_map.iter_rules()]

            missing = []
            for endpoint in required_endpoints:
                if endpoint not in rules:
                    missing.append(endpoint)

            if missing:
                print(f"   ⚠️ Endpoint mancanti: {missing}")
                return False
            else:
                print(f"   ✅ Tutti gli endpoint registrati")
                return True

    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False


def main():
    print("="*70)
    print("🧪 TEST SETUP FATTURAZIONE ELETTRONICA")
    print("="*70)

    results = []

    # Esegui test
    results.append(("Import moduli", test_imports()))
    results.append(("Configurazione", test_configurazione()))
    results.append(("Database", test_database()))
    results.append(("Generatore XML", test_generatore_xml()))
    results.append(("API Endpoints", test_api_endpoints()))

    # Riepilogo
    print("\n" + "="*70)
    print("📊 RIEPILOGO TEST")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n✅ Passati: {passed}/{total}")

    if passed == total:
        print("\n🎉 TUTTI I TEST SUPERATI!")
        print("✅ Il sistema di fatturazione è pronto all'uso")
        print("\n📝 PROSSIMI PASSI:")
        print("   1. Configura i dati aziendali in backend/fatture/config_cedente.py")
        print("   2. Riavvia il server")
        print("   3. Accedi alla sezione Fatture dal menu")
    else:
        print("\n⚠️ Alcuni test non sono passati")
        print("📝 Controlla gli errori sopra e correggi prima di procedere")

    print("="*70)


if __name__ == '__main__':
    main()
