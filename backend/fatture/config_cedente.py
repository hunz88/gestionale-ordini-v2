#!/usr/bin/env python3
"""
Configurazione dati cedente/prestatore per fatture elettroniche
IMPORTANTE: Compilare tutti i campi con i dati reali dell'esercizio
"""

# ══════════════════════════════════════════════════════════════════════════════
# DATI CEDENTE/PRESTATORE (IL TUO ESERCIZIO)
# ══════════════════════════════════════════════════════════════════════════════

DATI_CEDENTE = {
    # ===== DATI FISCALI (OBBLIGATORI) =====
    'partita_iva': 'IT12345678901',  # ⚠️ MODIFICARE con la tua P.IVA (11 cifre precedute da IT)
    'codice_fiscale': '12345678901',  # ⚠️ MODIFICARE con il tuo CF (se diverso da P.IVA)
    'denominazione': 'SUNSET BAR S.R.L.',  # ⚠️ MODIFICARE con ragione sociale o nome ditta

    # ===== REGIME FISCALE =====
    # RF01 = Regime ordinario
    # RF02 = Regime dei contribuenti minimi (art. 1, c.96-117, L. 244/2007)
    # RF04 = Agricoltura e attività connesse e pesca (artt. 34 e 34-bis, DPR 633/1972)
    # RF05 = Vendita sali e tabacchi (art. 74, c.1, DPR 633/1972)
    # RF06 = Commercio dei fiammiferi (art. 74, c.1, DPR 633/1972)
    # RF07 = Editoria (art. 74, c.1, DPR 633/1972)
    # RF08 = Gestione di servizi di telefonia pubblica (art. 74, c.1, DPR 633/1972)
    # RF09 = Rivendita di documenti di trasporto pubblico e di sosta (art. 74, c.1, DPR 633/1972)
    # RF10 = Intrattenimenti, giochi e altre attività di cui alla tariffa allegata al DPR 640/72
    # RF11 = Agenzie di viaggi e turismo (art. 74-ter, DPR 633/1972)
    # RF12 = Agriturismo (art. 5, c.2, L. 413/1991)
    # RF13 = Vendite a domicilio (art. 25-bis, c.6, DPR 600/1973)
    # RF14 = Rivendita di beni usati, di oggetti d'arte, d'antiquariato o da collezione
    # RF15 = Agenzie di vendite all'asta di oggetti d'arte, antiquariato o da collezione
    # RF16 = IVA per cassa P.A. (art. 6, c.5, DPR 633/1972)
    # RF17 = IVA per cassa (art. 32-bis, DL 83/2012)
    # RF18 = Altro
    # RF19 = Regime forfettario (L. 190/2014)
    'regime_fiscale': 'RF01',  # ⚠️ MODIFICARE se necessario (vedi elenco sopra)

    # ===== INDIRIZZO SEDE LEGALE (OBBLIGATORIO) =====
    'indirizzo': 'Via Roma, 123',  # ⚠️ MODIFICARE con indirizzo completo
    'cap': '00100',  # ⚠️ MODIFICARE con CAP corretto
    'citta': 'Roma',  # ⚠️ MODIFICARE con città
    'provincia': 'RM',  # ⚠️ MODIFICARE con sigla provincia (2 lettere)
    'nazione': 'IT',  # Lasciare IT per Italia

    # ===== CONTATTI (OPZIONALI MA CONSIGLIATI) =====
    'telefono': '+39 06 12345678',  # ⚠️ MODIFICARE con telefono (opzionale)
    'email': 'info@sunsetbar.it'  # ⚠️ MODIFICARE con email (opzionale)
}

# ══════════════════════════════════════════════════════════════════════════════
# ISTRUZIONI PER LA COMPILAZIONE
# ══════════════════════════════════════════════════════════════════════════════
"""
1. Modifica TUTTI i campi marcati con ⚠️ inserendo i tuoi dati reali
2. La Partita IVA deve essere nel formato IT + 11 cifre (es: IT12345678901)
3. Il regime fiscale più comune per bar/ristoranti è:
   - RF01: Regime ordinario (con partita IVA normale)
   - RF19: Regime forfettario (se fatturato sotto soglie previste)
4. L'indirizzo deve essere quello della sede legale/operativa
5. Dopo la modifica, riavvia il server per applicare le modifiche

IMPORTANTE: Questi dati appariranno nelle fatture elettroniche inviate all'Agenzia
delle Entrate. Assicurati che siano corretti e aggiornati!
"""

# ══════════════════════════════════════════════════════════════════════════════
# VALIDAZIONE CONFIGURAZIONE
# ══════════════════════════════════════════════════════════════════════════════
def valida_configurazione():
    """Verifica che la configurazione sia stata compilata correttamente"""
    errori = []

    # Verifica campi obbligatori
    if DATI_CEDENTE['partita_iva'] == 'IT12345678901':
        errori.append("⚠️ Partita IVA non configurata! Modifica il file config_cedente.py")

    if DATI_CEDENTE['denominazione'] == 'SUNSET BAR S.R.L.':
        errori.append("⚠️ Denominazione non configurata! Modifica il file config_cedente.py")

    if DATI_CEDENTE['indirizzo'] == 'Via Roma, 123':
        errori.append("⚠️ Indirizzo non configurato! Modifica il file config_cedente.py")

    # Verifica formato P.IVA
    piva = DATI_CEDENTE['partita_iva']
    if not piva.startswith('IT') or len(piva) != 13:
        errori.append(f"⚠️ Partita IVA non valida: {piva}. Formato: IT + 11 cifre")

    # Verifica provincia (2 caratteri)
    if len(DATI_CEDENTE['provincia']) != 2:
        errori.append("⚠️ Provincia deve essere 2 lettere (es: RM, MI, TO)")

    # Verifica CAP (5 cifre)
    if not DATI_CEDENTE['cap'].isdigit() or len(DATI_CEDENTE['cap']) != 5:
        errori.append("⚠️ CAP deve essere 5 cifre")

    return errori


if __name__ == '__main__':
    # Test configurazione
    print("="*60)
    print("VERIFICA CONFIGURAZIONE CEDENTE")
    print("="*60)

    errori = valida_configurazione()

    if errori:
        print("\n❌ ERRORI TROVATI:\n")
        for errore in errori:
            print(f"  {errore}")
        print("\n📝 Modifica il file backend/fatture/config_cedente.py e riprova")
        print("="*60)
    else:
        print("\n✅ CONFIGURAZIONE VALIDA!\n")
        print("Dati cedente configurati:")
        print(f"  Denominazione: {DATI_CEDENTE['denominazione']}")
        print(f"  P.IVA: {DATI_CEDENTE['partita_iva']}")
        print(f"  Regime: {DATI_CEDENTE['regime_fiscale']}")
        print(f"  Indirizzo: {DATI_CEDENTE['indirizzo']}, {DATI_CEDENTE['cap']} {DATI_CEDENTE['citta']} ({DATI_CEDENTE['provincia']})")
        if DATI_CEDENTE.get('telefono'):
            print(f"  Telefono: {DATI_CEDENTE['telefono']}")
        if DATI_CEDENTE.get('email'):
            print(f"  Email: {DATI_CEDENTE['email']}")
        print("\n✅ Pronto per emettere fatture elettroniche!")
        print("="*60)
