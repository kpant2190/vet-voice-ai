"""Insurance verification and payment processing service."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class InsuranceProvider(Enum):
    """Common pet insurance providers."""
    TRUPANION = "trupanion"
    PETPLAN = "petplan"
    HEALTHY_PAWS = "healthy_paws"
    EMBRACE = "embrace"
    FIGO = "figo"
    ASPCA = "aspca"
    PETS_BEST = "pets_best"
    NATIONWIDE = "nationwide"
    OTHER = "other"


class InsuranceVerificationService:
    """Handles insurance verification and payment processing."""
    
    def __init__(self):
        self.supported_providers = {
            provider.value: {
                "name": provider.name.replace("_", " ").title(),
                "verification_method": "api",  # In real implementation
                "typical_coverage": 70  # Default coverage percentage
            }
            for provider in InsuranceProvider
        }
    
    async def verify_insurance_coverage(
        self,
        pet_name: str,
        owner_name: str,
        insurance_provider: str,
        policy_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify pet insurance coverage."""
        
        # In a real implementation, this would integrate with:
        # - Insurance provider APIs
        # - Practice management software
        # - Third-party verification services
        
        provider_key = insurance_provider.lower().replace(" ", "_")
        
        if provider_key in self.supported_providers:
            # Simulate insurance verification
            verification_result = {
                "status": "verified",
                "provider": self.supported_providers[provider_key]["name"],
                "policy_number": policy_number or "XXXX-XXXX-1234",
                "coverage_percentage": 80,
                "deductible_remaining": 150.00,
                "annual_limit": 5000.00,
                "pre_authorization_required": False,
                "covered_services": [
                    "routine_checkups", "vaccinations", "emergency_care",
                    "surgery", "medications", "diagnostic_testing"
                ],
                "excluded_services": ["cosmetic_procedures", "breeding_related"]
            }
            
            return verification_result
        else:
            return {
                "status": "unknown_provider",
                "message": "I'm not familiar with that insurance provider. Let me connect you with our staff who can help verify your coverage."
            }
    
    async def get_cost_estimate(
        self,
        service_type: str,
        insurance_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Provide cost estimates for veterinary services."""
        
        # Base service costs (these would come from practice management system)
        service_costs = {
            "routine_checkup": {"base_cost": 85.00, "description": "Annual wellness exam"},
            "vaccination_package": {"base_cost": 120.00, "description": "Core vaccination series"},
            "dental_cleaning": {"base_cost": 350.00, "description": "Professional dental cleaning"},
            "spay_neuter": {"base_cost": 450.00, "description": "Spay/neuter surgery"},
            "emergency_exam": {"base_cost": 150.00, "description": "Emergency examination"},
            "xray": {"base_cost": 200.00, "description": "Digital X-ray imaging"},
            "blood_work": {"base_cost": 120.00, "description": "Complete blood panel"},
            "microchip": {"base_cost": 45.00, "description": "Microchip implantation"}
        }
        
        if service_type not in service_costs:
            return {
                "status": "unknown_service",
                "message": "Let me connect you with our staff for specific pricing information."
            }
        
        base_cost = service_costs[service_type]["base_cost"]
        description = service_costs[service_type]["description"]
        
        estimate = {
            "service": description,
            "base_cost": base_cost,
            "tax": round(base_cost * 0.08, 2),  # 8% tax
            "total_cost": round(base_cost * 1.08, 2)
        }
        
        if insurance_info and insurance_info.get("status") == "verified":
            coverage_percentage = insurance_info.get("coverage_percentage", 0) / 100
            insurance_coverage = round(base_cost * coverage_percentage, 2)
            out_of_pocket = round(estimate["total_cost"] - insurance_coverage, 2)
            
            estimate.update({
                "insurance_coverage": insurance_coverage,
                "your_cost": out_of_pocket,
                "savings": insurance_coverage
            })
        
        return {"status": "success", "estimate": estimate}
    
    async def process_payment_information(
        self,
        payment_method: str,
        amount: float,
        owner_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process payment information for services."""
        
        # This would integrate with payment processors like:
        # - Stripe, Square, PayPal
        # - Practice management billing systems
        # - Insurance claim processing
        
        if payment_method.lower() in ["credit card", "debit card"]:
            return {
                "status": "payment_scheduled",
                "message": f"I can process a ${amount:.2f} payment when you arrive for your appointment. We accept all major credit cards.",
                "payment_options": ["credit_card", "debit_card", "care_credit", "cash", "check"]
            }
        
        elif payment_method.lower() == "insurance":
            return {
                "status": "insurance_claim",
                "message": "We'll file the insurance claim for you. You'll only need to pay your portion at checkout.",
                "claim_processing_time": "7-14 business days"
            }
        
        elif payment_method.lower() == "payment plan":
            return {
                "status": "payment_plan_available",
                "message": f"We offer payment plans for services over $200. For a ${amount:.2f} service, you could pay as little as ${amount/6:.2f} per month.",
                "plan_options": ["3_months", "6_months", "12_months"]
            }
        
        else:
            return {
                "status": "need_more_info",
                "message": "We accept credit cards, cash, checks, and CareCredit. We can also set up payment plans for larger expenses."
            }
    
    def generate_insurance_response(
        self,
        service_type: str,
        insurance_verification: Dict[str, Any],
        cost_estimate: Dict[str, Any]
    ) -> str:
        """Generate response with insurance and cost information."""
        
        if insurance_verification.get("status") == "verified" and cost_estimate.get("status") == "success":
            estimate = cost_estimate["estimate"]
            
            if "your_cost" in estimate:
                response = (
                    f"Great news! Your {insurance_verification['provider']} insurance "
                    f"covers {insurance_verification['coverage_percentage']}% of the {estimate['service']}. "
                    f"The total cost is ${estimate['total_cost']:.2f}, and with your insurance, "
                    f"you'll only pay ${estimate['your_cost']:.2f} out of pocket."
                )
            else:
                response = (
                    f"For the {estimate['service']}, the total cost would be ${estimate['total_cost']:.2f}. "
                    f"I can verify your {insurance_verification.get('provider', 'insurance')} coverage "
                    f"when you arrive for your appointment."
                )
        
        elif cost_estimate.get("status") == "success":
            estimate = cost_estimate["estimate"]
            response = (
                f"For the {estimate['service']}, the cost is ${estimate['total_cost']:.2f}. "
                f"We accept insurance, credit cards, and offer payment plans for larger expenses."
            )
        
        else:
            response = (
                "I'd be happy to provide you with detailed pricing information. "
                "Let me connect you with our staff who can give you an exact quote "
                "and verify your insurance coverage."
            )
        
        return response
    
    async def detect_insurance_inquiry(self, user_message: str) -> Dict[str, Any]:
        """Detect if the caller is asking about insurance or costs."""
        
        insurance_keywords = [
            "insurance", "coverage", "cost", "price", "how much", "expensive",
            "payment", "bill", "charge", "fee", "estimate", "quote"
        ]
        
        provider_keywords = [
            "trupanion", "petplan", "healthy paws", "embrace", "figo",
            "aspca", "pets best", "nationwide", "pet insurance"
        ]
        
        message_lower = user_message.lower()
        
        has_insurance_keywords = any(keyword in message_lower for keyword in insurance_keywords)
        mentioned_provider = any(provider in message_lower for provider in provider_keywords)
        
        if has_insurance_keywords or mentioned_provider:
            return {
                "is_insurance_inquiry": True,
                "confidence": 0.9 if mentioned_provider else 0.7,
                "requires_information": ["service_type", "insurance_provider"],
                "can_provide_estimate": True
            }
        
        return {"is_insurance_inquiry": False, "confidence": 0.0}
