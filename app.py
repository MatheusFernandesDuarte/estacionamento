from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import logging
from werkzeug.utils import secure_filename
import builtins
import os

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
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Recibo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    data_entrada = db.Column(db.DateTime, nullable=True)
    data_saida = db.Column(db.DateTime, nullable=True)
    mes_referencia = db.Column(db.String(7), nullable=True)
    valor = db.Column(db.Float, nullable=False)
    pago = db.Column(db.Boolean, default=False)
    cliente = db.relationship('Cliente', backref=db.backref('recibos', lazy=True))

class Plano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_veiculo = db.Column(db.String(20), nullable=False, unique=True)
    valor = db.Column(db.Float, nullable=False)

class Configuracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor_hora = db.Column(db.Float, nullable=False, default=10.0)
    valor_diaria = db.Column(db.Float, nullable=False, default=50.0)

@app.template_global()
def str(value):
    return builtins.str(value)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes')
def clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

def inicializar_planos():
    tipos_veiculos = ['carro pequeno', 'SUV', 'moto', 'vinte_quatro_horas']
    valores_iniciais = [320.0, 350.0, 150.0, 400.0]

    for tipo, valor in zip(tipos_veiculos, valores_iniciais):
        plano = Plano.query.filter_by(tipo_veiculo=tipo).first()
        if not plano:
            novo_plano = Plano(tipo_veiculo=tipo, valor=valor)
            db.session.add(novo_plano)
    db.session.commit()

    configuracao = Configuracao.query.first()
    if not configuracao:
        configuracao = Configuracao(valor_hora=10.0, valor_diaria=50.0)
        db.session.add(configuracao)
        db.session.commit()

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
            db.session.add(novo_cliente)
            db.session.commit()
            if mensalista or vinte_quatro_horas:
                calcular_pagamentos_pendentes(novo_cliente)
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'danger')

    return render_template('novo_cliente.html')

@app.route('/cliente/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = db.session.get(Cliente, id)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('clientes'))

    if request.method == 'POST':
        era_mensalista = cliente.mensalista
        era_vinte_quatro_horas = cliente.vinte_quatro_horas
        tipo_veiculo_anterior = cliente.tipo_veiculo

        cliente.nome = request.form['nome']
        cliente.telefone = request.form['telefone']
        cliente.tipo_veiculo = request.form['tipo_veiculo']
        cliente.modelo = request.form['modelo']
        cliente.placa = request.form['placa']
        cliente.cpf_cnpj = request.form['cpf_cnpj']
        cliente.mensalista = 'mensalista' in request.form
        cliente.vinte_quatro_horas = 'vinte_quatro_horas' in request.form

        # Verificar se o cliente está sendo marcado como mensalista e 24h ao mesmo tempo
        if cliente.mensalista and cliente.vinte_quatro_horas:
            flash('Um cliente não pode ser marcado como Mensalista e 24h ao mesmo tempo.', 'danger')
            return redirect(url_for('editar_cliente', id=id))

        try:
            if (era_mensalista != cliente.mensalista or era_vinte_quatro_horas != cliente.vinte_quatro_horas or tipo_veiculo_anterior != cliente.tipo_veiculo):
                # Atualizar recibos futuros não pagos se o plano mudou
                if cliente.mensalista or cliente.vinte_quatro_horas:
                    atualizar_recibos_futuros(cliente)
                else:
                    apagar_recibos_futuros(cliente)
                calcular_pagamentos_pendentes(cliente)

            db.session.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar cliente: {str(e)}', 'danger')

    return render_template('editar_cliente.html', cliente=cliente)

def atualizar_recibos_futuros(cliente):
    hoje = datetime.now().strftime('%Y-%m')
    recibos_futuros = Recibo.query.filter(Recibo.cliente_id == cliente.id, Recibo.mes_referencia >= hoje, Recibo.pago == False).all()
    
    plano = Plano.query.filter_by(tipo_veiculo=cliente.tipo_veiculo).first()
    valor_mensal = plano.valor if plano else 0
    if cliente.vinte_quatro_horas:
        plano_24h = Plano.query.filter_by(tipo_veiculo='vinte_quatro_horas').first()
        valor_mensal = plano_24h.valor if plano_24h else 0

    for recibo in recibos_futuros:
        recibo.valor = valor_mensal
    db.session.commit()

def apagar_recibos_futuros(cliente):
    hoje = datetime.now().strftime('%Y-%m')
    recibos_futuros = Recibo.query.filter(Recibo.cliente_id == cliente.id, Recibo.mes_referencia >= hoje).all()
    for recibo in recibos_futuros:
        db.session.delete(recibo)
    db.session.commit()

@app.route('/cliente/<int:id>/deletar', methods=['POST'])
def deletar_cliente(id):
    cliente = db.session.get(Cliente, id)
    
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('clientes'))

    # Verificar se o cliente possui recibos e se todos os recibos estão pagos
    recibos = Recibo.query.filter_by(cliente_id=cliente.id).all()
    if recibos and any(not recibo.pago for recibo in recibos):
        flash('Não é possível deletar o cliente, pois ele possui recibos não pagos.', 'danger')
        return redirect(url_for('clientes'))

    try:
        # Apagar os recibos do cliente antes de apagar o cliente
        for recibo in recibos:
            db.session.delete(recibo)
        
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
        
        if cliente.mensalista or cliente.vinte_quatro_horas:
            mes_referencia = request.form['mes_referencia']
            if not mes_referencia:
                flash('Mês de referência é necessário para mensalistas e clientes 24h.', 'danger')
                return redirect(url_for('novo_recibo'))

            # Verificar se é o primeiro mês do cliente
            recibo_existente = Recibo.query.filter_by(cliente_id=cliente_id).first()
            if recibo_existente:
                # Não é o primeiro mês, definir data_entrada e data_saida como dia 5 do mês de referência e do próximo mês
                mes_referencia_date = datetime.strptime(mes_referencia, '%Y-%m')
                data_entrada = mes_referencia_date.replace(day=5)
                data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)
            else:
                # É o primeiro mês, definir data_entrada como a data atual e data_saida como dia 5 do próximo mês
                data_entrada = datetime.now()
                mes_referencia_date = datetime.strptime(mes_referencia, '%Y-%m')
                data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)

            valor = calcular_valor(cliente, mes_referencia)
            novo_recibo = Recibo(cliente_id=cliente_id, mes_referencia=mes_referencia, valor=valor,
                                 data_entrada=data_entrada, data_saida=data_saida)
        else:
            diaria = 'diaria' in request.form
            if diaria:
                data_diaria = request.form['data_diaria']
                if not data_diaria:
                    flash('Data é necessária para recibo de diária.', 'danger')
                    return redirect(url_for('novo_recibo'))
                data_entrada = datetime.strptime(data_diaria, '%Y-%m-%d')
                configuracao = Configuracao.query.first()
                valor = configuracao.valor_diaria if configuracao else 50.0
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
                    valor = calcular_valor_por_horas(horas)
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

def novo_recibo():
    clientes = Cliente.query.all()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        cliente = db.session.get(Cliente, cliente_id)
        
        if cliente.mensalista or cliente.vinte_quatro_horas:
            mes_referencia = request.form['mes_referencia']
            if not mes_referencia:
                flash('Mês de referência é necessário para mensalistas e clientes 24h.', 'danger')
                return redirect(url_for('novo_recibo'))

            # Verificar se é o primeiro mês do cliente
            recibo_existente = Recibo.query.filter_by(cliente_id=cliente_id).first()
            if recibo_existente:
                # Não é o primeiro mês, definir data_entrada e data_saida como dia 5 do mês de referência e do próximo mês
                mes_referencia_date = datetime.strptime(mes_referencia, '%Y-%m')
                data_entrada = mes_referencia_date.replace(day=5)
                data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)
            else:
                # É o primeiro mês, definir data_entrada como a data atual e data_saida como dia 5 do próximo mês
                data_entrada = datetime.now()
                mes_referencia_date = datetime.strptime(mes_referencia, '%Y-%m')
                data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)

            valor = calcular_valor(cliente, mes_referencia)
            novo_recibo = Recibo(cliente_id=cliente_id, mes_referencia=mes_referencia, valor=valor,
                                 data_entrada=data_entrada, data_saida=data_saida)
        else:
            diaria = 'diaria' in request.form
            if diaria:
                data_diaria = request.form['data_diaria']
                if not data_diaria:
                    flash('Data é necessária para recibo de diária.', 'danger')
                    return redirect(url_for('novo_recibo'))
                data_entrada = datetime.strptime(data_diaria, '%Y-%m-%d')
                configuracao = Configuracao.query.first()
                valor = configuracao.valor_diaria if configuracao else 50.0
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
                    valor = calcular_valor_por_horas(horas)
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

@app.route('/recibos', methods=['GET', 'POST'])
def recibos():
    clientes = Cliente.query.all()
    cliente_id = request.form.get('cliente_id')
    data_entrada_inicio = request.form.get('data_entrada_inicio')
    data_entrada_fim = request.form.get('data_entrada_fim')
    pago = request.form.get('pago')

    query = Recibo.query

    if cliente_id:
        query = query.filter(Recibo.cliente_id == cliente_id)
    
    if data_entrada_inicio:
        data_entrada_inicio = datetime.strptime(data_entrada_inicio, '%Y-%m-%d')
        query = query.filter(Recibo.data_entrada >= data_entrada_inicio)
    
    if data_entrada_fim:
        data_entrada_fim = datetime.strptime(data_entrada_fim, '%Y-%m-%d')
        query = query.filter(Recibo.data_entrada <= data_entrada_fim)
    
    if pago:
        pago = pago.lower() == 'true'
        query = query.filter(Recibo.pago == pago)
    
    recibos = query.all()

    for recibo in recibos:
        if recibo.cliente.mensalista and recibo.mes_referencia:
            mes_referencia = datetime.strptime(recibo.mes_referencia, '%Y-%m')
            if not recibo.data_entrada or recibo.data_entrada.month != mes_referencia.month:
                recibo.data_entrada = mes_referencia.replace(day=5)
            if not recibo.data_saida or recibo.data_saida.month != (mes_referencia + timedelta(days=32)).month:
                recibo.data_saida = (mes_referencia + timedelta(days=32)).replace(day=5)
        elif recibo.cliente.vinte_quatro_horas and recibo.mes_referencia:
            mes_referencia = datetime.strptime(recibo.mes_referencia, '%Y-%m')
            if not recibo.data_entrada or recibo.data_entrada.month != mes_referencia.month:
                recibo.data_entrada = mes_referencia.replace(day=5)
            if not recibo.data_saida or recibo.data_saida.month != (mes_referencia + timedelta(days=32)).month:
                recibo.data_saida = (mes_referencia + timedelta(days=32)).replace(day=5)

    return render_template('recibos.html', recibos=recibos, clientes=clientes)

@app.route('/recibo/<int:id>/pago', methods=['POST'])
def marcar_pago(id):
    recibo = db.session.get(Recibo, id)
    if recibo:
        recibo.pago = not recibo.pago
        db.session.commit()
    return redirect(url_for('recibos'))

@app.route('/recibo/<int:id>/exportar')
def exportar_recibo(id):
    recibo = db.session.get(Recibo, id)
    if not recibo.pago:
        flash('Apenas recibos pagos podem ser exportados.', 'danger')
        return redirect(url_for('recibos'))
    
    cliente = db.session.get(Cliente, recibo.cliente_id)
    
    # Nome da pasta inclui o nome do cliente, ID e modelo do carro
    client_folder = secure_filename(f"{cliente.nome}_{cliente.id}_{cliente.modelo}")
    base_path = os.path.join('files', client_folder)
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    if recibo.mes_referencia:
        file_name = f"recibo_{recibo.mes_referencia}.txt"
    elif recibo.data_entrada and recibo.data_saida:
        file_name = f"recibo_{recibo.data_entrada.strftime('%d-%m-%Y')}_a_{recibo.data_saida.strftime('%d-%m-%Y')}.txt"
    elif recibo.data_entrada:
        file_name = f"recibo_{recibo.data_entrada.strftime('%d-%m-%Y')}.txt"
    else:
        file_name = f"recibo_{recibo.id}.txt"

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
                f"Valor: {recibo.valor}\n"
                f"Pago: {'Sim' if recibo.pago else 'Não'}\n")

    with open(file_path, "w") as file:
        file.write(conteudo)

    return send_file(file_path, as_attachment=True)

@app.route('/recibo/<int:id>/editar', methods=['GET', 'POST'])
def editar_recibo(id):
    recibo = db.session.get(Recibo, id)
    if not recibo:
        flash('Recibo não encontrado.', 'danger')
        return redirect(url_for('recibos'))
    
    clientes = Cliente.query.all()
    
    if request.method == 'POST':
        try:
            recibo.cliente_id = request.form['cliente_id']
            recibo.cliente = db.session.get(Cliente, recibo.cliente_id)
            recibo.mes_referencia = request.form['mes_referencia']
            recibo.valor = float(request.form['valor'])
            
            # Atualizar as datas de entrada e saída
            if recibo.cliente.mensalista and recibo.mes_referencia:
                mes_referencia_date = datetime.strptime(recibo.mes_referencia, '%Y-%m')
                if not recibo.data_entrada:
                    recibo.data_entrada = mes_referencia_date.replace(day=5)
                if not recibo.data_saida:
                    recibo.data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)
            else:
                data_entrada = request.form.get('data_entrada')
                data_saida = request.form.get('data_saida')
                if data_entrada:
                    recibo.data_entrada = datetime.strptime(data_entrada, '%Y-%m-%dT%H:%M')
                else:
                    recibo.data_entrada = None

                if data_saida:
                    recibo.data_saida = datetime.strptime(data_saida, '%Y-%m-%dT%H:%M')
                else:
                    recibo.data_saida = None

                # Atualizar a data diária se for uma diária
                data_diaria = request.form.get('data_diaria')
                if data_diaria:
                    recibo.data_entrada = datetime.strptime(data_diaria, '%Y-%m-%d')
                    recibo.data_saida = None
                    recibo.mes_referencia = None

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

def calcular_pagamentos_pendentes(cliente):
    hoje = datetime.now()
    primeiro_dia_mes_atual = hoje.replace(day=1)
    proximo_mes = (primeiro_dia_mes_atual + timedelta(days=32)).replace(day=1)
    dia_5_proximo_mes = proximo_mes.replace(day=5)
    diferenca_dias = (dia_5_proximo_mes - hoje).days

    plano = Plano.query.filter_by(tipo_veiculo=cliente.tipo_veiculo).first()
    valor_mensal = plano.valor if plano else 0
    if cliente.vinte_quatro_horas:
        plano_24h = Plano.query.filter_by(tipo_veiculo='vinte_quatro_horas').first()
        valor_mensal = plano_24h.valor if plano_24h else 0

    numero_dias_mes_atual = (proximo_mes - primeiro_dia_mes_atual).days
    valor_pro_rata = round(((valor_mensal / numero_dias_mes_atual) * diferenca_dias), 2)

    recibos_existentes = Recibo.query.filter(Recibo.cliente_id == cliente.id, Recibo.mes_referencia >= hoje.strftime('%Y-%m'), Recibo.pago == False).all()

    if recibos_existentes:
        recibo_atual = recibos_existentes[0]
        recibo_atual.valor = valor_pro_rata
    else:
        novo_recibo = Recibo(cliente_id=cliente.id, mes_referencia=hoje.strftime('%Y-%m'), valor=valor_pro_rata)
        db.session.add(novo_recibo)

    for i in range(1, 13):
        mes_referencia = (hoje.replace(day=1) + timedelta(days=32 * i)).strftime('%Y-%m')
        recibo_existente = Recibo.query.filter(Recibo.cliente_id == cliente.id, Recibo.mes_referencia == mes_referencia, Recibo.pago == False).first()
        if recibo_existente:
            recibo_existente.valor = valor_mensal
        else:
            novo_recibo = Recibo(cliente_id=cliente.id, mes_referencia=mes_referencia, valor=valor_mensal)
            db.session.add(novo_recibo)

    db.session.commit()

def calcular_valor(cliente, mes_referencia):
    plano = Plano.query.filter_by(tipo_veiculo=cliente.tipo_veiculo).first()
    if cliente.vinte_quatro_horas:
        plano = Plano.query.filter_by(tipo_veiculo='vinte_quatro_horas').first()
    return plano.valor if plano else 0

def calcular_valor_por_horas(horas):
    configuracao = Configuracao.query.first()
    valor_hora = configuracao.valor_hora if configuracao else 10.0
    valor_diaria = configuracao.valor_diaria if configuracao else 50.0
    valor_inicial = 12.0  # Valor inicial fixo para começar

    if horas > 5:
        return valor_diaria
    return valor_inicial + (int(horas) * valor_hora)

def verificar_renovar_recibos(cliente):
    if not cliente.mensalista and not cliente.vinte_quatro_horas:
        return

    tipo_veiculo_valores = {
        'carro pequeno': 320.0,
        'SUV': 350.0,
        'moto': 150.0,
    }

    ultimo_recibo = Recibo.query.filter_by(cliente_id=cliente.id).order_by(Recibo.mes_referencia.desc()).first()
    if ultimo_recibo:
        ultimo_mes = datetime.strptime(ultimo_recibo.mes_referencia, '%Y-%m')
        proximo_mes = (ultimo_mes + timedelta(days=32)).replace(day=1)

        if (proximo_mes - datetime.now()).days <= 30:
            valor_mensal = 400.0 if cliente.vinte_quatro_horas else tipo_veiculo_valores.get(cliente.tipo_veiculo, 0)

            for i in range(12):
                mes_referencia = (proximo_mes + timedelta(days=32 * i)).strftime('%Y-%m')
                novo_recibo = Recibo(cliente_id=cliente.id, mes_referencia=mes_referencia, valor=valor_mensal)
                db.session.add(novo_recibo)

            db.session.commit()

@app.route('/configurar_planos', methods=['GET', 'POST'])
def configurar_planos():
    if request.method == 'POST':
        valores = {
            'carro pequeno': request.form['carro_pequeno'],
            'SUV': request.form['suv'],
            'moto': request.form['moto'],
            'vinte_quatro_horas': request.form['vinte_quatro_horas'],
            'valor_hora': request.form['valor_hora'],
            'valor_diaria': request.form['valor_diaria']
        }

        for tipo, valor in valores.items():
            if tipo in ['valor_hora', 'valor_diaria']:
                configuracao = Configuracao.query.first()
                if configuracao:
                    setattr(configuracao, tipo, float(valor))
                else:
                    configuracao = Configuracao(valor_hora=valores['valor_hora'], valor_diaria=valores['valor_diaria'])
                    db.session.add(configuracao)
            else:
                plano = Plano.query.filter_by(tipo_veiculo=tipo).first()
                if plano:
                    plano.valor = float(valor)
                    atualizar_recibos_nao_pagos(plano.id, plano.valor)
                else:
                    novo_plano = Plano(tipo_veiculo=tipo, valor=float(valor))
                    db.session.add(novo_plano)

        db.session.commit()
        flash('Valores dos planos atualizados com sucesso!', 'success')
        return redirect(url_for('clientes'))

    planos = Plano.query.all()
    valores_planos = {plano.tipo_veiculo: plano.valor for plano in planos}
    configuracao = Configuracao.query.first()
    valores_planos['valor_hora'] = configuracao.valor_hora if configuracao else 10.0
    valores_planos['valor_diaria'] = configuracao.valor_diaria if configuracao else 50.0

    return render_template('configurar_planos.html', valores=valores_planos)

def atualizar_recibos_nao_pagos(plano_id, novo_valor):
    plano = Plano.query.get(plano_id)
    if plano:
        recibos = Recibo.query.join(Cliente).filter(Cliente.tipo_veiculo == plano.tipo_veiculo, Recibo.pago == False).all()
        for recibo in recibos:
            if not recibo.cliente.mensalista and not recibo.cliente.vinte_quatro_horas:
                recibo.valor = novo_valor
        db.session.commit()

# Função para obter os valores dos planos
@app.route('/get_planos_valores')
def get_planos_valores():
    valores_planos = app.config.get('PLANOS_VALORES', {
        'carro_pequeno': 320.0,
        'suv': 350.0,
        'moto': 150.0,
        'vinte_quatro_horas': 400.0
    })
    return jsonify(valores_planos)

def corrigir_datas_recibos():
    recibos = Recibo.query.join(Cliente).filter((Cliente.mensalista == True) | (Cliente.vinte_quatro_horas == True)).all()

    for recibo in recibos:
        if recibo.mes_referencia:
            mes_referencia_date = datetime.strptime(recibo.mes_referencia, '%Y-%m')
            if not recibo.data_entrada:
                recibo.data_entrada = mes_referencia_date.replace(day=5)
            if not recibo.data_saida:
                recibo.data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)
        else:
            # Primeiro mês, data de entrada é a data atual e data de saída é dia 5 do próximo mês
            if not recibo.data_entrada:
                recibo.data_entrada = datetime.now()
            if not recibo.data_saida:
                mes_referencia_date = datetime.strptime(recibo.mes_referencia, '%Y-%m')
                recibo.data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)

    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        inicializar_planos()
        corrigir_datas_recibos()
    app.run(debug=True)