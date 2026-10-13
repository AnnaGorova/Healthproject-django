from django.shortcuts import render


class CustomErrorMiddleware:
    """
    Універсальний middleware для перехоплення 403 і 404.
    Автоматично показує кастомні сторінки для ВСІХ view.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Перехоплюємо 403 (Forbidden)
        if response.status_code == 403:
            return render(request, '403.html', status=403)
        
        # Перехоплюємо 404 (Not Found)
        if response.status_code == 404:
            return render(request, '404.html', status=404)
        
        return response