import logging
import os

from flask import Flask, render_template
from flask_migrate import Migrate

from src.repository.database import db
from src.utils.backups import backup_database
from src.controllers.cliente_controller import cliente_bp
from src.controllers.recibo_controller import recibo_bp

app = Flask(__name__)

app.template_folder = os.path.join(os.path.abspath(''), 'src')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'SECRET_KEY_WEBSOCKET'

db.init_app(app)

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

''' Registrando as blueprints '''
app.register_blueprint(cliente_bp)
app.register_blueprint(recibo_bp)

''' Configurando o logger '''
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('views/index.html')

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 5000
    app.run(debug=True, host=host, port=port)

    with app.app_context():
        backup_database()