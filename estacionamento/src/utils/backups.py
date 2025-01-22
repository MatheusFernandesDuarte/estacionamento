import os
import shutil

from flask import current_app
from sqlalchemy.event import listens_for
from datetime import datetime

from models.cliente import Cliente
from models.recibo import Recibo

def backup_database():
    db_path = os.path.join(current_app.instance_path, 'database.db')

    if os.path.exists(db_path):
        now = datetime.now()
        backup_dir = f"backups/{now.strftime('%m-%Y')}"

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        backup_path = os.path.join(backup_dir, f"backup_{now.strftime('Dia_%d_Horario_%H-%M-%S')}.db")
        shutil.copy2(db_path, backup_path)
        print(f"Backup criado: {backup_path}")

    else:
        print(f"Erro: {db_path} não encontrado. Backup não realizado.")

@listens_for(Cliente, 'after_insert')
@listens_for(Cliente, 'after_update')
@listens_for(Cliente, 'after_delete')
@listens_for(Recibo, 'after_insert')
@listens_for(Recibo, 'after_update')
@listens_for(Recibo, 'after_delete')
def receive_after_change(mapper, connection, target):
    print(1)
    backup_database()

if __name__ == '__main__':
    from estacionamento.src.app import app  # Importa o app para garantir que o contexto está ativo
