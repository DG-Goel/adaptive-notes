"""Conservative educational eligibility; layout heuristics never authorize deletion."""
from typing import Literal
from pydantic import BaseModel, ConfigDict

EducationalStatus = Literal['educational', 'noneducational', 'mixed', 'noisy_educational', 'incomplete_educational', 'uncertain']


class EducationalAssessment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: EducationalStatus = 'uncertain'
    reason: str | None = None
    whole_unit_reviewed: bool = False

    @property
    def excluded(self):
        return self.status == 'noneducational' and self.whole_unit_reviewed and bool(self.reason and self.reason.strip())


def validate_exclusions(units, exclusions, cited_source_ids=()):
    """Validate explicit whole-unit exclusions without guessing relevance from text."""
    sources={u.source_id:u for u in units}
    if len(sources)!=len(units):
        raise ValueError('Duplicate canonical source ID')
    seen=set()
    for source_id in exclusions:
        if source_id not in sources or source_id in seen:
            raise ValueError('Unknown or duplicate source exclusion')
        if source_id in cited_source_ids:
            raise ValueError('Cited source cannot be excluded')
        if not sources[source_id].educational_assessment.excluded:
            raise ValueError('Whole-unit exclusion requires an explicit noneducational assessment')
        seen.add(source_id)
    return seen
