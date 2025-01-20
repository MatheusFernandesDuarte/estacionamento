from datetime import datetime

from src.models.recibo import Recibo
from src.repository.database import db

def apagar_recibos_futuros(cliente) -> None:
    hoje = datetime.now().strftime('%Y-%m')
    recibos_futuros = Recibo.query.filter(Recibo.cliente_id == cliente.id, Recibo.mes_referencia >= hoje).all()

    for recibo in recibos_futuros:
        db.session.delete(recibo)
        
    db.session.commit()