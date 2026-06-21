# Referentie — threat-designer-owasped

De fork [`threat-designer-owasped`](https://github.com/AgileCatalystDV/threat-designer-owasped) is **geen codebase om verder te migreren**, maar **bron van waarheid** voor bewezen pipeline-gedrag. **Essentiële captures staan ook in deze repo** (onder `docs/reference/`) zodat Maestro'D self-contained blijft.

## Essentiële captures (in-repo)

| Bestand | Inhoud |
|---------|--------|
| [partialexchangeqwen.md](partialexchangeqwen.md) | Volledige LM Studio / Qwen agent-exchange — **pipeline-vragen & tools** |
| [spar-specs-local-build-experiment.md](spar-specs-local-build-experiment.md) | Spar-artefact v0.1 — local bounded-slice experiment (historisch; actief: [specsrebuild.md](../../specsrebuild.md)) |
| [examples/tmexample1.jpeg](../../examples/tmexample1.jpeg) | Voorbeeld threat-model diagram |

## Essentiële captures (owasped fork, sibling clone)

| Bestand | Inhoud |
|---------|--------|
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
