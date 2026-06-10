# Portions adapted from awslabs/threat-designer (Apache-2.0)
# https://github.com/awslabs/threat-designer

from typing import Annotated, List

from pydantic import BaseModel, Field


class DataFlow(BaseModel):
    flow_description: Annotated[str, Field(description="Data flow description")]
    source_entity: Annotated[str, Field(description="Source entity")]
    target_entity: Annotated[str, Field(description="Target entity")]


class TrustBoundary(BaseModel):
    purpose: Annotated[str, Field(description="Boundary purpose")]
    source_entity: Annotated[str, Field(description="Source entity")]
    target_entity: Annotated[str, Field(description="Target entity")]


class ThreatSource(BaseModel):
    category: Annotated[str, Field(description="Threat actor category")]
    description: Annotated[str, Field(description="Relevance description")]
    example: Annotated[str, Field(description="Example actor types")]


class FlowsList(BaseModel):
    data_flows: Annotated[List[DataFlow], Field(description="Data flows")]
    trust_boundaries: Annotated[List[TrustBoundary], Field(description="Trust boundaries")]
    threat_sources: Annotated[List[ThreatSource], Field(description="Threat sources")]
