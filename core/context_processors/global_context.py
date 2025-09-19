# core/context_processors.py
from django.conf import settings


def global_context(request):
    """
    Context processor that adds global company information to all templates
    """
    return {
        "global_info": {
            "company_name": settings.COMPANY_NAME,
            "company_address": settings.COMPANY_ADDRESS,
            "company_contacts": settings.COMPANY_CONTACTS,
            "company_logo_url": settings.COMPANY_LOGO_URL,
            "header_color_start": settings.HEADER_COLOR_START,
            "header_color_end": settings.HEADER_COLOR_END,
        }
    }
