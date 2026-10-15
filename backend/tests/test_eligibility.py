from app.models.verifications import VerificationResult, VerificationStatus, VerificationType
from app.models.journeys import JourneyState
from app.rules.eligibility_engine import EligibilityEngine

def test_eligibility_all_valid():
    v1 = VerificationResult(verification_type=VerificationType.IDENTITY, status=VerificationStatus.VALID)
    v2 = VerificationResult(verification_type=VerificationType.COMPLIANCE, status=VerificationStatus.VALID)
    
    decision = EligibilityEngine.evaluate([v1, v2])
    assert decision.is_eligible is True
    assert decision.state == JourneyState.ELIGIBLE

def test_eligibility_expired():
    v1 = VerificationResult(verification_type=VerificationType.IDENTITY, status=VerificationStatus.VALID)
    v2 = VerificationResult(verification_type=VerificationType.COMPLIANCE, status=VerificationStatus.EXPIRED)
    
    decision = EligibilityEngine.evaluate([v1, v2])
    assert decision.is_eligible is False
    assert decision.state == JourneyState.NOT_ELIGIBLE

def test_eligibility_source_unavailable():
    v1 = VerificationResult(verification_type=VerificationType.IDENTITY, status=VerificationStatus.UNAVAILABLE)
    v2 = VerificationResult(verification_type=VerificationType.COMPLIANCE, status=VerificationStatus.VALID)
    
    decision = EligibilityEngine.evaluate([v1, v2])
    assert decision.is_eligible is False
    assert decision.state == JourneyState.HOLD
    assert decision.code == "SOURCE_UNAVAILABLE"
