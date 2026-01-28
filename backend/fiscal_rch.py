#!/usr/bin/env python3
"""
Modulo per gestione stampante fiscale RCH Print RT via rete Ethernet/WiFi
IP: 192.168.0.10
"""

import socket
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class RCHPrintRT:
    """Gestione stampante fiscale RCH Print RT via rete"""
    
    def __init__(self, ip='192.168.0.10', port=9100, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.sock = None
        logging.info(f"Configurazione RCH: {ip}:{port}")
    
    def connect(self):
        """Connessione alla stampante"""
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
        """Chiude connessione"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
    
    def send_command(self, command):
        """Invia comando alla stampante"""
        if not self.sock:
            if not self.connect():
                return None
        
        try:
            if isinstance(command, str):
                command = command.encode('utf-8')
            
            self.sock.sendall(command)
            logging.info(f"→ Comando inviato ({len(command)} bytes)")
            
            try:
                response = self.sock.recv(1024)
                return response
            except socket.timeout:
                return b''
            
        except Exception as e:
            logging.error(f"✗ Errore: {e}")
            self.disconnect()
            return None
    
    def open_drawer(self):
        """Apre cassetto portamonete"""
        logging.info("Apertura cassetto...")
        # Comando ESC/POS standard
        command = b'\x1B\x70\x00\x19\x19'
        response = self.send_command(command)
        
        if response is not None:
            logging.info("✓ Cassetto aperto")
            return True
        else:
            logging.error("✗ Errore apertura cassetto")
            return False
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# TEST
if __name__ == '__main__':
    print("\n" + "="*50)
    print("  TEST STAMPANTE RCH - 192.168.0.10")
    print("="*50 + "\n")
    
    with RCHPrintRT(ip='192.168.0.10') as printer:
        print("\n✓ Connessione OK!")
        print("\nPremi INVIO per testare apertura cassetto...")
        input()
        
        if printer.open_drawer():
            print("\n✓ Cassetto dovrebbe essere aperto!")
        else:
            print("\n✗ Errore apertura cassetto")
    
    print("\n" + "="*50)
    print("  TEST COMPLETATO")
    print("="*50 + "\n")
