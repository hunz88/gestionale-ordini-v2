#!/usr/bin/env python3
"""
Test apertura cassetto - Multipli comandi
IP Stampante: 192.168.0.10
"""

import socket
import time
import logging

logging.basicConfig(level=logging.INFO)

class RCHPrintRT:
    def __init__(self, ip='192.168.0.10', port=9100, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.sock = None
        logging.info(f"Configurazione RCH: {ip}:{port}")
    
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.ip, self.port))
            logging.info(f"✓ Connesso a {self.ip}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"✗ Errore connessione: {e}")
            return False
    
    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
    
    def send_command(self, command):
        if not self.sock:
            if not self.connect():
                return None
        
        try:
            if isinstance(command, str):
                command = command.encode('utf-8')
            
            self.sock.sendall(command)
            
            try:
                response = self.sock.recv(1024)
                return response
            except socket.timeout:
                return b''
            
        except Exception as e:
            logging.error(f"✗ Errore: {e}")
            self.disconnect()
            return None
    
    def test_drawer_commands(self):
        """Prova vari comandi apertura cassetto"""
        
        commands = [
            ("ESC p 0 25 25", b'\x1B\x70\x00\x19\x19'),
            ("ESC p 0 50 50", b'\x1B\x70\x00\x32\x32'),
            ("ESC p 0 80 80", b'\x1B\x70\x00\x50\x50'),
            ("DLE DC4", b'\x10\x14\x01\x00\x05'),
            ("BEL", b'\x07'),
            ("ESC p 0 100 100", b'\x1B\x70\x00\x64\x64'),
        ]
        
        print("\n" + "="*60)
        print("  TEST APERTURA CASSETTO - 6 COMANDI DIVERSI")
        print("="*60)
        print("\nOSSERVA IL CASSETTO FISICAMENTE!\n")
        
        for i, (nome, cmd) in enumerate(commands, 1):
            print(f"\n[Test {i}/6] {nome}")
            print("Invio comando...", end=' ', flush=True)
            
            response = self.send_command(cmd)
            
            if response is not None:
                print("✓ Inviato")
                print("Aspetto 2 secondi...")
                time.sleep(2)
            else:
                print("✗ Errore invio")
        
        print("\n" + "="*60)
        print("\n❓ IL CASSETTO SI È APERTO CON UNO DI QUESTI COMANDI?")
        risposta = input("\nScrivi il numero (1-6) o 0 se nessuno: ")
        
        if risposta.strip() in ['1','2','3','4','5','6']:
            print(f"\n✅ PERFETTO! Il comando #{risposta} funziona!")
            print(f"Comando: {commands[int(risposta)-1][0]}")
            return int(risposta)
        else:
            print("\n❌ Nessun comando ha funzionato")
            return 0
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


if __name__ == '__main__':
    with RCHPrintRT(ip='192.168.0.10') as printer:
        risultato = printer.test_drawer_commands()
        
        if risultato > 0:
            print(f"\n✅ Usa il comando #{risultato} per il cassetto!")
        else:
            print("\n⚠️  Nessun comando ha funzionato.")
            print("Verifica:")
            print("1. Cassetto collegato alla stampante?")
            print("2. Cavo cassetto inserito correttamente?")
            print("3. Cassetto funziona dal menu stampante?")
