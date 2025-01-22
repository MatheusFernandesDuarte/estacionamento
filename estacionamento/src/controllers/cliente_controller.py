from flask import Blueprint, render_template, request, flash, redirect, url_for

from repository.database import db
from models.cliente import Cliente
from models.recibo import Recibo
from utils import apagar_recibos_futuros, atualizar_recibos_futuros, get_template_dir

# Criar um Blueprint para o cliente
cliente_bp = Blueprint('cliente', __name__)

# Definindo o Diretório
template_dir = get_template_dir.get_template_dir()

@cliente_bp.route('/clientes')
def clientes():
    clientes = Cliente.query.all()
    total_clientes = len(clientes)
    return render_template('views/clientes.html', clientes=clientes, total_clientes=total_clientes)
    
@cliente_bp.route('/clientes/novo', methods=['GET', 'POST'])
def novo_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        tipo_veiculo = request.form['tipo_veiculo']
        modelo = request.form['modelo']
        data_vencimento = request.form['data_vencimento']
        cpf_cnpj = request.form['cpf_cnpj']
        email = request.form['email']
        endereco = request.form['endereco']
        mensalista = 'mensalista' in request.form
        vinte_quatro_horas = 'vinte_quatro_horas' in request.form
        valor = request.form['valor']

        # Se for avulso
        if mensalista == False and vinte_quatro_horas == False:
            valor = 0

        # Verificar se já existe um cliente com todas as mesmas informações
        cliente_existente = Cliente.query.filter_by(
            nome=nome,
            telefone=telefone,
            tipo_veiculo=tipo_veiculo,
            modelo=modelo,
            data_vencimento=data_vencimento,
            cpf_cnpj=cpf_cnpj,
            email=email,
            endereco=endereco,
            mensalista=mensalista,
            vinte_quatro_horas=vinte_quatro_horas,
            valor=valor
        ).first()

        if cliente_existente:
            flash('Já existe um cliente com todas essas informações.', 'danger')
            return redirect(url_for('cliente.clientes'))
        
        novo_cliente = Cliente(nome=nome, 
                               telefone=telefone, 
                               tipo_veiculo=tipo_veiculo,
                               modelo=modelo, 
                               data_vencimento=data_vencimento,
                               cpf_cnpj=cpf_cnpj, 
                               email=email,
                               endereco=endereco,
                               mensalista=mensalista,
                               vinte_quatro_horas=vinte_quatro_horas,
                               valor=valor
                                )

        try:
            db.session.add(novo_cliente)
            db.session.commit()

            flash('Cliente cadastrado com sucesso!', 'success')

            return redirect(url_for('cliente.clientes'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'danger')
            return redirect(url_for('cliente.novo_cliente'))

    elif request.method == 'GET':
        return render_template('views/novo_cliente.html')
        
@cliente_bp.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
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
        cliente.data_vencimento = request.form['data_vencimento']        
        cliente.cpf_cnpj = request.form['cpf_cnpj']
        cliente.email = request.form['email']
        cliente.endereco = request.form['endereco']
        cliente.mensalista = 'mensalista' in request.form
        cliente.vinte_quatro_horas = 'vinte_quatro_horas' in request.form
        cliente.valor = request.form['valor']

        try:
            if (era_mensalista != cliente.mensalista or era_vinte_quatro_horas != cliente.vinte_quatro_horas or tipo_veiculo_anterior != cliente.tipo_veiculo):
                if era_mensalista or era_vinte_quatro_horas or cliente.mensalista or cliente.vinte_quatro_horas:

                    # Atualizar recibos futuros não pagos se o plano mudou
                    if cliente.mensalista or cliente.vinte_quatro_horas:
                        atualizar_recibos_futuros.atualizar_recibos_futuros(cliente)
                    else:
                        apagar_recibos_futuros.apagar_recibos_futuros(cliente)

            db.session.commit()
            flash('Cliente atualizado com sucesso!', 'success')

            return redirect(url_for('cliente.clientes'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar cliente: {str(e)}', 'danger')

    return render_template('views/editar_cliente.html', cliente=cliente)
    
@cliente_bp.route('/clientes/<int:id>/deletar', methods=['POST'])
def deletar_cliente(id):
    cliente = db.session.get(Cliente, id)
    
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('cliente.clientes'))

    # Verificar se o cliente possui recibos e se todos os recibos estão pagos
    recibos = Recibo.query.filter_by(cliente_id=cliente.id).all()
    if recibos and any(not recibo.pago for recibo in recibos):
        flash('Não é possível deletar o cliente, pois ele possui recibos não pagos.', 'danger')
        return redirect(url_for('cliente.clientes'))

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
    
    return redirect(url_for('cliente.clientes'))