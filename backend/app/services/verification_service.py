from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from app.models.verifications import VerificationResult, VerificationType, VerificationStatus
from app.models.vehicles import Vehicle

class VerificationService:
    # Simulated external failure toggle
    forced_failure_service: str = None # "IDENTITY" or "COMPLIANCE" or None

    @classmethod
    def set_forced_failure(cls, service_name: str, fail: bool):
        if fail:
            cls.forced_failure_service = service_name
        else:
            cls.forced_failure_service = None

    @classmethod
    def verify_identity(cls, db: Session, journey_id: int, vehicle: Vehicle, simulated_override_status: str = None) -> VerificationResult:
        if cls.forced_failure_service == "IDENTITY":
            status = VerificationStatus.UNAVAILABLE
            err = "Identity API Gateway timeout (Simulated Failure)"
            details = json.dumps({"source": "Govt_Reg_DB", "error": "Gateway Timeout 504"})
        elif simulated_override_status:
            status = VerificationStatus[simulated_override_status]
            err = "Simulated status override" if status != VerificationStatus.VALID else None
            details = json.dumps({"source": "Govt_Reg_DB", "simulated": True})
        elif "EXPIRED" in vehicle.vehicle_number:
            status = VerificationStatus.EXPIRED
            err = "Vehicle registration expired on 2026-01-01"
            details = json.dumps({"owner": vehicle.owner_name, "expiry": "2026-01-01"})
        elif "INVALID" in vehicle.vehicle_number:
            status = VerificationStatus.INVALID
            err = "Vehicle registration record flagged as fraudulent"
            details = json.dumps({"owner": vehicle.owner_name, "flag": "BLACKLISTED"})
        else:
            status = VerificationStatus.VALID
            err = None
            details = json.dumps({
                "source": "Govt_Reg_DB",
                "owner": vehicle.owner_name or "Express Logistics Corp",
                "registration_date": "2022-04-15",
                "status": "ACTIVE"
            })

        res = VerificationResult(
            journey_id=journey_id,
            vehicle_id=vehicle.id,
            verification_type=VerificationType.IDENTITY,
            source="Govt_Reg_Authority_V2",
            status=status,
            details=details,
            error_message=err,
            timestamp=datetime.utcnow()
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res

    @classmethod
    def verify_compliance(cls, db: Session, journey_id: int, vehicle: Vehicle, simulated_override_status: str = None) -> VerificationResult:
        if cls.forced_failure_service == "COMPLIANCE":
            status = VerificationStatus.UNAVAILABLE
            err = "Compliance Inspection Portal Connection Refused (Simulated Failure)"
            details = json.dumps({"source": "Permit_Compliance_Center", "error": "Connection Refused"})
        elif simulated_override_status:
            status = VerificationStatus[simulated_override_status]
            err = "Simulated status override" if status != VerificationStatus.VALID else None
            details = json.dumps({"source": "Permit_Compliance_Center", "simulated": True})
        elif "FAIL" in vehicle.vehicle_number or "NON_ELIGIBLE" in vehicle.vehicle_number:
            status = VerificationStatus.INVALID
            err = "Failed emissions inspection certificate test"
            details = json.dumps({"emissions_level": "Euro 3 (Non-compliant)", "safety_cert": "EXPIRED"})
        elif "DUE" in vehicle.vehicle_number:
            status = VerificationStatus.VALID
            err = None
            details = json.dumps({"permit_type": "Hazardous Goods", "permit_status": "DUE_SOON", "expires_in_days": 12})
        else:
            status = VerificationStatus.VALID
            err = None
            details = json.dumps({
                "source": "Permit_Compliance_Center",
                "emissions_cert": "Euro 6 (Compliant)",
                "safety_inspection": "PASSED",
                "valid_until": "2027-10-01"
            })

        res = VerificationResult(
            journey_id=journey_id,
            vehicle_id=vehicle.id,
            verification_type=VerificationType.COMPLIANCE,
            source="Permit_Compliance_Center",
            status=status,
            details=details,
            error_message=err,
            timestamp=datetime.utcnow()
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res
