# Just somthings we need :]
from src.core.config import REQUIRED_PERMISSIONS
from .i18n import t

lri, pdi = "\u2066", "\u2069"


def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))

def format_token_guidance_html(lang="en"):
    """
    Generates an HTML-formatted string for the token guidance message.
    """
    permissions_html = ""
    for perm, level in REQUIRED_PERMISSIONS['permissions'].items():
        permissions_html += f"  - <code>{perm}: {level}</code>\n"

    guidance = (
        f"<b>{t('token_guidance_title', lang)}</b>\n\n"
        f"{t('token_guidance_intro', lang)}\n"
        f"<a href=\"https://dash.cloudflare.com/profile/api-tokens\">{t('token_guidance_link_text', lang)}</a>\n\n"
        f"<b>{t('token_guidance_steps_title', lang)}</b>\n"
        f"1. {t('token_guidance_step1', lang)}\n"
        f"2. {t('token_guidance_step2', lang)}\n"
        f"3. {t('token_guidance_step3', lang)}\n"
        f"<blockquote>{permissions_html}</blockquote>\n"
        f"4. {t('token_guidance_step4', lang)}\n"
        f"5. {t('token_guidance_step5', lang)}\n"
    )
    return guidance