from datetime import datetime

from models.recibo import Recibo
from repository.database import db

def atualizar_recibos_futuros(cliente) -> None:
    hoje = datetime.now().strftime('%Y-%m')
    recibos_futuros = Recibo.query.filter(Recibo.cliente_id == cliente.id, Recibo.mes_referencia >= hoje, Recibo.pago == False).all()

    for recibo in recibos_futuros:
        recibo.valor = cliente.valor
        
    db.session.commit()