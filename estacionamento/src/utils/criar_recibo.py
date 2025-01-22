import locale
import os

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame

def criar_recibo(valor: float, cliente: str, data_de_entrada: str, data_de_saida: str, veiculo: str, output_path: str) -> None:
    # Setting locale for currency formatting
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    # Formatting the currency value
    valor_formatado = f"R${locale.currency(valor, grouping=True).replace('R$','')}"

    # Creating the canvas
    cnv = canvas.Canvas(filename=output_path, pagesize=(945, 591))

    # Registering the font
    pdfmetrics.registerFont(TTFont('Arial', "Arial.ttf"))

    # Drawing the template image
    cnv.drawImage(image=os.path.join(os.path.abspath(""),"src", "static", "recibo_img", "template_recibo.png"), x=0, y=0)

    # Setting font and color for the value text
    cnv.setFont(psfontname="Arial", size=50)
    cnv.setFillColor(colors.black)

    # Drawing the value text
    cnv.drawString(x=650, y=434, text=valor_formatado)

    # Defining the text to be wrapped
    text = f"Recebemos de {cliente} o valor mencionado referente a um estacionamento com manobrista para o veículo {veiculo}, no período de {data_de_entrada} a {data_de_saida}."

    # Defining a custom style for the paragraph
    styles = getSampleStyleSheet()
    justified_style = ParagraphStyle(
        name='Justified',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=30,
        leading=35,
        alignment=4  # Justified alignment
    )

    # Creating the paragraph
    paragraph = Paragraph(text, justified_style)

    # Creating a frame to fit the paragraph
    frame = Frame(50, 125, 845, 200, showBoundary=0)

    # Drawing the paragraph inside the frame
    frame.addFromList([paragraph], cnv)

    # Finalizing the PDF
    cnv.showPage()
    cnv.save()