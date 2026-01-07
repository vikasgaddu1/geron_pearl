"""StudySisterRelation model for tracking code reuse between studies.

Sister studies are studies where code/templates can be reused, reducing
the effort required for new work. This model tracks these relationships
and the estimated percentage of code reuse.
"""

from sqlalchemy import Integer, String, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base
from app.db.mixins import TimestampMixin


if TYPE_CHECKING:
    from app.models.study import Study


# Default factor for adapting copied code (30% effort to adapt)
CODE_ADAPTATION_FACTOR = 0.30


class StudySisterRelation(Base, TimestampMixin):
    """Links studies that share code/templates for reuse estimation.
    
    When calculating estimates for a study with a sister study:
    - If code_reuse_percentage is 60%, then:
      - 40% of work is truly new
      - 60% can be adapted from sister study (but still takes some effort)
    
    Effective effort = base_estimate * (1 - reuse%) + (base_estimate * reuse% * adaptation_factor)
    
    Example with 60% reuse and 30% adaptation factor:
    - Original estimate: 100 hours
    - New work: 100 * 0.40 = 40 hours  
    - Adapted code: 100 * 0.60 * 0.30 = 18 hours
    - Total: 58 hours (42% reduction)
    """
    
    __tablename__ = "study_sister_relations"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    primary_study_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The study that can reuse code from the sister study"
    )
    sister_study_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The study providing reusable code/templates"
    )
    
    # Reuse details
    code_reuse_percentage: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        doc="Estimated percentage of code that can be reused (0-100)"
    )
    
    # Optional description of what can be reused
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Description of what code/templates are being reused"
    )
    
    # Categories of reusable components (comma-separated)
    reusable_components: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Types of reusable components: SDTM_specs, ADaM_specs, TLF_shells, macros"
    )
    
    # Relationships
    primary_study: Mapped["Study"] = relationship(
        "Study",
        foreign_keys=[primary_study_id],
        backref="sister_study_sources"
    )
    sister_study: Mapped["Study"] = relationship(
        "Study",
        foreign_keys=[sister_study_id],
        backref="sister_study_targets"
    )
    
    # Unique constraint - only one relation per study pair
    __table_args__ = (
        UniqueConstraint(
            'primary_study_id', 
            'sister_study_id', 
            name='uq_sister_study_pair'
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<StudySisterRelation(primary={self.primary_study_id}, "
            f"sister={self.sister_study_id}, reuse={self.code_reuse_percentage}%)>"
        )
    
    @property
    def effort_reduction_factor(self) -> float:
        """
        Calculate the effort reduction factor for estimation.
        
        Returns a multiplier to apply to base estimates.
        Example: 0.58 means the work will take 58% of the original estimate.
        """
        reuse_fraction = self.code_reuse_percentage / 100
        new_work_fraction = 1 - reuse_fraction
        adapted_work_fraction = reuse_fraction * CODE_ADAPTATION_FACTOR
        return new_work_fraction + adapted_work_fraction
    
    def calculate_adjusted_estimate(self, base_estimate: float) -> float:
        """
        Calculate adjusted estimate accounting for code reuse.
        
        Args:
            base_estimate: Original estimate in hours or complexity points
            
        Returns:
            Adjusted estimate after applying reuse factor
        """
        return base_estimate * self.effort_reduction_factor

