from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class PipelineErrorSummary(BaseModel):
    pipeline_id: str
    project_id: str
    branch: str
    failed_job_name: str
    error_log_snippet: str
    error_type: str

class AnalysisResult(BaseModel):
    is_deterministic: bool
    error_type: str
    category: Literal["code", "dependency", "security", "infrastructure"]
    severity: Literal["low", "medium", "high", "critical"]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    requires_llm: bool
    auto_fix: bool
    decision: Literal["AUTO_FIX", "ESCALATE_LLM", "ESCALATE_HUMAN"]
    decision_reason: str
    root_cause: str
    proposed_fix_description: str
    file_to_modify: str
    code_patch: str
    requires_human_escalation: bool
    recommended_human_action: Optional[str] = None

class ValidationResult(BaseModel):
    is_valid: bool
    feedback: str
    exit_code: int

class EscalationResult(BaseModel):
    decision: Literal["escalate"] = "escalate"
    reason: str
    human_action_required: str
    retry_after_action: bool

class AuditReport(BaseModel):
    execution_id: Optional[int] = None
    timestamp: str
    execution_mode: str
    status: Literal["SUCCESS", "FAILED", "ESCALATED"]
    test_case: str
    checks: Dict[str, bool]
    pipeline: Dict[str, str]
    resolution: Dict[str, Any]
    supervisor_action: Literal["APPROVE_MR", "REJECT_MR", "ESCALATE_HUMAN", "NONE"]
    