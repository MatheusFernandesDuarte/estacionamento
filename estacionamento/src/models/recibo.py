from repository.database import db

class Recibo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    data_entrada = db.Column(db.DateTime, nullable=True)
    data_saida = db.Column(db.DateTime, nullable=True)
    mes_referencia = db.Column(db.String(7), nullable=True)
    valor = db.Column(db.Float, nullable=False)
    pago = db.Column(db.Boolean, default=False)
    cliente = db.relationship('Cliente', backref=db.backref('recibos', lazy=True))