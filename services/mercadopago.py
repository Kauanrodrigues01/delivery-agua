import uuid
from datetime import datetime, timedelta
from typing import Dict
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from django.conf import settings


class MercadoPagoService:
    """
    Serviço para interagir com a API de pagamentos do Mercado Pago.
    """

    # --- Mapeamentos de Status e Detalhes ---
    STATUS_MAP = {
        "unknown": "Status desconhecido.",
        "pending": "O usuário ainda não concluiu o processo de pagamento (por exemplo, ao gerar um boleto).",
        "approved": "O pagamento foi aprovado e creditado com sucesso.",
        "authorized": "O pagamento foi autorizado, mas ainda não foi capturado.",
        "in_process": "O pagamento está em análise.",
        "in_mediation": "O usuário iniciou uma disputa.",
        "rejected": "O pagamento foi rejeitado (o usuário pode tentar pagar novamente).",
        "cancelled": "O pagamento foi cancelado por uma das partes ou o prazo de pagamento expirou.",
        "refunded": "O pagamento foi reembolsado ao usuário.",
        "charged_back": "Um chargeback foi aplicado no cartão de crédito do comprador.",
    }

    STATUS_DETAIL_MAP = {
        "unknown": "Status desconhecido.",
        "accredited": "Pagamento creditado.",
        "partially_refunded": "O pagamento foi feito com pelo menos um reembolso parcial.",
        "pending_capture": "O pagamento foi autorizado e aguarda captura.",
        "offline_process": "Por falta de processamento online, o pagamento está sendo processado de maneira offline.",
        "pending_contingency": "Falha temporária. O pagamento será processado diferido.",
        "pending_review_manual": "O pagamento está em revisão para determinar sua aprovação ou rejeição.",
        "pending_waiting_transfer": "Aguardando que o usuário finalize o processo de pagamento no seu banco.",
        "pending_waiting_payment": "Pendente até que o usuário realize o pagamento.",
        "pending_challenge": "Pagamento com cartão de crédito com confirmação pendente (challenge).",
        "bank_error": "Pagamento rejeitado por um erro com o banco.",
        "cc_rejected_3ds_mandatory": "Pagamento rejeitado por não ter o challenge 3DS quando é obrigatório.",
        "cc_rejected_bad_filled_card_number": "Número de cartão incorreto.",
        "cc_rejected_bad_filled_date": "Data de validade incorreta.",
        "cc_rejected_bad_filled_other": "Detalhes do cartão incorretos.",
        "cc_rejected_bad_filled_security_code": "Código de segurança (CVV) incorreto.",
        "cc_rejected_blacklist": "O cartão está desativado ou em uma lista de restrições (roubo/fraude).",
        "cc_rejected_call_for_authorize": "O método de pagamento requer autorização prévia para o valor.",
        "cc_rejected_card_disabled": "O cartão está inativo.",
        "cc_rejected_duplicated_payment": "Pagamento duplicado.",
        "cc_rejected_high_risk": "Recusado por prevenção de fraudes.",
        "cc_rejected_insufficient_amount": "Limite do cartão insuficiente.",
        "cc_rejected_invalid_installments": "Número inválido de parcelas.",
        "cc_rejected_max_attempts": "Número máximo de tentativas excedido.",
        "cc_rejected_other_reason": "Erro genérico do processador de pagamento.",
        "cc_rejected_time_out": "A transação expirou (timeout).",
        "cc_amount_rate_limit_exceeded": "Superou o limite de valor para o meio de pagamento.",
        "rejected_high_risk": "Rejeitado por suspeita de fraude.",
        "rejected_insufficient_data": "Rejeitado por falta de informações obrigatórias.",
        "rejected_by_bank": "Operação recusada pelo banco.",
        "rejected_by_regulations": "Pagamento recusado devido a regulamentações.",
        "rejected_by_biz_rule": "Pagamento recusado devido a regras de negócio.",
    }

    def __init__(self):
        # Validação rigorosa das variáveis de ambiente
        if not settings.MP_ACCESS_TOKEN or settings.MP_ACCESS_TOKEN.strip() == "":
            raise ValueError(
                "A variável de ambiente MP_ACCESS_TOKEN não foi definida ou está vazia."
            )

        if not settings.MP_BASE_API_URL or settings.MP_BASE_API_URL.strip() == "":
            raise ValueError(
                "A variável de ambiente MP_BASE_API_URL não foi definida ou está vazia."
            )

        if not settings.NOTIFICATION_URL or settings.NOTIFICATION_URL.strip() == "":
            raise ValueError(
                "A variável de ambiente NOTIFICATION_URL não foi definida ou está vazia."
            )

        self._access_token = settings.MP_ACCESS_TOKEN.strip()
        self._base_url = settings.MP_BASE_API_URL.strip().rstrip("/")
        self._notification_url = settings.NOTIFICATION_URL.strip()
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }

    def generate_payment_expiration_date(
        self,
        days: int | None = None,
        hours: int | None = None,
        minutes: int | None = None,
    ):
        """
        Gera uma data de expiração no formato ISO 8601 com base no fuso horário configurado.
        """
        try:
            timezone = ZoneInfo(settings.TIME_ZONE)
        except ZoneInfoNotFoundError:
            raise ValueError(
                f'Timezone "{settings.TIME_ZONE}" não encontrado. Verifique a configuração.'
            )

        current_time = datetime.now(timezone)
        time_delta = timedelta(days=days or 0, hours=hours or 0, minutes=minutes or 0)

        # Validação para evitar datas no passado
        if time_delta.total_seconds() <= 0:
            raise ValueError("A data de expiração deve ser no futuro.")

        expiration_date = current_time + time_delta

        return expiration_date.isoformat(timespec="milliseconds")

    def pay_with_pix(
        self,
        amount: float,
        payer_email: str,
        payer_cpf: str,
        description: str = "Pagamento",
    ):
        """
        Cria um pagamento via Pix.
        """
        # Validações de entrada
        if not amount or amount <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero.")

        if not payer_email or "@" not in payer_email:
            raise ValueError("Email do pagador inválido.")

        if not payer_cpf or len(payer_cpf.replace(".", "").replace("-", "")) != 11:
            raise ValueError("CPF do pagador deve ter 11 dígitos.")

        if not description or description.strip() == "":
            raise ValueError("Descrição do pagamento não pode estar vazia.")

        try:
            payload = {
                "payment_method_id": "pix",
                "transaction_amount": float(amount),
                "description": description.strip(),
                "date_of_expiration": self.generate_payment_expiration_date(minutes=30),
                "payer": {
                    "email": payer_email.strip(),
                    "identification": {
                        "type": "CPF",
                        "number": payer_cpf.replace(".", "").replace("-", ""),
                    },
                },
                "external_reference": f"ID-PIX-{uuid.uuid4()}",
                "notification_url": self._notification_url,
            }
            return self._create_payment(payload)
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(f"Erro inesperado ao criar pagamento PIX: {str(e)}")

    def pay_with_boleto(
        self,
        amount: float,
        payer_email: str,
        payer_first_name: str,
        payer_last_name: str,
        payer_cpf: str,
        payer_address: Dict[str, str],
        description: str = "Pagamento",
        days_to_expire: int = 3,
    ):
        """
        Cria um pagamento via Boleto Bancário.
        """
        # Validações de entrada
        if not amount or amount <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero.")

        if not payer_email or "@" not in payer_email:
            raise ValueError("Email do pagador inválido.")

        if not payer_first_name or payer_first_name.strip() == "":
            raise ValueError("Nome do pagador não pode estar vazio.")

        if not payer_last_name or payer_last_name.strip() == "":
            raise ValueError("Sobrenome do pagador não pode estar vazio.")

        if not payer_cpf or len(payer_cpf.replace(".", "").replace("-", "")) != 11:
            raise ValueError("CPF do pagador deve ter 11 dígitos.")

        if not description or description.strip() == "":
            raise ValueError("Descrição do pagamento não pode estar vazia.")

        if not isinstance(payer_address, dict) or not payer_address:
            raise ValueError(
                "Endereço do pagador é obrigatório e deve ser um dicionário."
            )

        required_address_fields = [
            "zip_code",
            "street_name",
            "neighborhood",
            "city",
            "federal_unit",
        ]
        for field in required_address_fields:
            if field not in payer_address or not payer_address[field]:
                raise ValueError(f"Campo obrigatório do endereço ausente: {field}")

        if days_to_expire <= 0 or days_to_expire > 30:
            raise ValueError("Dias para expiração deve ser entre 1 e 30.")

        try:
            payload = {
                "transaction_amount": float(amount),
                "description": description.strip(),
                "payment_method_id": "bolbradesco",
                "date_of_expiration": self.generate_payment_expiration_date(
                    days=days_to_expire
                ),
                "payer": {
                    "first_name": payer_first_name.strip(),
                    "last_name": payer_last_name.strip(),
                    "email": payer_email.strip(),
                    "identification": {
                        "type": "CPF",
                        "number": payer_cpf.replace(".", "").replace("-", ""),
                    },
                    "address": {
                        "zip_code": payer_address.get("zip_code").strip(),
                        "street_name": payer_address.get("street_name").strip(),
                        "street_number": payer_address.get(
                            "street_number", "S/N"
                        ).strip(),
                        "neighborhood": payer_address.get("neighborhood").strip(),
                        "city": payer_address.get("city").strip(),
                        "federal_unit": payer_address.get("federal_unit")
                        .strip()
                        .upper(),
                    },
                },
                "external_reference": f"ID-BOLETO-{uuid.uuid4()}",
                "notification_url": self._notification_url,
            }
            return self._create_payment(payload)
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(
                f"Erro inesperado ao criar pagamento por boleto: {str(e)}"
            )

    def pay_with_card(
        self,
        amount: float,
        payer_email: str,
        payer_cpf: str,
        card_data: dict,
        installments: int = 1,
        description: str = "Pagamento",
    ):
        """
        Cria um pagamento via Cartão de Crédito.
        """
        # Validações de entrada
        if not amount or amount <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero.")

        if not payer_email or "@" not in payer_email:
            raise ValueError("Email do pagador inválido.")

        if not payer_cpf or len(payer_cpf.replace(".", "").replace("-", "")) != 11:
            raise ValueError("CPF do pagador deve ter 11 dígitos.")

        if not description or description.strip() == "":
            raise ValueError("Descrição do pagamento não pode estar vazia.")

        if not isinstance(card_data, dict) or not card_data:
            raise ValueError(
                "Dados do cartão são obrigatórios e devem ser um dicionário."
            )

        required_card_fields = [
            "card_number",
            "expiration_month",
            "expiration_year",
            "security_code",
            "cardholder",
        ]
        for field in required_card_fields:
            if field not in card_data or not card_data[field]:
                raise ValueError(f"Campo obrigatório do cartão ausente: {field}")

        if not isinstance(installments, int) or installments < 1 or installments > 24:
            raise ValueError("Número de parcelas deve ser entre 1 e 24.")

        try:
            card_token = self._get_card_token(card_data)

            if not card_token or "id" not in card_token:
                raise RuntimeError("Falha ao obter token do cartão.")

            payload = {
                "transaction_amount": float(amount),
                "token": card_token.get("id"),
                "description": description.strip(),
                "installments": installments,
                "payer": {
                    "email": payer_email.strip(),
                    "identification": {
                        "type": "CPF",
                        "number": payer_cpf.replace(".", "").replace("-", ""),
                    },
                },
                "external_reference": f"ID-CARTAO-{uuid.uuid4()}",
                "statement_descriptor": "Compra Online",
                "notification_url": self._notification_url,
            }
            return self._create_payment(payload)
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(
                f"Erro inesperado ao criar pagamento com cartão: {str(e)}"
            )

    def get_payment_info(self, transaction_id: str):
        """
        Obtém informações detalhadas sobre um pagamento específico.
        """
        if not transaction_id or transaction_id.strip() == "":
            raise ValueError("ID da transação não pode estar vazio.")

        try:
            data = self._get(f"/v1/payments/{transaction_id.strip()}")
            print(f"Dados do pagamento: {data}")
            return data
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(
                f"Erro inesperado ao buscar informações do pagamento: {str(e)}"
            )

    def create_preference_with_card(self, items: list[dict], order_id: str = None) -> dict:
        """
        Cria uma preferência de pagamento com cartão de crédito ou débito.
        Valida se cada item contém as chaves obrigatórias antes de enviar.
        """
        if not items or not isinstance(items, list):
            raise ValueError("A lista de itens não pode estar vazia e deve ser uma lista.")

        required_keys = {"id", "title", "quantity", "currency_id", "unit_price"}

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"O item na posição {index} não é um dicionário.")
            missing_keys = required_keys - item.keys()
            if missing_keys:
                raise ValueError(f"O item na posição {index} está faltando as chaves: {', '.join(missing_keys)}")

        # Usar a URL base da aplicação ao invés da URL de notificação
        base_url = settings.BASE_APPLICATION_URL.rstrip('/')
        
        try:
            payload = {
                "items": items,
                "back_urls": {
                    "success": f"{base_url}/checkout/pagamento-realizado/{order_id or '1'}/",
                    "failure": f"{base_url}/checkout/erro-pagamento/{order_id or '1'}/",
                    "pending": f"{base_url}/checkout/aguardando-pagamento/{order_id or '1'}/",
                },
                "auto_return": "approved",
                "notification_url": self._notification_url,
            }
            
            # Adiciona external_reference se order_id for fornecido
            if order_id:
                payload["external_reference"] = str(order_id)
                
            return self._post("/checkout/preferences", payload)
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(f"Erro inesperado ao criar preferência: {str(e)}")


    # --- Métodos Internos Auxiliares ---

    def _handle_api_error(self, response):
        """
        Processa uma resposta de erro da API, enriquecendo a mensagem com os mapeamentos de status.
        """
        status_code = response.status_code
        try:
            error_data = response.json()
            
            status = error_data.get("status", "unknown")
            status_detail = error_data.get("status_detail", "unknown")
            message = error_data.get("message", "")
            cause = error_data.get("cause", [])

            status_map_message = self.STATUS_MAP.get(status, "Erro desconhecido.")
            status_detail_map_message = self.STATUS_DETAIL_MAP.get(
                status_detail, "Detalhe desconhecido."
            )

            error_msg = f"Erro na API do Mercado Pago ({status_code}): {status_map_message} - {status_detail_map_message}"
            if message:
                error_msg += f" | Mensagem: {message}"
            if cause:
                error_msg += f" | Causa: {cause}"
            
            return error_msg

        except Exception:
            return f"Erro na API do Mercado Pago ({status_code}): {response.text}"

    def _post(self, path: str, payload: dict, use_idempotency_key: bool = True):
        """
        Executa uma requisição POST para a API do Mercado Pago.
        """
        url = f"{self._base_url}{path}"
        headers = self._headers.copy()

        if use_idempotency_key:
            headers["X-Idempotency-Key"] = str(uuid.uuid4())

        try:
            response = requests.post(
                url=url, headers=headers, json=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_message = self._handle_api_error(e.response)
            raise RuntimeError(error_message)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erro de conexão com a API do Mercado Pago: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Erro inesperado na requisição POST: {str(e)}")

    def _get(self, path: str):
        """
        Executa uma requisição GET para a API do Mercado Pago.
        """
        url = f"{self._base_url}{path}"

        try:
            response = requests.get(url, headers=self._headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error = e.response.json()
            except ValueError:
                error = e.response.text

            raise RuntimeError(f"Erro ao acessar {url}: {error}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erro de conexão com a API do Mercado Pago: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Erro inesperado na requisição GET: {str(e)}")

    def _get_card_token(self, card_data: dict):
        """
        Obtém um token de cartão de crédito.
        """
        try:
            token_response = self._post(
                "/v1/card_tokens", card_data, use_idempotency_key=False
            )

            if not token_response or "id" not in token_response:
                raise RuntimeError("Resposta inválida ao gerar token do cartão.")

            return token_response
        except RuntimeError:
            # Re-propaga erros já tratados
            raise
        except Exception as e:
            raise RuntimeError(f"Erro inesperado ao gerar token do cartão: {str(e)}")

    def _create_payment(self, payload: dict):
        """
        Cria um novo pagamento, adicionando a URL de notificação se configurada.
        """
        try:
            if self._notification_url:
                payload["notification_url"] = self._notification_url

            payment_response = self._post("/v1/payments", payload)

            if not payment_response:
                raise RuntimeError("Resposta vazia ao criar pagamento.")

            return payment_response
        except RuntimeError:
            # Re-propaga erros já tratados
            raise
        except Exception as e:
            raise RuntimeError(f"Erro inesperado ao criar pagamento: {str(e)}")
    
    def _get_base_url(self, url: str) -> str:
        """
        Retorna apenas a URL base (protocolo + domínio).
        Exemplo:
        https://meu.site.com/webhooks/notify -> https://meu.site.com
        """
        if not url or not isinstance(url, str):
            raise ValueError("A URL precisa ser uma string válida.")

        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("A URL fornecida não é válida.")

        return f"{parsed.scheme}://{parsed.netloc}"


mp_service = MercadoPagoService()


def run_test_pay_with_pix():
    """
    Função de teste para pagamento via Pix.
    """
    try:
        response = mp_service.pay_with_pix(
            amount=100.00,
            payer_email="test_user_123@testuser.com",
            payer_cpf="12345678909",
            description="Teste de pagamento com Pix",
        )
        print("--- Resposta PIX ---")
        print(response)
    except Exception as e:
        print(f"Erro ao processar pagamento PIX: {e}")


def run_test_pay_with_boleto():
    address_data = {
        "zip_code": "01001-000",
        "street_name": "Praça da Sé",
        "street_number": "s/n",
        "neighborhood": "Sé",
        "city": "São Paulo",
        "federal_unit": "SP",
    }

    try:
        response = mp_service.pay_with_boleto(
            amount=150.75,
            payer_email="test82281@gmail.com",
            payer_first_name="Carlos",
            payer_last_name="Junior",
            payer_cpf="12345678909",
            payer_address=address_data,
            description="Compra de teste com Boleto",
        )
        print("--- Resposta BOLETO ---")
        print(response)
    except Exception as e:
        print(f"Erro ao processar pagamento com boleto: {e}")


def run_test_pay_with_card():
    """
    Função de teste para pagamento via Cartão de Crédito.
    """
    try:
        card_data = {
            "card_number": "5031433215406351",
            "expiration_month": "11",
            "expiration_year": "2030",
            "security_code": "123",
            "cardholder": {
                # 'name': 'Test User', # Se usar este vai ser aprovado, com as credenciais de teste do Mercado Pago
                "name": "Other User",  # Se usar este vai ser reprovado, com as credenciais de teste do Mercado Pago
                "identification": {"type": "CPF", "number": "12345678909"},
            },
        }

        response = mp_service.pay_with_card(
            amount=200.00,
            card_data=card_data,
            description="Teste de pagamento com Cartão",
            payer_cpf="12345678909",
            payer_email="test1717@gmail.com",
        )
        print("--- Resposta CARTÃO ---")
        print(response)
    except Exception as e:
        print(f"Erro ao processar pagamento com cartão: {e}")


def init():
    """
    Função para executar os testes do MercadoPago de forma síncrona.
    """
    # TEST PIX 💰
    run_test_pay_with_pix()
    print()
    print("---" * 10)

    # TEST BOLETO 📄
    run_test_pay_with_boleto()
    print()
    print("---" * 10)

    # TEST CARTÃO 💳
    run_test_pay_with_card()
    print()
    print("---" * 10)

def test_preference_with_card():
    """
    Função de teste para criar preferência de pagamento com cartão.
    """
    try:
        items = [
            {
                "id": "1",
                "title": "Produto de Teste",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": 10,
            }
        ]
        response = mp_service.create_preference_with_card(items)
        print("--- Resposta PREFERÊNCIA ---")
        print(response)
    except Exception as e:
        print(f"Erro ao criar preferência de pagamento: {e}")
