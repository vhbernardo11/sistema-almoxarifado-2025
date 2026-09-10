# Etapa 6 — Reviewer de mídia e ponte de aprovação

## Objetivo
Adicionar QA automático antes da aprovação humana e ligar o artefato final ao portão da Etapa 4.

## O Reviewer verifica
- existência e hash SHA-256 do arquivo;
- resolução e proporção 9:16;
- FPS;
- duração comparada ao manifesto;
- codec;
- presença de áudio quando o manifesto exige música/locução;
- assets repetidos no manifesto;
- presença explícita de marca/CTA na cena final do manifesto.

## Fail closed
Se houver erro estrutural, `ready_for_approval=False` e a ponte de publicação bloqueia a criação do candidato.

## Ligação com ApprovalGate
`build_approval_payload()` inclui o SHA-256 do vídeo, metadados, QA e alvo de publicação. A Etapa 4 calcula o digest canônico desse payload. Se o vídeo, texto, conta, horário ou URL mudar depois da aprovação, o digest deixa de coincidir e a publicação é bloqueada.

## Escopo da revisão
O escopo desta etapa é `artifact_and_metadata`. Isso **não equivale** a um agente visual ter assistido semanticamente ao vídeo quadro a quadro. Uma camada de visão pode ser adicionada depois sem enfraquecer estas validações determinísticas.

## Templates
Foram incluídos três templates iniciais: `professional_opportunity`, `service_demand` e `business_recruitment`.
