# Sistema de Gerenciamento de Estacionamento Panorama

## Descrição
Este é um sistema de gerenciamento de estacionamento desenvolvido com Flask para o backend e SQLite como banco de dados. O sistema permite o cadastro, edição, deleção de clientes, e geração de recibos automáticos com base no tempo de permanência do veículo no estacionamento ou no plano do cliente. Os planos tem valores pré-definidos conforme o Diretor do estacionamento mencionou e existe a função de alterar esses valores.

## Funcionalidades
- Cadastro de novos clientes com informações detalhadas.
- Edição de informações de clientes já cadastrados.
- Deleção de clientes.
- Geração automática de recibos com base no tempo de permanência ou no plano do cliente.
- Gerar recibos avulsos manualmente.
- Cálculo automático do valor do recibo.
- Editar valor do plano.
- Exportar recibo em PDF, preenchido automaticamente.

## Estrutura do Projeto
```plaintext
/estacionamento
    ├── /files
    │   └── /nome_cliente
    │       └── arquivos.pdf
    ├── /instance
    │   └── clientes.db
    ├── /templates
    │   ├── clientes.html
    │   ├── configurar_planos.html
    │   ├── editar_cliente.html
    │   ├── editar_recibo.html
    │   ├── index.html
    │   ├── novo_cliente.html
    │   ├── novo_recibo.html
    │   └── recibos.html
    └── app.py
```

## Tecnologias Utilizadas
- Python
- Flask
- SQLite
- HTML/CSS
- Bootstrap

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

### Alterar valor dos planos
- Vá até a página de clientes e clique em "Configurar Valores dos Planos".
- Preencha os novos valores e clique em "Salvar".