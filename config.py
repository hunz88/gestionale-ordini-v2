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
    FILES_FOLDER = UPLOAD_FOLDER / 'files'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

    # Business settings (defaults)
    HOURLY_LABOR_RATE = float(os.getenv('HOURLY_LABOR_RATE', '15.0'))
    DEFAULT_MARGIN_PERCENTAGE = float(os.getenv('DEFAULT_MARGIN_PERCENTAGE', '30.0'))

    # Allowed extensions - TUTTI I TIPI DI FILE
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'webm', 'm4a', 'ogg', 'aac', 'flac'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'svg'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt', 'odt', 'ods', 'rtf'}
    ALLOWED_CAD_EXTENSIONS = {'stl', 'obj', 'step', 'stp', 'iges', 'igs', 'dxf', 'dwg', 'svg', 'ai', 'gcode', '3mf', 'amf'}
    ALLOWED_ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'}
    ALL_ALLOWED_EXTENSIONS = (ALLOWED_AUDIO_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS |
                             ALLOWED_DOCUMENT_EXTENSIONS | ALLOWED_CAD_EXTENSIONS |
                             ALLOWED_ARCHIVE_EXTENSIONS)

    # Server
    FLASK_PORT = int(os.getenv('FLASK_PORT', os.getenv('PORT', '5321')))
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')

    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create necessary directories
        Config.AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.PHOTOS_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.FILES_FOLDER.mkdir(parents=True, exist_ok=True)
        (Config.BASE_DIR / 'data').mkdir(parents=True, exist_ok=True)
