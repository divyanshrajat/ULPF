from typing import Any

class ValidationError(Exception):
    pass

class RuleValidator:
    @staticmethod
    def validate_extracted_fields(extracted: dict[str, Any], required_fields: list[str], type_constraints: dict[str, str] = None) -> None:
        """
        Validates that extracted fields meet requirement and type constraints.
        Raises ValidationError if validation fails.
        """
        if required_fields:
            missing = [f for f in required_fields if f not in extracted]
            if missing:
                raise ValidationError(f"Missing required fields: {missing}")
                
        if type_constraints:
            for field, type_name in type_constraints.items():
                if field in extracted:
                    val = extracted[field]
                    if not RuleValidator._check_type(val, type_name):
                        raise ValidationError(f"Field '{field}' with value '{val}' does not match type constraint '{type_name}'")
                        
    @staticmethod
    def _check_type(val: Any, type_name: str) -> bool:
        type_name = type_name.lower()
        if type_name in ("int", "integer"):
            try:
                int(val)
                return True
            except (ValueError, TypeError):
                return False
        elif type_name == "float":
            try:
                float(val)
                return True
            except (ValueError, TypeError):
                return False
        elif type_name == "ip":
            import ipaddress
            try:
                ipaddress.ip_address(str(val).strip())
                return True
            except ValueError:
                return False
        elif type_name == "datetime":
            from dateutil import parser
            try:
                parser.parse(str(val))
                return True
            except Exception:
                return False
        elif type_name == "boolean":
            return str(val).lower() in ("true", "false", "1", "0", "yes", "no")
        return True
