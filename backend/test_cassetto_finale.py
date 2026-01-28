#!/usr/bin/env python3
import socket
import time

def invia_comando(comando, descrizione):
    print(f"\n{descrizione}")
    print("Invio...", end=' ', flush=True)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('192.168.0.10', 9100))
        sock.sendall(comando.encode('utf-8'))
        
        try:
            resp = sock.recv(2048)
            print(f"✓ Risposta: {len(resp)} bytes")
            if len(resp) > 0:
                print(f"Contenuto: {resp[:200]}")
        except:
            print("✓ Inviato")
        
        sock.close()
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"✗ Errore: {e}")
        return False

print("\n" + "="*70)
print("  TEST FINALE - SCONTRINO €0.01 PER APERTURA CASSETTO")
print("="*70)
print("\nQuesta è l'ultima prova basata sul manuale RCH!")
print("Lo scontrino minimo dovrebbe aprire il cassetto.\n")

input("Premi INVIO per iniziare il test...")

# Scontrino fiscale minimo RCH
scontrino_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<printerFiscalReceipt>
  <beginFiscalReceipt operator="1"/>
  <printRecItem description="APERTURA" quantity="1" unitPrice="0.01" department="1"/>
  <printRecTotal payment="0" paymentAmount="0.01"/>
  <endFiscalReceipt/>
</printerFiscalReceipt>'''

if invia_comando(scontrino_xml, "[TEST] Scontrino fiscale €0.01"):
    print("\n" + "="*70)
    print("\n❓ RISULTATO:")
    print("1. La stampante ha stampato qualcosa?")
    print("2. Il CASSETTO si è APERTO?")
    
    risposta = input("\nIl cassetto si è aperto? (si/no): ")
    
    if risposta.lower() in ['si', 's', 'sì', 'yes', 'y']:
        print("\n" + "="*70)
        print("🎉 PERFETTO! CASSETTO FUNZIONA!")
        print("="*70)
        print("\nIL CASSETTO RCH si apre DOPO la chiusura scontrino!")
        print("\nPer aprire il cassetto senza vendita vera:")
        print("→ Stampa scontrino da €0.01")
        print("→ Il cassetto si apre automaticamente")
        print("\nPossiamo integrare questo nel sistema!")
    else:
        print("\n" + "="*70)
        print("⚠️  Cassetto NON si è aperto")
        print("="*70)
        print("\nPROSSIMI STEP:")
        print("1. Verifica cassetto collegato correttamente")
        print("2. Test apertura da tastiera stampante")
        print("3. Contatta supporto RCH: support.rch.it")
        print("4. Verifica configurazione cassetto in PRG")
else:
    print("\n✗ Errore invio comando")

print("\n" + "="*70)
