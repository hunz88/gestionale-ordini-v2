import socket
import time

def test_xml_command(xml, descrizione):
    print(f"\n[TEST] {descrizione}")
    print("Invio...", end=' ', flush=True)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(('192.168.0.10', 9100))
        sock.sendall(xml.encode('utf-8'))
        
        try:
            resp = sock.recv(1024)
            print(f"✓ Risposta: {len(resp)} bytes")
        except:
            print("✓ Inviato (no risposta)")
        
        sock.close()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"✗ Errore: {e}")
        return False

print("="*60)
print("  TEST COMANDI XML RCH - APERTURA CASSETTO")
print("="*60)
print("\nOSSERVA IL CASSETTO!\n")

# Varianti comando apertura cassetto XML per RCH
comandi = [
    # Variante 1
    ('''<?xml version="1.0" encoding="UTF-8"?>
<printerCommand>
  <openDrawer/>
</printerCommand>''', "XML Standard - openDrawer"),

    # Variante 2
    ('''<?xml version="1.0" encoding="UTF-8"?>
<printerFiscal>
  <openDrawer/>
</printerFiscal>''', "XML Fiscale - openDrawer"),

    # Variante 3
    ('''<?xml version="1.0"?>
<command>
  <openCashDrawer/>
</command>''', "XML - openCashDrawer"),

    # Variante 4 - Pulse
    ('''<?xml version="1.0" encoding="UTF-8"?>
<printerCommand>
  <directIO command="27" data="112,0,25,25"/>
</printerCommand>''', "XML DirectIO - ESC p"),

    # Variante 5 - RCH Specific
    ('''<?xml version="1.0" encoding="UTF-8"?>
<root>
  <openDrawer drawer="1"/>
</root>''', "XML Root - drawer 1"),
]

for i, (xml, desc) in enumerate(comandi, 1):
    print(f"\n{'='*60}")
    print(f"Comando {i}/{len(comandi)}")
    test_xml_command(xml, desc)

print("\n" + "="*60)
risposta = input("\n❓ IL CASSETTO SI È APERTO? Scrivi numero (1-5) o 0: ")

if risposta.strip() in ['1','2','3','4','5']:
    print(f"\n✅ TROVATO! Comando #{risposta} funziona!")
else:
    print("\n⚠️ Nessun comando XML ha funzionato")
    print("\nPROSSIMO STEP:")
    print("1. Cercare manuale RCH Print RT")
    print("2. Verificare comando apertura cassetto dal PC attuale")
    print("3. Contattare supporto RCH")

