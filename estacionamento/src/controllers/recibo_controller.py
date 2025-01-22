import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

from repository.database import db
from models.cliente import Cliente
from models.recibo import Recibo
from utils import criar_recibo, get_template_dir, recibo_existente_check

# Criar um Blueprint para o recibo
recibo_bp = Blueprint('recibo', __name__)

# Definindo o Diretório
template_dir = get_template_dir.get_template_dir()

@recibo_bp.route('/recibos', methods=['GET', 'POST'])
def recibos():
    cliente = Cliente.query.all()

    cliente_id = request.form.get('cliente_id')
    print(f"Cliente ID selecionado: {cliente_id}")  # Depuração
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

    return render_template('views/recibos.html', recibos=recibos, clientes=cliente)
    
@recibo_bp.route('/recibos/novo', methods=['GET', 'POST'])
def novo_recibo():
    clientes = Cliente.query.all()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        cliente =  db.session.get(Cliente, cliente_id)

        # Se o Cliente for Mensalista ou 24 Horas
        if cliente.mensalista or cliente.vinte_quatro_horas:
            mes_referencia = request.form['mes_referencia']

            if not mes_referencia:
                flash('Mês de referência é necessário para mensalistas e clientes 24h.', 'danger')
                return redirect(url_for('recibo.novo_recibo'))
            
            mes_referencia_date = datetime.strptime(mes_referencia, '%Y-%m')
            data_entrada = mes_referencia_date.replace(day=5)
            data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)
            valor = request.form['valor']

            recibo_existente = recibo_existente_check.recibo_existente(
                cliente_id=cliente_id,
                data_entrada = data_entrada,
                data_saida = data_saida,
                mes_referencia = mes_referencia,
                valor=valor
            )
            if recibo_existente:
                flash('O recibo já existe.', 'danger')
                return redirect(url_for('recibo.recibos'))
            
            novo_recibo = Recibo(cliente_id=cliente_id,
                                 mes_referencia=mes_referencia,
                                 valor=valor,
                                 data_entrada=data_entrada,
                                 data_saida=data_saida
                                 )
        else:
            diaria = 'diaria' in request.form

            if diaria:
                data_diaria = request.form['data_diaria']

                if not data_diaria:
                    flash('Data é necessária para recibo de diária.', 'danger')
                    return redirect(url_for('novo_recibo'))
                
                data_entrada = datetime.strptime(data_diaria, '%Y-%m-%d')
                data_saida = data_entrada + timedelta(hours=23, minutes=59)
                valor = request.form['valor']
                
                recibo_existente = recibo_existente_check.recibo_existente(
                    cliente_id=cliente_id,
                    data_entrada = data_entrada,
                    data_saida = data_saida,
                    mes_referencia = None,
                    valor=valor
                )
                if recibo_existente:
                    flash('O recibo já existe.', 'danger')
                    return redirect(url_for('recibo.recibos'))

                novo_recibo = Recibo(cliente_id=cliente_id,
                                     data_entrada=data_entrada,
                                     data_saida=data_saida,
                                     valor=valor)
            else: # Se for avulso e não for diária
                data_entrada = request.form.get('data_entrada')
                data_saida = request.form.get('data_saida')

                if data_entrada and data_saida:
                    data_entrada = datetime.strptime(data_entrada, '%Y-%m-%dT%H:%M')
                    data_saida = datetime.strptime(data_saida, '%Y-%m-%dT%H:%M')

                    if data_entrada > data_saida:
                        flash('A data de entrada não pode ser posterior à data de saída.', 'danger')
                        return redirect(url_for('novo_recibo'))
                    
                    valor = request.form['valor']

                    recibo_existente = recibo_existente_check.recibo_existente(
                        cliente_id=cliente_id,
                        data_entrada = data_entrada,
                        data_saida = data_saida,
                        mes_referencia = None,
                        valor=valor
                    )
                    if recibo_existente:
                        flash('O recibo já existe.', 'danger')
                        return redirect(url_for('recibo.recibos'))

                    novo_recibo = Recibo(cliente_id=cliente_id, 
                                         data_entrada=data_entrada,
                                         data_saida=data_saida, 
                                         valor=valor)
                else:
                    flash('Datas de entrada e saída são necessárias.', 'danger')
                    return redirect(url_for('novo_recibo'))

        try:
            db.session.add(novo_recibo)
            db.session.commit()
            flash('Recibo gerado com sucesso!', 'success')
            return redirect(url_for('recibo.recibos'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao gerar recibo: {str(e)}', 'danger')

    return render_template('views/novo_recibo.html', clientes=clientes)

@recibo_bp.route('/recibos/<int:id>/editar', methods=['GET', 'POST'])
def editar_recibo(id):
    recibo = db.session.get(Recibo, id)

    if not recibo:
        flash('Recibo não encontrado.', 'danger')
        return redirect(url_for('recibo.recibos'))
    
    clientes = Cliente.query.all()
    
    if request.method == 'POST':
        try:
            recibo.cliente_id = request.form['cliente_id']
            recibo.cliente = db.session.get(Cliente, recibo.cliente_id)
            recibo.mes_referencia = request.form['mes_referencia'] if request.form['mes_referencia'] else None

            if recibo.mes_referencia:
                mes_referencia_date = datetime.strptime(recibo.mes_referencia, '%Y-%m')

                recibo.data_entrada = mes_referencia_date.replace(day=5)
                recibo.data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)
            else:
                diaria = 'diaria' in request.form

                if diaria:
                    data_diaria = request.form['data_diaria']

                    if not data_diaria:
                        flash('Data é necessária para recibo de diária.', 'danger')
                        return redirect(url_for('recibo.recibos'))
                    
                    recibo.data_entrada = datetime.strptime(data_diaria, '%Y-%m-%d')
                    recibo.data_saida = recibo.data_entrada + timedelta(hours=23, minutes=59)

                else: # se for por hora
                    data_entrada = request.form.get('data_entrada')
                    data_saida = request.form.get('data_saida')

                    if data_entrada and data_saida:
                        recibo.data_entrada = datetime.strptime(data_entrada, '%Y-%m-%dT%H:%M')
                        recibo.data_saida = datetime.strptime(data_saida, '%Y-%m-%dT%H:%M')

                        if data_entrada > data_saida:
                            flash('A data de entrada não pode ser posterior à data de saída.', 'danger')
                            return redirect(url_for('novo_recibo'))
                    
                    if not data_entrada or not data_saida:
                        flash('Datas de entrada e saídas são necessárias para recibos de hora.', 'danger')
                        return redirect(url_for('recibo.recibos'))

            recibo.valor = float(request.form['valor'])

            db.session.commit()

            flash('Recibo atualizado com sucesso!', 'success')
            return redirect(url_for('recibo.recibos'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar recibo: {str(e)}', 'danger')

    return render_template('views/editar_recibo.html', recibo=recibo, clientes=clientes)

@recibo_bp.route('/recibos/<int:id>/deletar', methods=['POST'])
def deletar_recibo(id):
    recibo = db.session.get(Recibo, id)

    try:
        db.session.delete(recibo)
        db.session.commit()
        flash('Recibo deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar recibo: {str(e)}', 'danger')
    
    return redirect(url_for('recibo.recibos'))

@recibo_bp.route('/recibos/<int:id>/pago', methods=['POST'])
def marcar_pago(id):
    recibo = db.session.get(Recibo, id)

    if recibo:
        recibo.pago = not recibo.pago
        db.session.commit()
        
    return redirect(url_for('recibo.recibos'))

@recibo_bp.route('/recibo/<int:id>/exportar')
def exportar_recibo(id):
    recibo = db.session.get(Recibo, id)

    if not recibo.pago:
        flash('Apenas recibos pagos podem ser exportados.', 'danger')
        return redirect(url_for('recibos'))
    
    cliente = db.session.get(Cliente, recibo.cliente_id)
    
    client_folder = secure_filename(f"{cliente.nome}_{cliente.id}_{cliente.modelo}")
    base_path = os.path.join(os.path.abspath(''), 'src', 'files', client_folder)
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    if recibo.mes_referencia:
        mes_referencia_date = datetime.strptime(recibo.mes_referencia, '%Y-%m')

        if not recibo.data_entrada:
            recibo.data_entrada = mes_referencia_date.replace(day=5)
        if not recibo.data_saida:
            recibo.data_saida = (mes_referencia_date + timedelta(days=32)).replace(day=5)

        file_name = f"recibo_{recibo.data_entrada.strftime('%d-%m-%Y')}_a_{recibo.data_saida.strftime('%d-%m-%Y')}.pdf"

    elif recibo.data_entrada and recibo.data_saida:
        file_name = f"recibo_{recibo.data_entrada.strftime('%d-%m-%Y')}_a_{recibo.data_saida.strftime('%d-%m-%Y')}.pdf"

    elif recibo.data_entrada:
        file_name = f"recibo_{recibo.data_entrada.strftime('%d-%m-%Y')}.pdf"

    else:
        file_name = f"recibo_{recibo.id}.pdf"

    if not recibo.data_saida:
        recibo.data_saida = recibo.data_entrada

    file_path = os.path.join(base_path, file_name)

    criar_recibo.criar_recibo(
        valor=recibo.valor,
        cliente=cliente.nome,
        data_de_entrada=recibo.data_entrada.strftime('%d/%m/%Y %H:%M:%S'),
        data_de_saida=recibo.data_saida.strftime('%d/%m/%Y %H:%M:%S'),
        veiculo=cliente.modelo,
        output_path=file_path
    )

    return send_from_directory(base_path, file_name, as_attachment=True)