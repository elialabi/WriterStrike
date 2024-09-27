import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    TIDB_HOST = os.environ.get('TIDB_HOST') or 'gateway01.eu-central-1.prod.aws.tidbcloud.com'
    TIDB_PORT = int(os.environ.get('TIDB_PORT') or 4000)
    TIDB_USER = os.environ.get('TIDB_USER') or 'coMP9hperszXc6a.root'
    TIDB_PASSWORD = os.environ.get('TIDB_PASSWORD') or 'AFRmGLwwVc05PDZO'
    TIDB_DATABASE = os.environ.get('TIDB_DATABASE') or 'feedback_system'