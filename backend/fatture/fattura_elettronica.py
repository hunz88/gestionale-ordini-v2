#!/usr/bin/env python3
"""
Modulo per la generazione di fatture elettroniche in formato XML FatturaPA v1.2.1
Conforme alle specifiche dell'Agenzia delle Entrate italiana
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, List, Optional
import os


class FatturaElettronicaXML:
    """Generatore di file XML per fatture elettroniche FatturaPA"""

    def __init__(self, dati_cedente: Optional[Dict] = None):
        """
        Inizializza il generatore con i dati del cedente

        Args:
            dati_cedente: Dizionario con i dati dell'esercizio (opzionale, usa config)
        """
        # Carica configurazione da file
        try:
            from backend.fatture.config_cedente import DATI_CEDENTE
            self.CEDENTE = DATI_CEDENTE.copy()
        except ImportError:
            # Fallback a dati vuoti se config non trovato
            self.CEDENTE = {
                'partita_iva': '',
                'codice_fiscale': '',
                'denominazione': '',
                'regime_fiscale': 'RF01',
                'indirizzo': '',
                'cap': '',
                'citta': '',
                'provincia': '',
                'nazione': 'IT',
                'telefono': '',
                'email': ''
            }

        # Sovrascrivi con dati passati se presenti
        if dati_cedente:
            self.CEDENTE.update(dati_cedente)

    def genera_xml(self, fattura: Dict, cliente: Dict, righe: List[Dict],
                   output_dir: str = '/home/sunsetbar/gestionale-ordini-v2/fatture_xml') -> str:
        """
        Genera il file XML della fattura elettronica

        Args:
            fattura: Dict con dati fattura (numero, anno, data_emissione, etc.)
            cliente: Dict con dati cliente
            righe: Lista di dict con le righe della fattura
            output_dir: Directory di output per il file XML

        Returns:
            Percorso completo del file XML generato
        """
        # Crea struttura XML
        root = ET.Element('p:FatturaElettronica', {
            'versione': 'FPR12',
            'xmlns:ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xmlns:p': 'http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2 http://www.fatturapa.gov.it/export/fatturazione/sdi/fatturapa/v1.2/Schema_del_file_xml_FatturaPA_versione_1.2.xsd'
        })

        # === HEADER ===
        header = ET.SubElement(root, 'FatturaElettronicaHeader')
        self._genera_dati_trasmissione(header, cliente)
        self._genera_cedente_prestatore(header)
        self._genera_cessionario_committente(header, cliente)

        # === BODY ===
        body = ET.SubElement(root, 'FatturaElettronicaBody')
        self._genera_dati_generali(body, fattura)
        self._genera_dati_beni_servizi(body, righe, fattura)

        # Genera nome file secondo standard: IT[PartitaIVA]_[Progressivo5cifre].xml
        partita_iva = self.CEDENTE['partita_iva'].replace('IT', '')
        progressivo = str(fattura['numero']).zfill(5)
        nome_file = f"IT{partita_iva}_{progressivo}.xml"

        # Crea directory anno se non esiste
        anno_dir = os.path.join(output_dir, str(fattura['anno']))
        os.makedirs(anno_dir, exist_ok=True)

        # Percorso completo
        percorso_file = os.path.join(anno_dir, nome_file)

        # Formattazione XML leggibile
        xml_string = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(
            indent='  ', encoding='UTF-8'
        )

        # Salva file
        with open(percorso_file, 'wb') as f:
            f.write(xml_string)

        return percorso_file

    def _genera_dati_trasmissione(self, header: ET.Element, cliente: Dict):
        """Genera sezione DatiTrasmissione"""
        dati_trasm = ET.SubElement(header, 'DatiTrasmissione')

        # IdTrasmittente
        id_trasm = ET.SubElement(dati_trasm, 'IdTrasmittente')
        ET.SubElement(id_trasm, 'IdPaese').text = 'IT'
        ET.SubElement(id_trasm, 'IdCodice').text = self.CEDENTE['partita_iva'].replace('IT', '')

        # ProgressivoInvio (timestamp univoco)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        ET.SubElement(dati_trasm, 'ProgressivoInvio').text = timestamp

        # FormatoTrasmissione
        ET.SubElement(dati_trasm, 'FormatoTrasmissione').text = 'FPR12'

        # CodiceDestinatario o PECDestinatario
        if cliente.get('codice_destinatario') and cliente['codice_destinatario'] != '0000000':
            ET.SubElement(dati_trasm, 'CodiceDestinatario').text = cliente['codice_destinatario']
        elif cliente.get('pec'):
            ET.SubElement(dati_trasm, 'PECDestinatario').text = cliente['pec']
        else:
            # Default per invio tramite codice generico
            ET.SubElement(dati_trasm, 'CodiceDestinatario').text = '0000000'

    def _genera_cedente_prestatore(self, header: ET.Element):
        """Genera sezione CedentePrestatore (dati dell'esercizio)"""
        cedente = ET.SubElement(header, 'CedentePrestatore')

        # DatiAnagrafici
        dati_anag = ET.SubElement(cedente, 'DatiAnagrafici')
        id_fiscale = ET.SubElement(dati_anag, 'IdFiscaleIVA')
        ET.SubElement(id_fiscale, 'IdPaese').text = 'IT'
        ET.SubElement(id_fiscale, 'IdCodice').text = self.CEDENTE['partita_iva'].replace('IT', '')

        if self.CEDENTE.get('codice_fiscale'):
            ET.SubElement(dati_anag, 'CodiceFiscale').text = self.CEDENTE['codice_fiscale']

        anagrafica = ET.SubElement(dati_anag, 'Anagrafica')
        ET.SubElement(anagrafica, 'Denominazione').text = self.CEDENTE['denominazione']

        ET.SubElement(dati_anag, 'RegimeFiscale').text = self.CEDENTE['regime_fiscale']

        # Sede
        sede = ET.SubElement(cedente, 'Sede')
        ET.SubElement(sede, 'Indirizzo').text = self.CEDENTE['indirizzo']
        ET.SubElement(sede, 'CAP').text = self.CEDENTE['cap']
        ET.SubElement(sede, 'Comune').text = self.CEDENTE['citta']
        ET.SubElement(sede, 'Provincia').text = self.CEDENTE['provincia']
        ET.SubElement(sede, 'Nazione').text = self.CEDENTE['nazione']

        # Contatti (opzionali)
        if self.CEDENTE.get('telefono') or self.CEDENTE.get('email'):
            contatti = ET.SubElement(cedente, 'Contatti')
            if self.CEDENTE.get('telefono'):
                ET.SubElement(contatti, 'Telefono').text = self.CEDENTE['telefono']
            if self.CEDENTE.get('email'):
                ET.SubElement(contatti, 'Email').text = self.CEDENTE['email']

    def _genera_cessionario_committente(self, header: ET.Element, cliente: Dict):
        """Genera sezione CessionarioCommittente (dati cliente)"""
        cessionario = ET.SubElement(header, 'CessionarioCommittente')

        # DatiAnagrafici
        dati_anag = ET.SubElement(cessionario, 'DatiAnagrafici')

        # IdFiscaleIVA (solo se azienda con P.IVA)
        if cliente.get('partita_iva'):
            id_fiscale = ET.SubElement(dati_anag, 'IdFiscaleIVA')
            # Estrai paese dalla P.IVA se presente (es: IT12345678901)
            piva = cliente['partita_iva']
            if len(piva) > 11:
                paese = piva[:2]
                codice = piva[2:]
            else:
                paese = 'IT'
                codice = piva
            ET.SubElement(id_fiscale, 'IdPaese').text = paese
            ET.SubElement(id_fiscale, 'IdCodice').text = codice

        # CodiceFiscale
        ET.SubElement(dati_anag, 'CodiceFiscale').text = cliente['codice_fiscale']

        # Anagrafica
        anagrafica = ET.SubElement(dati_anag, 'Anagrafica')
        if cliente.get('ragione_sociale'):
            ET.SubElement(anagrafica, 'Denominazione').text = cliente['ragione_sociale']
        else:
            ET.SubElement(anagrafica, 'Nome').text = cliente.get('nome', '')
            ET.SubElement(anagrafica, 'Cognome').text = cliente.get('cognome', '')

        # Sede
        sede = ET.SubElement(cessionario, 'Sede')
        ET.SubElement(sede, 'Indirizzo').text = cliente['indirizzo']
        ET.SubElement(sede, 'CAP').text = cliente['cap']
        ET.SubElement(sede, 'Comune').text = cliente['citta']
        if cliente.get('provincia'):
            ET.SubElement(sede, 'Provincia').text = cliente['provincia']
        ET.SubElement(sede, 'Nazione').text = cliente.get('nazione', 'IT')

    def _genera_dati_generali(self, body: ET.Element, fattura: Dict):
        """Genera sezione DatiGenerali"""
        dati_gen = ET.SubElement(body, 'DatiGenerali')
        dati_doc = ET.SubElement(dati_gen, 'DatiGeneraliDocumento')

        # TipoDocumento (TD01 = Fattura, TD04 = Nota di Credito)
        tipo_doc = fattura.get('tipo_documento', 'TD01')
        ET.SubElement(dati_doc, 'TipoDocumento').text = tipo_doc

        # Divisa
        ET.SubElement(dati_doc, 'Divisa').text = 'EUR'

        # Data
        if isinstance(fattura['data_emissione'], str):
            data_str = fattura['data_emissione']
        else:
            data_str = fattura['data_emissione'].strftime('%Y-%m-%d')
        ET.SubElement(dati_doc, 'Data').text = data_str

        # Numero
        numero_fattura = f"{fattura['anno']}/{fattura['numero']}"
        ET.SubElement(dati_doc, 'Numero').text = numero_fattura

        # Importo Totale Documento
        ET.SubElement(dati_doc, 'ImportoTotaleDocumento').text = f"{fattura['totale']:.2f}"

        # DatiDocumentiCorrelati - per Note di Credito
        if tipo_doc == 'TD04' and fattura.get('fattura_riferimento'):
            dati_correlati = ET.SubElement(dati_gen, 'DatiFattureCollegate')
            rif = fattura['fattura_riferimento']

            # ID del documento collegato
            ET.SubElement(dati_correlati, 'IdDocumento').text = f"{rif['anno']}/{rif['numero']}"

            # Data del documento collegato
            if isinstance(rif['data_emissione'], str):
                data_rif_str = rif['data_emissione']
            else:
                data_rif_str = rif['data_emissione'].strftime('%Y-%m-%d')
            ET.SubElement(dati_correlati, 'Data').text = data_rif_str

    def _genera_dati_beni_servizi(self, body: ET.Element, righe: List[Dict], fattura: Dict):
        """Genera sezione DatiBeniServizi con righe fattura e riepilogo IVA"""
        dati_beni = ET.SubElement(body, 'DatiBeniServizi')

        # Righe dettaglio
        for idx, riga in enumerate(righe, start=1):
            dettaglio = ET.SubElement(dati_beni, 'DettaglioLinee')
            ET.SubElement(dettaglio, 'NumeroLinea').text = str(idx)
            ET.SubElement(dettaglio, 'Descrizione').text = riga['descrizione']
            ET.SubElement(dettaglio, 'Quantita').text = f"{riga['quantita']:.2f}"
            ET.SubElement(dettaglio, 'PrezzoUnitario').text = f"{riga['prezzo_unitario']:.2f}"
            ET.SubElement(dettaglio, 'PrezzoTotale').text = f"{riga['totale_riga']:.2f}"
            ET.SubElement(dettaglio, 'AliquotaIVA').text = f"{riga['aliquota_iva']:.2f}"

        # Calcola riepilogo IVA per aliquota
        riepilogo_iva = {}
        for riga in righe:
            aliquota = riga['aliquota_iva']
            if aliquota not in riepilogo_iva:
                riepilogo_iva[aliquota] = {'imponibile': 0, 'iva': 0}

            imponibile_riga = riga['totale_riga']
            iva_riga = imponibile_riga * (aliquota / 100)

            riepilogo_iva[aliquota]['imponibile'] += imponibile_riga
            riepilogo_iva[aliquota]['iva'] += iva_riga

        # DatiRiepilogo per ogni aliquota
        for aliquota, dati in riepilogo_iva.items():
            riepilogo = ET.SubElement(dati_beni, 'DatiRiepilogo')
            ET.SubElement(riepilogo, 'AliquotaIVA').text = f"{aliquota:.2f}"
            ET.SubElement(riepilogo, 'ImponibileImporto').text = f"{dati['imponibile']:.2f}"
            ET.SubElement(riepilogo, 'Imposta').text = f"{dati['iva']:.2f}"
            ET.SubElement(riepilogo, 'EsigibilitaIVA').text = 'I'  # I=Immediata


def valida_partita_iva(piva: str) -> bool:
    """
    Valida formato Partita IVA italiana

    Args:
        piva: Partita IVA da validare (con o senza IT)

    Returns:
        True se valida, False altrimenti
    """
    # Rimuovi prefisso IT se presente
    piva = piva.replace('IT', '').replace('it', '')

    # Deve essere di 11 cifre numeriche
    if not piva.isdigit() or len(piva) != 11:
        return False

    return True


def valida_codice_fiscale(cf: str) -> bool:
    """
    Valida formato Codice Fiscale italiano (validazione base lunghezza)

    Args:
        cf: Codice fiscale da validare

    Returns:
        True se formato corretto, False altrimenti
    """
    cf = cf.upper().strip()

    # CF può essere 11 cifre (P.IVA) o 16 caratteri alfanumerici
    if len(cf) == 11 and cf.isdigit():
        return True
    elif len(cf) == 16 and cf.isalnum():
        return True

    return False


def valida_codice_sdi(codice: str) -> bool:
    """
    Valida Codice Destinatario SDI

    Args:
        codice: Codice SDI da validare

    Returns:
        True se valido, False altrimenti
    """
    # Codice SDI deve essere 7 caratteri alfanumerici
    # 0000000 è il codice per invio generico
    if not codice or len(codice) != 7:
        return False

    return codice.isalnum()
