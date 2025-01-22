from datetime import datetime

from repository.database import db

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    tipo_veiculo = db.Column(db.String(20), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    cpf_cnpj = db.Column(db.String(20), nullable=False)
    data_vencimento = db.Column(db.String(11), nullable=True)

    email = db.Column(db.String(20))
    endereco = db.Column(db.String(50))
    valor = db.Column(db.Float)

    mensalista = db.Column(db.Boolean, default=False)
    vinte_quatro_horas = db.Column(db.Boolean, default=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)