# Sistema de Gerenciamento de Estacionamento Panorama

## Descrição
Este projeto foi desenvolvido para facilitar o **controle de mensalistas** no **Estacionamento Panorama**, localizado em:

📍 **R. Artista Bitencourt, 98 - Centro, Florianópolis - SC, 88020-060**  

## Funcionalidades
- **Cadastro de novos clientes com informações detalhadas.**
- **Edição de informações de clientes já cadastrados.**
- **Deleção de clientes.**
- **Gerar recibos avulsos manualmente.**
- **Exportar recibo em PDF, preenchido automaticamente.**
- **Filtragem de clientes inadimplentes**
- **Histórico de pagamentos**

## Estrutura do Projeto
```plaintext
/estacionamento2
    ├── /.vscode
    │   └── settings.json
    ├── /backups
    ├── /instance
    │   └── database.db
    ├── /src
    │   └── /controllers
    │       └── __init__.py
    │       └── cliente_controller.py
    │       └── recibo_controller.py
    │   └── /files
    │       └── /nome_cliente
    │           └── arquivos.pdf
    │   └── /models
    │       └── __init__.py
    │       └── cliente.py
    │       └── recibo.py
    │   └── /repository
    │       └── __init__.py
    │       └── database.py
    │   └── /static
    │       └── /recibo_img
    │           └── __init__.py
    │           └── template_recibo.png
    │       └── __init__.py
    │   └── /utils
    │       └── __init__.py
    │       └── apagar_recibos_futuros.py
    │       └── atualizar_recibos_futuros.py
    │       └── backups.py
    │       └── criar_recibo.py
    │       └── get_template_dir.py
    │       └── recibo_existente_check.py
    │   └── /views
    │       └── __init__.py
    │       └── clientes.html
    │       └── editar_cliente.html
    │       └── editar_recibo.html
    │       └── index.html
    │       └── novo_cliente.html
    │       └── novo_recibo.html
    │       └── recibos.html
    │   └── __init__.py
    │   └── .gitignore
    │   └── app.py
    │   └── README.md
    │   └── requirements.txt
    └──
```

## Tecnologias Utilizadas
- **Back-end**: Flask + SQLite
- **Front-end**: HTML, CSS, Jinja2
- **Banco de Dados**: SQLite (com opção para PostgreSQL)
- **Testes**: Pytest
- **Deploy**: Docker + GitHub Actions

## 📦 Como Rodar o Projeto
### 🔧 Requisitos:
- Python 3.9+
- pip instalado

### 🏗️ Configuração do Ambiente:
```bash
# Clone o repositório
git clone https://github.com/seuusuario/estacionamento2.git

# Entre na pasta do projeto
cd estacionamento2

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Para Linux/Mac
venv\Scripts\activate  # Para Windows

# Instale as dependências
pip install -r requirements.txt

# Execute o servidor
python src/app.py
```

## Como Usar

### Cadastro de Cliente
- Navegue até a página de clientes e clique em "Novo Cliente".
- Preencha o formulário com as informações do cliente e clique em "Salvar".

### Edição de Cliente
- Na página de clientes, clique no botão "Editar" ao lado do cliente que deseja modificar.
- Atualize as informações no formulário e clique em "Salvar".

### Deleção de Cliente
- Na página de clientes, clique no botão "Deletar" ao lado do cliente que deseja remover. Caso o cliente possua recibos não pagos, essa função não irá funcionar, visto que só é permitido deletar clientes que estão com tudo quitado.

### Geração de Recibo
- Navegue até a página de geração de recibos.
- Selecione o cliente, insira a data e hora de entrada e saída, e clique em "Gerar Recibo".
- Caso o cliente tenha um plano, você deverá apenas escolher o mês de referência do plano. Todavia, o sistema gera automaticamente, então cheque antes se o recibo já existe.

## 📬 Contato
Desenvolvido por **Matheus Fernandes**
📧 E-mail: matthfeeer@gmail.com
🔗 [LinkedIn](https://linkedin.com/in/matheus-fernandes-duarte-a8a74724a/) | [GitHub](https://github.com/MatheusFernandesDuarte)

## 📝 Licença
Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
