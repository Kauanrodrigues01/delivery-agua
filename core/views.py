from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Health check endpoint para monitoramento da aplicação
    """
    try:
        # Test DB connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Test cache
        cache.set('health_check', 'ok', 30)
        cache_ok = cache.get('health_check') == 'ok'

        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok' if cache_ok else 'error',
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


def cache_stats_view(request):
    """
    View para mostrar estatísticas do cache (apenas para admins)
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        # Verificar se o Redis está disponível
        from django_redis import get_redis_connection

        # Obter conexão Redis diretamente
        redis_conn = get_redis_connection("default")
        info = redis_conn.info()

        stats = {
            'used_memory': info.get('used_memory_human', 'N/A'),
            'used_memory_peak': info.get('used_memory_peak_human', 'N/A'),
            'total_keys': info.get('db1', {}).get('keys', 0),
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'redis_version': info.get('redis_version', 'N/A'),
            'connected_clients': info.get('connected_clients', 0),
        }

        # Calcular hit ratio
        hits = stats['hits']
        misses = stats['misses']
        stats['hit_ratio'] = round(hits / (hits + misses), 4) if (hits + misses) > 0 else 0

        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
