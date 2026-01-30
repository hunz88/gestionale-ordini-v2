import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # Base directory
    BASE_DIR = Path(__file__).parent.absolute()

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/data/printshub.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

    # Upload folders
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    AUDIO_FOLDER = UPLOAD_FOLDER / 'audio'
    PHOTOS_FOLDER = UPLOAD_FOLDER / 'photos'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

    # Business settings (defaults)
    HOURLY_LABOR_RATE = float(os.getenv('HOURLY_LABOR_RATE', '15.0'))
    DEFAULT_MARGIN_PERCENTAGE = float(os.getenv('DEFAULT_MARGIN_PERCENTAGE', '30.0'))

    # Allowed extensions
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'webm', 'm4a', 'ogg'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Server
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5321'))
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')

    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create necessary directories
        Config.AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.PHOTOS_FOLDER.mkdir(parents=True, exist_ok=True)
        (Config.BASE_DIR / 'data').mkdir(parents=True, exist_ok=True)
