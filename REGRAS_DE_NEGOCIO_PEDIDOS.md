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

| Status Operacional | Status Pagamento | Situação | Ações Permitidas | Interface |
|-------------------|------------------|----------|------------------|-----------|
| `pending` | `pending` | Pedido novo | ✅ Todas as ações | Botões: Editar, Concluir, Pagar, Cancelar |
| `pending` | `paid` | Pago, aguarda entrega | ✅ Concluir, editar limitado* | Botões: Editar Info, Concluir, Cancelar |
| `pending` | `cancelled` | Pagamento devolvido | ⚠️ Apenas cancelar pedido | Banner vermelho + Botão: Cancelar |
| `completed` | `pending` | Entregue, aguarda pagamento | ✅ Marcar como pago | Banner azul + Botão: Confirmar Pago |
| `completed` | `paid` | **FINALIZADO** | ❌ Nenhuma alteração | Banner verde: "Finalizado" |
| `completed` | `cancelled` | Entregue, pagamento devolvido | ⚠️ Permitir cancelar entrega* | Banner amarelo + Botão: Cancelar Entrega |
| `cancelled` | `pending` | Cancelado, sem pagamento | ✅ Alterar pagamento | Banner cinza + Botão: Marcar Pago |
| `cancelled` | `paid` | Cancelado, deve devolver | ✅ Cancelar pagamento | Banner vermelho + Botão: Devolver |
| `cancelled` | `cancelled` | Totalmente cancelado | ❌ Nenhuma alteração | Banner cinza: "Cancelado" |

**Legenda de Cores dos Banners**:
- 🟢 **Verde**: Estado finalizado (sucesso completo)
- 🟡 **Amarelo**: Situação especial que requer atenção
- 🔴 **Vermelho**: Problema que requer ação corretiva
- 🔵 **Azul**: Aguardando confirmação de pagamento
- ⚫ **Cinza**: Estados cancelados ou sem ações disponíveis

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

### 🚫 Estado Totalmente Cancelado (`is_totally_cancelled`)
**Condição**: `status == "cancelled" AND payment_status == "cancelled"`

**Bloqueios Aplicados**:
- ❌ Editar pedido (qualquer tipo)
- ❌ Alterar status operacional
- ❌ Alterar status de pagamento
- ❌ Cancelar pedido (já cancelado)
- ❌ Todas as operações exceto visualização
- ✅ Apenas visualização permitida

**Justificativa**: Pedido e pagamento cancelados representam uma transação encerrada que não deve ser modificada.

### ⚠️ Outras Proteções
- **Pedidos Cancelados**: Não podem ter status operacional alterado
- **Pagamentos Cancelados**: Não podem ser alterados para pago/pendente
- **Validação de Troco**: Aplicada apenas para pagamento em dinheiro

### 📝 Edição Limitada para Pedidos Pagos
**Condição**: `payment_status == "paid" AND status != "completed"`

**Edições Permitidas**:
- ✅ Nome do cliente
- ✅ Telefone
- ✅ Endereço de entrega
- ✅ Status operacional

**Edições Bloqueadas**:
- ❌ Adicionar produtos
- ❌ Remover produtos  
- ❌ Alterar quantidades

**Justificativa**: Após o pagamento, os itens devem permanecer inalterados para garantir que o valor pago corresponda aos produtos entregues.

### 🚫 Restrições para Pedidos com Pagamento Cancelado
**Condição**: `status == "pending" AND payment_status == "cancelled"`

**Ações Permitidas**:
- ✅ Visualizar pedido
- ✅ Cancelar pedido

**Ações Bloqueadas**:
- ❌ Editar pedido (informações ou itens)
- ❌ Marcar como concluído
- ❌ Alterar status de pagamento
- ❌ Outras operações de pagamento

**Justificativa**: Quando o pagamento é cancelado/devolvido, o pedido deve ser encerrado via cancelamento para manter a integridade financeira.

### ⚠️ Caso Especial: Entrega Concluída com Pagamento Cancelado
**Condição**: `status == "completed" AND payment_status == "cancelled"`

**Cenário de Uso**: 
- A entrega foi realizada
- Posteriormente foi identificado problema com o produto (defeito, item errado, etc.)
- O dinheiro foi devolvido ao cliente (pagamento cancelado)
- Faz sentido também cancelar a entrega para refletir que a transação foi desfeita

**Ação Permitida**:
- ✅ Cancelar entrega (alterar status para "cancelled")

**Resultado Final**: Pedido fica como `cancelled/cancelled` (totalmente cancelado)

**Justificativa**: Quando uma entrega é concluída mas há devolução de dinheiro por problemas com o produto, é lógico permitir cancelar a entrega também, para que o sistema reflita corretamente que a transação foi totalmente desfeita.

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
- `status == "pending"` OU
- `status == "completed" AND payment_status == "cancelled"` (caso especial)
- `NOT is_finalized`

**Resultado**: Define `status = "cancelled"`
**Nota**: NÃO altera automaticamente o status de pagamento

**Caso Especial Explicado**: Quando uma entrega foi concluída mas o pagamento foi cancelado (por exemplo, produto com defeito e dinheiro devolvido), é possível cancelar também a entrega para refletir que a transação foi totalmente desfeita.

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

#### Banners Informativos por Estado
- **🟢 Finalizado**: "✅ Pedido Finalizado - Não é possível fazer mais alterações"
- **⚫ Totalmente Cancelado**: "🚫 Pedido Totalmente Cancelado - Nenhuma alteração é permitida"
- **🔴 Pending + Cancelled**: "⚠️ Pagamento Cancelado - Apenas o cancelamento do pedido está disponível"
- **🟡 Completed + Cancelled**: "⚠️ Entrega Concluída - Pagamento Devolvido - Você pode cancelar a entrega"
- **⚫ Cancelled + Pending**: "❌ Pedido Cancelado - Pagamento Pendente - Você pode alterar o status do pagamento"
- **🔴 Cancelled + Paid**: "❌ Pedido Cancelado - Precisa Devolver Pagamento - É necessário cancelar o pagamento"
- **🔵 Completed + Pending**: "✅ Entrega Concluída - Aguardando Pagamento - Confirme o recebimento"

### 📋 Lista de Pedidos
- **Filtros**: Por status operacional e status de pagamento
- **Ações Condicionais**: Botões aparecem apenas quando aplicáveis conforme matriz de estados
- **Indicador Mobile**: Estados especiais têm indicadores visuais específicos
- **Responsividade**: Interface adaptada para desktop e mobile

#### Ações Específicas por Estado na Lista:
- **Finalizado**: "✅ Finalizado" (apenas texto)
- **Totalmente Cancelado**: "🚫 Cancelado" (apenas texto)
- **Pending + Cancelled**: Botão "Cancelar Pedido"
- **Completed + Cancelled**: Botão "Cancelar Entrega"
- **Cancelled + Pending**: Botão "Marcar Pago"
- **Cancelled + Paid**: Texto "💰 Devolver"
- **Completed + Pending**: Botão "Confirmar Pago"
- **Pending + Pending**: Botões "Editar", "Concluir", "Marcar Pago", "Cancelar"
- **Pending + Paid**: Botões "Editar Info", "Concluir", "Cancelar"

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

### `can_edit_items`
```python
@property
def can_edit_items(self):
    return self.payment_status != "paid"
```

### `can_edit_basic_info`
```python
@property
def can_edit_basic_info(self):
    return not self.is_finalized and not self.is_totally_cancelled
```

### `is_totally_cancelled`
```python
@property
def is_totally_cancelled(self):
    return self.status == "cancelled" and self.payment_status == "cancelled"
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
1. **Cliente faz pedido** → `pending/pending` → Interface: Todas as ações disponíveis
2. **Cliente paga** → `pending/paid` → Interface: Edição limitada, pode concluir
3. **Entrega realizada** → `completed/paid` → Interface: Banner verde "**FINALIZADO**"

### 🟡 Fluxo Padrão (Pagamento na Entrega)
1. **Cliente faz pedido** → `pending/pending` → Interface: Todas as ações disponíveis
2. **Entrega realizada** → `completed/pending` → Interface: Banner azul "Confirmar Pagamento"
3. **Pagamento confirmado** → `completed/paid` → Interface: Banner verde "**FINALIZADO**"

### 🔴 Fluxo de Cancelamento (Antes do Pagamento)
1. **Cliente faz pedido** → `pending/pending` → Interface: Todas as ações disponíveis
2. **Pedido cancelado** → `cancelled/pending` → Interface: Banner cinza, pode alterar pagamento

### 🔄 Fluxo de Devolução (Após Pagamento)
1. **Pedido pago** → `any/paid` → Interface: Ações limitadas
2. **Pedido cancelado** → `cancelled/paid` → Interface: Banner vermelho "Deve Devolver"
3. **Dinheiro devolvido** → `cancelled/cancelled` → Interface: Banner cinza "**TOTALMENTE CANCELADO**"

### ⚠️ Fluxo Especial (Problema Pós-Entrega)
1. **Entrega concluída** → `completed/pending` → Interface: Banner azul "Confirmar Pagamento"
2. **Pagamento confirmado** → `completed/paid` → Interface: Banner verde "**FINALIZADO**"
3. **Problema identificado** → `completed/cancelled` → Interface: Banner amarelo "Cancelar Entrega"
4. **Entrega cancelada** → `cancelled/cancelled` → Interface: Banner cinza "**TOTALMENTE CANCELADO**"

### 🚫 Fluxo de Rejeição (Pagamento Devolvido)
1. **Cliente faz pedido** → `pending/pending` → Interface: Todas as ações disponíveis
2. **Pagamento devolvido** → `pending/cancelled` → Interface: Banner vermelho "Apenas Cancelar"
3. **Pedido cancelado** → `cancelled/cancelled` → Interface: Banner cinza "**TOTALMENTE CANCELADO**"

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

## 🎯 Resumo de Implementação

### ✅ Estados Totalmente Implementados
Todos os **9 casos** da matriz de estados estão implementados com:
- **Interface específica** para cada combinação de status
- **Ações condicionais** que aparecem apenas quando aplicáveis
- **Banners informativos** com cores e mensagens específicas
- **Proteções de negócio** que impedem operações inválidas

### 🛡️ Proteções Implementadas
- **Pedidos Finalizados**: Imutáveis (completed + paid)
- **Pedidos Totalmente Cancelados**: Imutáveis (cancelled + cancelled)
- **Edição Limitada**: Pedidos pagos só permitem editar informações básicas
- **Caso Especial**: Entrega concluída + pagamento cancelado permite cancelar entrega

### 🎨 Interface Responsiva
- **Desktop**: Tabela com ações inline
- **Mobile**: Cards com ações em botões
- **Filtros**: Por status operacional e de pagamento
- **Indicadores visuais**: Cores e emojis para cada estado

### 📊 Relatórios e Métricas
O sistema permite análise completa através de:
- Filtros por combinação de estados
- Identificação de pedidos que precisam de ação
- Rastreamento de devoluções e cancelamentos
- Monitoramento de pedidos atrasados

---

*Documento atualizado em: Setembro 2025*  
*Versão: 2.0 - Implementação Completa*  
*Sistema: Delivery de Água*  
*Status: ✅ Totalmente Implementado*
