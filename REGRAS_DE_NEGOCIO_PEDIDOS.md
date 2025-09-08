# 📋 Regras de Negócio - Sistema de Pedidos

## 📌 Visão Geral

Este documento descreve todas as regras de negócio relacionadas ao ciclo de vida dos pedidos no sistema de delivery de água. O sistema possui dois estados independentes que controlam o fluxo operacional e financeiro.

---

## 🏗️ Estrutura do Pedido

### Campos Principais
- **`customer_name`**: Nome do cliente
- **`phone`**: Telefone para contato
- **`address`**: Endereço de entrega
- **`payment_method`**: Método de pagamento (PIX, Dinheiro, Cartão)
- **`cash_value`**: Valor em dinheiro (quando pagamento é dinheiro)
- **`status`**: Status operacional do pedido
- **`payment_status`**: Status financeiro do pagamento
- **`created_at`**: Data/hora de criação

### Itens do Pedido
- **`OrderItem`**: Produtos e quantidades
- **`total_price`**: Calculado automaticamente
- **`change_amount`**: Troco calculado (quando aplicável)

---

## 🔄 Estados do Sistema

### 📋 Status Operacional (`status`)
| Status | Descrição | Estado |
|--------|-----------|--------|
| `pending` | Pedido aguardando processamento/entrega | 🟡 Ativo |
| `completed` | Pedido entregue com sucesso | 🟢 Concluído |
| `cancelled` | Pedido cancelado | 🔴 Cancelado |

### 💰 Status de Pagamento (`payment_status`)
| Status | Descrição | Estado |
|--------|-----------|--------|
| `pending` | Pagamento pendente/não confirmado | 🟡 Aguardando |
| `paid` | Pagamento confirmado/recebido | 🟢 Confirmado |
| `cancelled` | Pagamento cancelado/devolvido | 🔴 Cancelado |

---

## 📊 Matriz de Estados Possíveis

| Status Operacional | Status Pagamento | Situação | Ações Permitidas |
|-------------------|------------------|----------|------------------|
| `pending` | `pending` | Pedido novo | ✅ Todas as ações |
| `pending` | `paid` | Pago, aguarda entrega | ✅ Concluir, editar limitado |
| `pending` | `cancelled` | Pagamento devolvido | ✅ Cancelar pedido |
| `completed` | `pending` | Entregue, aguarda pagamento | ✅ Marcar como pago |
| `completed` | `paid` | **FINALIZADO** | ❌ Nenhuma alteração |
| `completed` | `cancelled` | Entregue, pagamento devolvido | ❌ Nenhuma alteração |
| `cancelled` | `pending` | Cancelado, sem pagamento | ✅ Alterar pagamento |
| `cancelled` | `paid` | Cancelado, deve devolver | ✅ Cancelar pagamento |
| `cancelled` | `cancelled` | Totalmente cancelado | ❌ Nenhuma alteração |

---

## 🔒 Regras de Proteção

### 🚫 Estado Finalizado (`is_finalized`)
**Condição**: `status == "completed" AND payment_status == "paid"`

**Bloqueios Aplicados**:
- ❌ Editar pedido
- ❌ Alterar status operacional
- ❌ Alterar status de pagamento  
- ❌ Cancelar pedido
- ❌ Cancelar pagamento
- ✅ Apenas visualização permitida

**Justificativa**: Representa uma transação comercial concluída que deve ser imutável para auditoria.

### ⚠️ Outras Proteções
- **Pedidos Cancelados**: Não podem ter status operacional alterado
- **Pagamentos Cancelados**: Não podem ser alterados para pago/pendente
- **Validação de Troco**: Aplicada apenas para pagamento em dinheiro

---

## 🎯 Ações Disponíveis por Estado

### 📝 Editar Pedido
**Disponível quando**:
- `status != "cancelled"`
- `NOT is_finalized`

**Permite alterar**:
- Dados do cliente (nome, telefone, endereço)
- Itens e quantidades
- Método de pagamento
- Valor em dinheiro

### ✅ Marcar como Concluído
**Disponível quando**:
- `status == "pending"`
- `NOT is_finalized`

**Resultado**: Altera status para `completed`

### 🔄 Alterar Status de Pagamento
**Disponível quando**:
- `payment_status != "cancelled"`
- `NOT is_finalized`

**Comportamento**: Alterna entre `pending` ↔ `paid`

### ⚠️ Cancelar Pagamento
**Disponível quando**:
- `payment_status != "cancelled"`
- `NOT is_finalized`

**Resultado**: Define `payment_status = "cancelled"`
**Uso**: Quando há devolução de dinheiro ou estorno

### ❌ Cancelar Pedido
**Disponível quando**:
- `status == "pending"`
- `NOT is_finalized`

**Resultado**: Define `status = "cancelled"`
**Nota**: NÃO altera automaticamente o status de pagamento

---

## 💳 Regras de Pagamento

### PIX / Cartão
- **Troco**: Não aplicável
- **`cash_value`**: Deve ser `null`
- **Confirmação**: Manual pelo admin

### Dinheiro
- **`cash_value`**: Obrigatório e > `total_price`
- **Troco**: Calculado automaticamente (`cash_value - total_price`)
- **Validação**: Valor recebido deve ser suficiente

### Cálculo de Troco
```python
@property
def change_amount(self):
    if self.payment_method == "dinheiro" and self.cash_value:
        return max(0, self.cash_value - self.total_price)
    return Decimal('0.00')
```

---

## 📱 Interface do Usuario

### 🎨 Indicadores Visuais

#### Status Operacional
- 🟡 **Pendente**: Amarelo, pode ter indicador de atraso (>25min)
- 🟢 **Concluído**: Verde
- 🔴 **Cancelado**: Vermelho

#### Status de Pagamento
- 🟡 **Pendente**: Texto amarelo
- 🟢 **Pago**: Texto verde
- 🔴 **Cancelado/Devolvido**: Texto vermelho + explicação

#### Estado Finalizado
- ✅ **Banner Verde**: "Pedido Finalizado - Não é possível fazer mais alterações"
- 🔒 **Botões Ocultos**: Todas as ações de modificação removidas

### 📋 Lista de Pedidos
- **Filtros**: Por status operacional e status de pagamento
- **Ações Condicionais**: Botões aparecem apenas quando aplicáveis
- **Indicador Mobile**: "✅ Finalizado" substitui botões de ação

---

## 🔔 Notificações WhatsApp

### Para o Admin (Novo Pedido)
```
🚨 NOVO PEDIDO RECEBIDO!

Cliente: [nome]
Telefone: [telefone]
Endereço: [endereço]

Itens do pedido:
• [produto] (x[quantidade])

Total: R$ [valor]

Pagamento:
[método]
Status: [status_pagamento]
[informações de troco, se aplicável]
```

### Para o Cliente (Confirmação)
```
✅ Pedido Confirmado!

Olá [nome], seu pedido foi confirmado com sucesso!

Resumo do pedido:
Total: R$ [valor]
Pagamento: [informações]

Em breve entraremos em contato para combinar a entrega.

Obrigado pela preferência!
```

---

## 🔍 Propriedades Calculadas

### `is_paid`
```python
@property
def is_paid(self):
    return self.payment_status == "paid"
```

### `is_late`
```python
@property
def is_late(self):
    elapsed_time = timezone.now() - self.created_at
    return (elapsed_time > timedelta(minutes=25)) and self.status == "pending"
```

### `is_finalized`
```python
@property
def is_finalized(self):
    return self.status == "completed" and self.payment_status == "paid"
```

### `change_amount`
```python
@property
def change_amount(self):
    if self.payment_method == "dinheiro" and self.cash_value:
        return max(0, self.cash_value - self.total_price)
    return Decimal('0.00')
```

---

## 📈 Fluxos de Trabalho Típicos

### 🟢 Fluxo Ideal (Pagamento Antecipado)
1. **Cliente faz pedido** → `pending/pending`
2. **Cliente paga** → `pending/paid`
3. **Entrega realizada** → `completed/paid` (**FINALIZADO**)

### 🟡 Fluxo Padrão (Pagamento na Entrega)
1. **Cliente faz pedido** → `pending/pending`
2. **Entrega realizada** → `completed/pending`
3. **Pagamento confirmado** → `completed/paid` (**FINALIZADO**)

### 🔴 Fluxo de Cancelamento (Antes do Pagamento)
1. **Cliente faz pedido** → `pending/pending`
2. **Pedido cancelado** → `cancelled/pending`

### 🔄 Fluxo de Devolução (Após Pagamento)
1. **Pedido pago** → `any/paid`
2. **Pedido cancelado** → `cancelled/paid`
3. **Dinheiro devolvido** → `cancelled/cancelled`

---

## 🛠️ Manutenção e Auditoria

### Logs Automáticos
- Todas as alterações de status são registradas
- Timestamps preservados para auditoria
- Histórico de pagamentos mantido

### Validações de Integridade
```bash
# Comando para verificar inconsistências
python manage.py check
```

### Relatórios Disponíveis
- Pedidos por período
- Status de pagamentos pendentes
- Pedidos em atraso
- Devoluções realizadas

---

## 🚀 Considerações Técnicas

### Performance
- Uso de `select_related()` para carregar itens
- Propriedades calculadas para evitar queries desnecessárias
- Índices em campos de filtro

### Segurança
- Validação server-side em todas as alterações
- Confirmações obrigatórias para ações críticas
- Proteção CSRF em todos os formulários

### Escalabilidade
- Modelo preparado para múltiplos vendedores
- Status extensíveis conforme necessidade
- API endpoints disponíveis para integração

---

*Documento criado em: Setembro 2025*  
*Versão: 1.0*  
*Sistema: Delivery de Água*
