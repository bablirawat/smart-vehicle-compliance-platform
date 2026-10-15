from typing import List, Tuple
from app.models.verifications import VerificationResult, VerificationStatus, VerificationType
from app.models.journeys import JourneyState

class EligibilityDecision:
    def __init__(self, state: JourneyState, code: str, message: str, is_eligible: bool):
        self.state = state
        self.code = code
        self.message = message
        self.is_eligible = is_eligible

class EligibilityEngine:
    @staticmethod
    def evaluate(verifications: List[VerificationResult]) -> EligibilityDecision:
        if not verifications:
            return EligibilityDecision(
                state=JourneyState.NOT_ELIGIBLE,
                code="NO_VERIFICATION_DATA",
                message="No verification records found for journey",
                is_eligible=False
            )

        identity_res = next((v for v in verifications if v.verification_type == VerificationType.IDENTITY), None)
        compliance_res = next((v for v in verifications if v.verification_type == VerificationType.COMPLIANCE), None)

        # 1. Check external service unavailable
        if (identity_res and identity_res.status == VerificationStatus.UNAVAILABLE) or \
           (compliance_res and compliance_res.status == VerificationStatus.UNAVAILABLE):
            return EligibilityDecision(
                state=JourneyState.HOLD,
                code="SOURCE_UNAVAILABLE",
                message="External verification authority is currently unavailable. Sent for manual operator review.",
                is_eligible=False
            )

        # 2. Check timeout or not found
        if (identity_res and identity_res.status in [VerificationStatus.TIMEOUT, VerificationStatus.NOT_FOUND]) or \
           (compliance_res and compliance_res.status in [VerificationStatus.TIMEOUT, VerificationStatus.NOT_FOUND]):
            return EligibilityDecision(
                state=JourneyState.HOLD,
                code="VERIFICATION_FAILED",
                message="Vehicle identity or compliance records could not be verified automatically.",
                is_eligible=False
            )

        # 3. Check invalid or expired
        if (identity_res and identity_res.status in [VerificationStatus.INVALID, VerificationStatus.EXPIRED]):
            return EligibilityDecision(
                state=JourneyState.NOT_ELIGIBLE,
                code="REGISTRATION_INVALID_OR_EXPIRED",
                message=f"Vehicle registration verification failed: {identity_res.status.value}",
                is_eligible=False
            )

        if (compliance_res and compliance_res.status in [VerificationStatus.INVALID, VerificationStatus.EXPIRED]):
            return EligibilityDecision(
                state=JourneyState.NOT_ELIGIBLE,
                code="COMPLIANCE_INVALID_OR_EXPIRED",
                message=f"Vehicle compliance/permit verification failed: {compliance_res.status.value}",
                is_eligible=False
            )

        # 4. Check due soon condition
        if compliance_res and compliance_res.details and "DUE_SOON" in compliance_res.details:
            return EligibilityDecision(
                state=JourneyState.ELIGIBLE,
                code="DUE_SOON",
                message="Vehicle permit is due for renewal within 30 days. Allowed to proceed with warning.",
                is_eligible=True
            )

        # 5. All Valid
        return EligibilityDecision(
            state=JourneyState.ELIGIBLE,
            code="ELIGIBLE",
            message="Vehicle passed all identity and compliance verifications.",
            is_eligible=True
        )

eligibility_engine = EligibilityEngine()
