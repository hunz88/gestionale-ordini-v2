import os
import re
from pathlib import Path
from config import Config

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class WhisperService:
    """Service for handling Whisper API transcriptions"""

    def __init__(self, api_key=None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key

    def transcribe_audio(self, audio_file_path, language="it"):
        """
        Transcribe audio file using Whisper API

        Args:
            audio_file_path: Path to audio file
            language: Language code (default: "it" for Italian)

        Returns:
            str: Transcribed text or mock transcription if API not available
        """
        # Check if file exists
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # If API is available and configured, use it
        if OPENAI_AVAILABLE and self.api_key:
            try:
                with open(audio_file_path, "rb") as audio_file:
                    transcript = openai.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language
                    )
                return transcript.text
            except Exception as e:
                print(f"Error transcribing audio: {e}")
                return self._mock_transcription(audio_file_path)
        else:
            # Return mock transcription if API not available
            return self._mock_transcription(audio_file_path)

    def _mock_transcription(self, audio_file_path):
        """
        Generate mock transcription when API is not available

        Args:
            audio_file_path: Path to audio file (used for filename-based mocking)

        Returns:
            str: Mock transcription text
        """
        filename = Path(audio_file_path).stem.lower()

        # Generate different mock transcriptions based on filename or context
        if 'project' in filename or 'progetto' in filename:
            return "Devo fare 10 portachiavi personalizzati in PLA rosso per il cliente Marco Rossi. Dimensioni circa 5 centimetri, con il logo della loro azienda. Prevedo circa 3 ore di stampa."
        elif 'material' in filename or 'materiale' in filename:
            return "Il PLA bianco Sunlu funziona bene a 210 gradi, velocità 60mm/s. Ottima adesione e finitura liscia."
        elif 'quote' in filename or 'preventivo' in filename:
            return "Il cliente vuole 5 targhe personalizzate in acrilico trasparente, incisione laser, misure 20x30 cm. Budget indicativo 150 euro."
        else:
            return "Nota vocale di test. Questa è una trascrizione simulata perché l'API Whisper non è configurata. Per abilitare le trascrizioni reali, configura la chiave API OpenAI nel file .env."

    def parse_project_info(self, transcription):
        """
        Parse project information from transcription using regex

        Args:
            transcription: Transcribed text

        Returns:
            dict: Extracted information (customer, material, quantity, etc.)
        """
        info = {
            'customer_name': None,
            'quantity': 1,
            'material': None,
            'estimated_hours': None,
            'description': transcription
        }

        # Extract customer name (look for "cliente" or "per" followed by name)
        customer_patterns = [
            r'(?:cliente|per il cliente|per)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'(?:signor[ae]?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        for pattern in customer_patterns:
            match = re.search(pattern, transcription)
            if match:
                info['customer_name'] = match.group(1)
                break

        # Extract quantity (numbers followed by pieces/pezzi/unità)
        quantity_pattern = r'(\d+)\s+(?:pezzi|pz|unità|portachiavi|targhe|oggetti)'
        match = re.search(quantity_pattern, transcription, re.IGNORECASE)
        if match:
            info['quantity'] = int(match.group(1))

        # Extract material hints
        materials_map = {
            'pla': ['pla', 'polilattide'],
            'petg': ['petg'],
            'abs': ['abs'],
            'tpu': ['tpu', 'flessibile'],
            'wood_laser': ['legno', 'compensato', 'mdf'],
            'acrylic_laser': ['acrilico', 'plexiglass', 'perspex'],
        }

        transcription_lower = transcription.lower()
        for material_type, keywords in materials_map.items():
            if any(keyword in transcription_lower for keyword in keywords):
                info['material'] = material_type
                break

        # Extract estimated time (hours)
        time_pattern = r'(\d+(?:[.,]\d+)?)\s+(?:ore|ora|h)'
        match = re.search(time_pattern, transcription, re.IGNORECASE)
        if match:
            time_str = match.group(1).replace(',', '.')
            info['estimated_hours'] = float(time_str)

        return info

    def parse_material_info(self, transcription):
        """
        Parse material information from transcription

        Args:
            transcription: Transcribed text

        Returns:
            dict: Extracted material settings
        """
        info = {
            'temperature': None,
            'speed': None,
            'notes': transcription
        }

        # Extract temperature
        temp_pattern = r'(\d{3})\s*(?:gradi|°|℃|C)'
        match = re.search(temp_pattern, transcription)
        if match:
            info['temperature'] = int(match.group(1))

        # Extract speed
        speed_pattern = r'(\d+)\s*(?:mm/s|millimetri al secondo)'
        match = re.search(speed_pattern, transcription)
        if match:
            info['speed'] = int(match.group(1))

        return info

    def parse_quote_info(self, transcription):
        """
        Parse quote information from transcription

        Args:
            transcription: Transcribed text

        Returns:
            dict: Extracted quote information
        """
        info = self.parse_project_info(transcription)

        # Extract budget/price hints
        price_pattern = r'(?:budget|prezzo|costo).*?(\d+(?:[.,]\d+)?)\s*(?:euro|€|eur)'
        match = re.search(price_pattern, transcription, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '.')
            info['estimated_price'] = float(price_str)

        return info


# Singleton instance
_whisper_service = None


def get_whisper_service():
    """Get singleton Whisper service instance"""
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service
