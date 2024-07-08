import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes.db'
app.config['SECRET_KEY'] = 'mysecret'
db = SQLAlchemy(app)

# Configuração do logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    tipo_veiculo = db.Column(db.String(20), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    cpf_cnpj = db.Column(db.String(20), nullable=False)
    mensalista = db.Column(db.Boolean, default=False)
    vinte_quatro_horas = db.Column(db.Boolean, default=False)

class Recibo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    data_entrada = db.Column(db.DateTime, nullable=True)
    data_saida = db.Column(db.DateTime, nullable=True)
    mes_referencia = db.Column(db.String(7), nullable=True)
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
        modelo = request.form['modelo']
        placa = request.form['placa']
        cpf_cnpj = request.form['cpf_cnpj']
        mensalista = 'mensalista' in request.form
        vinte_quatro_horas = 'vinte_quatro_horas' in request.form

        novo_cliente = Cliente(nome=nome, telefone=telefone, tipo_veiculo=tipo_veiculo,
                               modelo=modelo, placa=placa, cpf_cnpj=cpf_cnpj, mensalista=mensalista,
                               vinte_quatro_horas=vinte_quatro_horas)

        try:
            logger.debug(f"Adicionando cliente: {novo_cliente}")
            db.session.add(novo_cliente)
            db.session.commit()
            logger.debug("Cliente adicionado com sucesso")
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao adicionar cliente: {e}")
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'danger')

    return render_template('novo_cliente.html')

@app.route('/cliente/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = db.session.get(Cliente, id)

    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.telefone = request.form['telefone']
        cliente.tipo_veiculo = request.form['tipo_veiculo']
        cliente.modelo = request.form['modelo']
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

@app.route('/cliente/<int:id>/deletar', methods=['POST'])
def deletar_cliente(id):
    cliente = db.session.get(Cliente, id)
    
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('clientes'))

    # Verificar se o cliente possui recibos associados
    if cliente.recibos:
        flash('Não é possível deletar o cliente, pois ele possui recibos associados.', 'danger')
        return redirect(url_for('clientes'))

    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar cliente: {str(e)}', 'danger')
    
    return redirect(url_for('clientes'))

@app.route('/recibo/novo', methods=['GET', 'POST'])
def novo_recibo():
    clientes = Cliente.query.all()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        cliente = db.session.get(Cliente, cliente_id)
        
        if cliente.mensalista:
            mes_referencia = request.form['mes_referencia']
            if not mes_referencia:
                flash('Mês de referência é necessário para mensalistas.', 'danger')
                return redirect(url_for('novo_recibo'))
            if cliente.tipo_veiculo == 'carro pequeno':
                valor = 320.0
            elif cliente.tipo_veiculo == 'moto':
                valor = 150.0
            elif cliente.tipo_veiculo == 'SUV':
                valor = 350.0
            else:
                valor = 150.0  # Valor padrão para outros tipos de veículos, se necessário
            novo_recibo = Recibo(cliente_id=cliente_id, mes_referencia=mes_referencia, valor=valor)
        elif cliente.vinte_quatro_horas:
            valor = 400.0  # Valor fixo para clientes 24h
            mes_referencia = request.form['mes_referencia']
            if not mes_referencia:
                flash('Mês de referência é necessário para clientes 24h.', 'danger')
                return redirect(url_for('novo_recibo'))
            novo_recibo = Recibo(cliente_id=cliente_id, mes_referencia=mes_referencia, valor=valor)
        else:
            diaria = 'diaria' in request.form
            if diaria:
                data_diaria = request.form['data_diaria']
                if not data_diaria:
                    flash('Data é necessária para recibo de diária.', 'danger')
                    return redirect(url_for('novo_recibo'))
                data_entrada = datetime.strptime(data_diaria, '%Y-%m-%d')
                valor = 50.0  # valor fixo da diária
                novo_recibo = Recibo(cliente_id=cliente_id, data_entrada=data_entrada, valor=valor)
            else:
                data_entrada = request.form.get('data_entrada')
                data_saida = request.form.get('data_saida')
                if data_entrada and data_saida:
                    data_entrada = datetime.strptime(data_entrada, '%Y-%m-%dT%H:%M')
                    data_saida = datetime.strptime(data_saida, '%Y-%m-%dT%H:%M')
                    if data_entrada > data_saida:
                        flash('A data de entrada não pode ser posterior à data de saída.', 'danger')
                        return redirect(url_for('novo_recibo'))
                    horas = (data_saida - data_entrada).total_seconds() / 3600
                    if horas > 5:
                        valor = 50.0  # diária fixa para mais de 5 horas
                    else:
                        valor = 10.0 + int(horas) * 10.0  # valor por hora, começando em 10 reais
                    novo_recibo = Recibo(cliente_id=cliente_id, data_entrada=data_entrada, data_saida=data_saida, valor=valor)
                else:
                    flash('Datas de entrada e saída são necessárias.', 'danger')
                    return redirect(url_for('novo_recibo'))

        try:
            db.session.add(novo_recibo)
            db.session.commit()
            flash('Recibo gerado com sucesso!', 'success')
            return redirect(url_for('recibos'))
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
    
    # Criar o diretório do cliente
    client_folder = secure_filename(cliente.nome)
    base_path = os.path.join('files', client_folder)
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
     # Determinar o nome do arquivo
    if recibo.mes_referencia:
        file_name = f"recibo_{recibo.mes_referencia}.txt"
    elif recibo.data_entrada and recibo.data_saida:
        file_name = f"recibo_{recibo.data_entrada.strftime('%Y-%m-%d')}_a_{recibo.data_saida.strftime('%Y-%m-%d')}.txt"
    elif recibo.data_entrada:
        file_name = f"recibo_{recibo.data_entrada.strftime('%Y-%m-%d')}.txt"
    else:
        file_name = f"recibo_{recibo.id}.txt"

    # Caminho completo do arquivo
    file_path = os.path.join(base_path, file_name)

    conteudo = (f"Recibo ID: {recibo.id}\n"
                f"Cliente: {cliente.nome}\n"
                f"Telefone: {cliente.telefone}\n"
                f"Tipo de Veículo: {cliente.tipo_veiculo}\n"
                f"Modelo: {cliente.modelo}\n"
                f"Placa: {cliente.placa}\n"
                f"CPF/CNPJ: {cliente.cpf_cnpj}\n"
                f"Data de Entrada: {recibo.data_entrada}\n"
                f"Data de Saída: {recibo.data_saida}\n"
                f"Mês de Referência: {recibo.mes_referencia}\n"
                f"Valor: {recibo.valor}\n")

    with open(file_path, "w") as file:
        file.write(conteudo)

    return send_file(file_path, as_attachment=True)

@app.route('/recibo/<int:id>/editar', methods=['GET', 'POST'])
def editar_recibo(id):
    recibo = db.session.get(Recibo, id)
    clientes = Cliente.query.all()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        recibo.cliente_id = cliente_id
        recibo.cliente = db.session.get(Cliente, cliente_id)
        
        if recibo.cliente.mensalista:
            recibo.mes_referencia = request.form['mes_referencia']
            recibo.data_entrada = None
            recibo.data_saida = None
            recibo.valor = 150.0  # valor fixo para mensalistas
        else:
            diaria = 'diaria' in request.form
            if diaria:
                data_diaria = request.form['data_diaria']
                if not data_diaria:
                    flash('Data é necessária para recibo de diária.', 'danger')
                    return redirect(url_for('editar_recibo', id=id))
                recibo.data_entrada = datetime.strptime(data_diaria, '%Y-%m-%d')
                recibo.data_saida = None
                recibo.valor = 50.0  # valor fixo da diária
            else:
                data_entrada = request.form.get('data_entrada')
                data_saida = request.form.get('data_saida')
                if data_entrada and data_saida:
                    data_entrada = datetime.strptime(data_entrada, '%Y-%m-%dT%H:%M')
                    data_saida = datetime.strptime(data_saida, '%Y-%m-%dT%H:%M')
                    if data_entrada > data_saida:
                        flash('A data de entrada não pode ser posterior à data de saída.', 'danger')
                        return redirect(url_for('editar_recibo', id=id))
                    horas = (data_saida - data_entrada).total_seconds() / 3600
                    if horas > 5:
                        recibo.valor = 50.0  # diária fixa para mais de 5 horas
                    else:
                        recibo.valor = 10.0 + int(horas) * 10.0  # valor por hora, começando em 10 reais
                    recibo.data_entrada = data_entrada
                    recibo.data_saida = data_saida
                else:
                    flash('Datas de entrada e saída são necessárias.', 'danger')
                    return redirect(url_for('editar_recibo', id=id))

        try:
            db.session.commit()
            flash('Recibo atualizado com sucesso!', 'success')
            return redirect(url_for('recibos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar recibo: {str(e)}', 'danger')

    return render_template('editar_recibo.html', recibo=recibo, clientes=clientes)

@app.route('/recibo/<int:id>/deletar', methods=['POST'])
def deletar_recibo(id):
    recibo = db.session.get(Recibo, id)

    try:
        db.session.delete(recibo)
        db.session.commit()
        flash('Recibo deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar recibo: {str(e)}', 'danger')
    
    return redirect(url_for('recibos'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)