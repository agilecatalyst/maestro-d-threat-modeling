# Referentie — threat-designer-owasped

De fork [`threat-designer-owasped`](../../../threat-designer-owasped) is **geen codebase om verder te migreren**, maar **bron van waarheid** voor:

- Bewezen LLM-pipeline (summary → assets → flows → threats)
- Parser-fallbacks (Gemma JSON, `[TOOL_REQUEST]`, Qwen tool calls)
- QA-captures voor fixtures en Sprint 9-achtige mocks

## Essentiële captures

| Bestand | Inhoud |
|---------|--------|
| [partialexchangeqwen.md](../../../threat-designer-owasped/docs/qa/partialexchangeqwen.md) | Volledige agent-exchange — **pipeline-vragen & tools** |
| [assetresponsegemma4.md](../../../threat-designer-owasped/docs/qa/assetresponsegemma4.md) | Gemma 4 AssetsList JSON |
| [dataflowresponsegemma4.md](../../../threat-designer-owasped/docs/qa/dataflowresponsegemma4.md) | Gemma 4 FlowsList JSON |
| [threat-modeling-llm-pipeline.md](../../../threat-designer-owasped/docs/threat-modeling-llm-pipeline.md) | Fasen & routes |

## Wat we níet meenemen naar Maestro'D

- DynamoDB Local (in-memory)
- MinIO / S3 / boto3 storage
- AWS Lambda / Cognito / Bedrock patterns
- `infra/` Terraform

## Wat we wél overnemen (conceptueel)

- LangGraph workflow-fasen
- Tool-schema's: `AssetsList`, `FlowsList`, `add_threats`, `gap_analysis`, …
- UI-flow: upload tekening → wizard → catalog → export **PDF**
- Sentry als optionele assistent
