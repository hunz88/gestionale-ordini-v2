#!/usr/bin/env python3
import socket

# XML per scontrino €0.00 che apre cassetto
xml_commands = [
    # Variante 1 - Scontrino vuoto
    '''<?xml version="1.0" encoding="UTF-8"?>
<printerFiscalReceipt>
  <beginFiscalReceipt operator="1"/>
  <printRecItem description="APERTURA CASSETTO" quantity="1" unitPrice="0.01" department="1"/>
  <printRecTotal payment="0" paymentAmount="0.01"/>
  <endFiscalReceipt/>
</printerFiscalReceipt>''',
    
    # Variante 2 - Solo pagamento
    '''<?xml version="1.0" encoding="UTF-8"?>
<printerFiscal>
  <beginFiscalReceipt/>
  <printRecTotal payment="0" paymentAmount="0.01"/>
  <endFiscalReceipt/>
</printerFiscal>''',
    
    # Variante 3 - Documento non fiscale
    '''<?xml version="1.0" encoding="UTF-8"?>
<printerNonFiscal>
  <beginNonFiscal/>
  <printNormal data="APERTURA CASSETTO"/>
  <endNonFiscal/>
</printerNonFiscal>''',
]

def test_comando(xml, num):
    print(f"\n{'='*60}")
    print(f"TEST {num}/{len(xml_commands)}")
    print("="*60)
    print("Invio comando...", end=' ', flush=True)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('192.168.0.10', 9100))
        sock.sendall(xml.encode('utf-8'))
        
        try:
            resp = sock.recv(2048)
            print(f"✓ Inviato - Risposta: {len(resp)} bytes")
            if resp:
                print(f"Contenuto: {resp[:100]}")
        except:
            print("✓ Inviato (nessuna risposta)")
        
        sock.close()
        
        import time
        time.sleep(3)
        
    except Exception as e:
        print(f"✗ Errore: {e}")

print("\n" + "="*60)
print("  TEST SCONTRINO €0.00 - APERTURA CASSETTO")
print("="*60)
print("\nOSSERVA:")
print("1. La stampante stampa qualcosa?")
print("2. Il cassetto si apre?")
print("\n")

for i, xml in enumerate(xml_commands, 1):
    input(f"Premi INVIO per test {i}/{len(xml_commands)}...")
    test_comando(xml, i)

print("\n" + "="*60)
print("\n❓ RISULTATI:")
risposta = input("Quale test ha funzionato? (1-3 o 0): ")

if risposta.strip() in ['1','2','3']:
    print(f"\n✅ PERFETTO! Test #{risposta} funziona!")
    print("\nQuesto comando:")
    print("- Stampa qualcosa?")
    print("- Apre il cassetto?")
else:
    print("\n⚠️ Nessun test ha funzionato")
    print("\nPROSSIMO STEP:")
    print("Prova a fare uno scontrino dal PC e dimmi:")
    print("1. Che software usi?")
    print("2. Posso accedere al PC per 5 minuti?")

