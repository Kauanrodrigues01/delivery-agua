# Delivery Água

Sistema de delivery de água com integração ao WhatsApp via Evolution API.

## Funcionalidades
- Cadastro e listagem de produtos
- Carrinho de compras
- Checkout com cálculo de troco
- Envio automático de mensagens WhatsApp para admin e cliente ao finalizar pedido
- Painel administrativo Django

## Tecnologias
- Python 3.10+
- Django 5.2+
- Pillow
- Requests
- Python Decouple
- Evolution API (WhatsApp)

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/Kauanrodrigues01/delivery-agua.git
   cd delivery-agua
   ```

2. Instale as dependências:
   ```bash
   poetry install
   ```

3. Copie o arquivo de variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o .env com suas configurações
   ```

4. Execute as migrações:
   ```bash
   poetry run python manage.py migrate
   ```

5. Crie um superusuário:
   ```bash
   poetry run python manage.py createsuperuser
   ```

6. Inicie o servidor:
   ```bash
   poetry run python manage.py runserver
   ```

## Configuração da Evolution API
Preencha as variáveis no `.env`:
- `EVOLUTION_API_BASE_URL`: URL base da sua API Evolution
- `EVOLUTION_API_KEY`: Chave de API
- `INSTANCE_NAME`: Nome da instância configurada
- `WHATSAPP_ADMIN_NUMBER`: Número do admin no formato internacional (ex: 5585999999999)

## Scripts úteis
- `poetry run python manage.py migrate` — Aplica migrações
- `poetry run python manage.py runserver` — Inicia o servidor
- `poetry run python manage.py test` — Executa os testes
- `poetry run python manage.py createsuperuser` — Cria um admin

## Estrutura do Projeto
```
app/           # Configurações do projeto Django
cart/          # Lógica do carrinho
checkout/      # Checkout e pedidos
core/          # Funções centrais
products/      # Produtos
services/      # Integração Evolution/WhatsApp
static/        # Arquivos estáticos
media/         # Uploads
```

## Licença
MIT

---
Desenvolvido por [Kauanrodrigues01](https://github.com/Kauanrodrigues01)
