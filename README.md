# Sistema de Gerenciamento de Estacionamento Panorama

## Descrição
Este é um sistema de gerenciamento de estacionamento desenvolvido com Flask para o backend e SQLite como banco de dados. O sistema permite o cadastro, edição, deleção de clientes, e geração de recibos automáticos com base no tempo de permanência do veículo no estacionamento.

## Funcionalidades
- Cadastro de novos clientes com informações detalhadas.
- Edição de informações de clientes já cadastrados.
- Deleção de clientes.
- Geração automática de recibos com base no tempo de permanência.
- Cálculo automático do valor do recibo.

## Estrutura do Projeto
/estacionamento
    /templates
        index.html
        clientes.html
        novo_cliente.html
        editar_cliente.html
        novo_recibo.html
    app.py
    clientes.db
## Tecnologias Utilizadas
- Python
- Flask
- SQLite
- HTML/CSS
- Bootstrap

## Instalação

1. Clone o repositório:
    ```bash
    git clone https://github.com/seu-usuario/estacionamento-panorama.git
    cd estacionamento-panorama
    ```

2. Crie um ambiente virtual e ative:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows use `venv\Scripts\activate`
    ```

3. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

4. Execute o aplicativo:
    ```bash
    python app.py
    ```

5. Acesse o aplicativo no navegador:
    ```
    http://127.0.0.1:5000
    ```

## Como Usar

### Cadastro de Cliente
- Navegue até a página de clientes e clique em "Adicionar Cliente".
- Preencha o formulário com as informações do cliente e clique em "Salvar".

### Edição de Cliente
- Na página de clientes, clique no botão "Editar" ao lado do cliente que deseja modificar.
- Atualize as informações no formulário e clique em "Salvar".

### Deleção de Cliente
- Na página de clientes, clique no botão "Deletar" ao lado do cliente que deseja remover.

### Geração de Recibo
- Navegue até a página de geração de recibos.
- Selecione o cliente, insira a data e hora de entrada e saída, e clique em "Gerar Recibo".

## Contribuição
Sinta-se à vontade para abrir issues e pull requests. Toda contribuição é bem-vinda!

## Licença
Este projeto está licenciado sob a [MIT License](LICENSE).