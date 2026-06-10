# Portions adapted from awslabs/threat-designer (Apache-2.0)
# https://github.com/awslabs/threat-designer

from typing import Annotated, List, Literal

from pydantic import BaseModel, Field

StrideCategory = Literal[
    "Spoofing",
    "Tampering",
    "Repudiation",
    "Information Disclosure",
    "Denial of Service",
    "Elevation of Privilege",
]

Likelihood = Literal["Low", "Medium", "High"]

STRIDE_VALUES = [
    "Spoofing",
    "Tampering",
    "Repudiation",
    "Information Disclosure",
    "Denial of Service",
    "Elevation of Privilege",
]


class Threat(BaseModel):
    name: Annotated[str, Field(description="Concise threat name")]
    stride_category: Annotated[StrideCategory, Field(description="STRIDE category")]
    description: Annotated[str, Field(description="Threat grammar description")]
    target: Annotated[str, Field(description="Target asset or entity")]
    impact: Annotated[str, Field(description="Business or technical impact")]
    likelihood: Annotated[Likelihood, Field(description="Threat likelihood")]
    mitigations: Annotated[
        List[str],
        Field(description="Mitigating controls", min_length=1),
    ]
    source: Annotated[str, Field(description="Threat actor category")]
    prerequisites: Annotated[
        List[str],
        Field(description="Conditions required for the threat"),
    ]
    vector: Annotated[str, Field(description="Attack vector")]


class ThreatsList(BaseModel):
    threats: Annotated[List[Threat], Field(description="Identified threats")]
