from models.recibo import Recibo

def recibo_existente(cliente_id, data_entrada, data_saida, mes_referencia, valor) -> bool:
    recibo_existente = Recibo.query.filter_by(
                    cliente_id=cliente_id,
                    data_entrada = data_entrada,
                    data_saida = data_saida,
                    mes_referencia = mes_referencia,
                    valor=valor
                    ).first()

    if recibo_existente:
        return True
    else:
        return False