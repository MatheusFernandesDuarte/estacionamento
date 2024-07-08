from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes.db'
app.config['SECRET_KEY'] = 'mysecret'
db = SQLAlchemy(app)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    tipo_veiculo = db.Column(db.String(20), nullable=False)
    carro = db.Column(db.String(50), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    cpf_cnpj = db.Column(db.String(20), nullable=False)
    mensalista = db.Column(db.Boolean, default=False)
    vinte_quatro_horas = db.Column(db.Boolean, default=False)

class Recibo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    data_entrada = db.Column(db.DateTime, nullable=True)
    data_saida = db.Column(db.DateTime, nullable=True)
    mes_referencia = db.Column(db.String(7), nullable=True)  # Formato YYYY-MM
    valor = db.Column(db.Float, nullable=False)

    cliente = db.relationship('Cliente', backref=db.backref('recibos', lazy=True))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes')
def clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/cliente/novo', methods=['GET', 'POST'])
def novo_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        tipo_veiculo = request.form['tipo_veiculo']
        carro = request.form['carro']
        placa = request.form['placa']
        cpf_cnpj = request.form['cpf_cnpj']
        mensalista = 'mensalista' in request.form
        vinte_quatro_horas = 'vinte_quatro_horas' in request.form

        novo_cliente = Cliente(nome=nome, telefone=telefone, tipo_veiculo=tipo_veiculo,
                               carro=carro, placa=placa, cpf_cnpj=cpf_cnpj, mensalista=mensalista,
                               vinte_quatro_horas=vinte_quatro_horas)

        try:
            db.session.add(novo_cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'danger')

    return render_template('novo_cliente.html')

@app.route('/cliente/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = db.session.get(Cliente, id)

    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.telefone = request.form['telefone']
        cliente.tipo_veiculo = request.form['tipo_veiculo']
        cliente.carro = request.form['carro']
        cliente.placa = request.form['placa']
        cliente.cpf_cnpj = request.form['cpf_cnpj']
        cliente.mensalista = 'mensalista' in request.form
        cliente.vinte_quatro_horas = 'vinte_quatro_horas' in request.form

        try:
            db.session.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar cliente: {str(e)}', 'danger')

    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/cliente/<int:id>/deletar')
def deletar_cliente(id):
    cliente = db.session.get(Cliente, id)

    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente deletado com sucesso!', 'success')
        return redirect(url_for('clientes'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar cliente: {str(e)}', 'danger')

@app.route('/recibo/novo', methods=['GET', 'POST'])
def novo_recibo():
    clientes = Cliente.query.all()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        cliente = db.session.get(Cliente, cliente_id)
        
        if cliente.mensalista:
            mes_referencia = request.form['mes_referencia']
            valor = 150.0  # valor fixo para mensalistas
            novo_recibo = Recibo(cliente_id=cliente_id, mes_referencia=mes_referencia, valor=valor)
        else:
            diaria = 'diaria' in request.form
            if diaria:
                valor = 50.0  # valor fixo da diária
                novo_recibo = Recibo(cliente_id=cliente_id, valor=valor)
            else:
                data_entrada = datetime.strptime(request.form['data_entrada'], '%Y-%m-%dT%H:%M')
                data_saida = datetime.strptime(request.form['data_saida'], '%Y-%m-%dT%H:%M')
                horas = (data_saida - data_entrada).total_seconds() / 3600
                if horas > 5:
                    valor = 50.0  # diária fixa para mais de 5 horas
                else:
                    valor = int(horas) * 10.0  # valor por hora, truncando os minutos extras
                novo_recibo = Recibo(cliente_id=cliente_id, data_entrada=data_entrada, data_saida=data_saida, valor=valor)

        try:
            db.session.add(novo_recibo)
            db.session.commit()
            flash('Recibo gerado com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao gerar recibo: {str(e)}', 'danger')

    return render_template('novo_recibo.html', clientes=clientes)

@app.route('/recibos')
def recibos():
    recibos = Recibo.query.all()
    return render_template('recibos.html', recibos=recibos)

@app.route('/recibo/<int:id>/exportar')
def exportar_recibo(id):
    recibo = db.session.get(Recibo, id)
    cliente = db.session.get(Cliente, recibo.cliente_id)
    conteudo = (f"Recibo ID: {recibo.id}\n"
                f"Cliente: {cliente.nome}\n"
                f"Telefone: {cliente.telefone}\n"
                f"Tipo de Veículo: {cliente.tipo_veiculo}\n"
                f"Carro: {cliente.carro}\n"
                f"Placa: {cliente.placa}\n"
                f"CPF/CNPJ: {cliente.cpf_cnpj}\n"
                f"Data de Entrada: {recibo.data_entrada}\n"
                f"Data de Saída: {recibo.data_saida}\n"
                f"Mês de Referência: {recibo.mes_referencia}\n"
                f"Valor: {recibo.valor}\n")

    arquivo = f"recibo_{recibo.id}.txt"
    with open(arquivo, "w") as file:
        file.write(conteudo)

    return send_file(arquivo, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)