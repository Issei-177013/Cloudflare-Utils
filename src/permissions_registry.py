from typing import Dict, List

# Defines the Cloudflare API permission groups required for each feature.
# The keys are feature names used internally, and the values are lists of
# permission group names as returned by the Cloudflare API.
FEATURE_PERMISSIONS: Dict[str, List[str]] = {
    "ip_rotation": ["Zone.DNS"],
    "zone_management": ["Zone.DNS", "Zone.Zone"],
    # Permission to check the token's own permissions.
    "token_validation": ["API Tokens Read"],
}
