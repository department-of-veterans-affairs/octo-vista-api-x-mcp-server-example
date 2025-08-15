"""Allergy and adverse reaction models for VistA patient data"""

from datetime import datetime

from pydantic import Field, computed_field

from ..base.common import BaseVistaModel
from .base import BasePatientModel


class AllergyProduct(BaseVistaModel):
    """Product that causes allergic reaction"""

    name: str = Field(..., description="Name of the allergenic product")
    vuid: str | None = Field(
        None, description="VistA Unique Identifier for the product"
    )


class AllergyReaction(BaseVistaModel):
    """Reaction to allergenic product"""

    name: str = Field(..., description="Name/description of the allergic reaction")
    vuid: str | None = Field(
        None, description="VistA Unique Identifier for the reaction"
    )


class Allergy(BasePatientModel):
    """Patient allergy/adverse reaction record"""

    uid: str = Field(..., description="Unique identifier for the allergy record")
    local_id: int = Field(..., alias="localId", description="Local facility identifier")
    facility_code: int = Field(..., alias="facilityCode", description="Facility code")
    facility_name: str = Field(..., alias="facilityName", description="Facility name")

    kind: str = Field(
        ..., description="Type of record (e.g., 'Allergy / Adverse Reaction')"
    )
    summary: str = Field(..., description="Brief summary of the allergy")

    products: list[AllergyProduct] = Field(
        default_factory=list, description="Products that cause allergic reactions"
    )
    reactions: list[AllergyReaction] = Field(
        default_factory=list, description="Allergic reactions experienced"
    )

    entered: datetime | None = Field(
        None, description="Date/time when allergy was entered"
    )
    verified: datetime | None = Field(
        None, description="Date/time when allergy was verified"
    )
    historical: bool | None = Field(
        None, description="Whether this is a historical record"
    )
    reference: str | None = Field(None, description="Reference information")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_verified(self) -> bool:
        """Check if allergy has been verified"""
        return self.verified is not None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def primary_product(self) -> str | None:
        """Get the primary allergenic product name"""
        if self.products:
            return self.products[0].name
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def primary_reaction(self) -> str | None:
        """Get the primary reaction name"""
        if self.reactions:
            return self.reactions[0].name
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def reaction_count(self) -> int:
        """Get the number of reactions documented"""
        return len(self.reactions)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def product_count(self) -> int:
        """Get the number of products documented"""
        return len(self.products)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_products(self) -> str:
        """Get comma-separated list of all product names"""
        return ", ".join(product.name for product in self.products)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_reactions(self) -> str:
        """Get comma-separated list of all reaction names"""
        return ", ".join(reaction.name for reaction in self.reactions)

    def __str__(self) -> str:
        return f"Allergy to {self.primary_product}: {self.primary_reaction}"
