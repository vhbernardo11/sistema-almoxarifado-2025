# Etapa 5 — mídia

A Etapa 5 foi consolidada no repositório canônico como `src/integra/media`.

## Resultado
- contrato `MediaManifest`;
- cenas estruturadas com duração e movimento;
- renderer determinístico via FFmpeg;
- áudio opcional e desativado por padrão;
- saída vertical 1080x1920 H.264;
- nenhuma dependência obrigatória de TTS ou provedor premium.

O renderer é uma ferramenta executora. Ele não decide estratégia e não publica nada.
