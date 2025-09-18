from django.conf import settings


class GlobalTemplateContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        response.context_data = response.context_data or {}
        response.context_data["global_info"] = {
            "company_name": settings.COMPANY_NAME,
        }
        return response
