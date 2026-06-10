# Portions adapted from awslabs/threat-designer (Apache-2.0)
# https://github.com/awslabs/threat-designer

from typing import Annotated, List, Literal

from pydantic import BaseModel, Field


class Assets(BaseModel):
    type: Annotated[
        Literal["Asset", "Entity"],
        Field(description="Asset or Entity"),
    ]
    name: Annotated[str, Field(description="Name of the asset")]
    description: Annotated[str, Field(description="Description")]
    criticality: Annotated[
        Literal["Low", "Medium", "High"],
        Field(default="Medium"),
    ] = "Medium"


class AssetsList(BaseModel):
    assets: Annotated[List[Assets], Field(description="List of assets")]
