from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Equipamento, PortaSwitch
import json

@require_GET
def portas_por_equipamento(request):
    """
    Retorna as portas de um equipamento específico em formato JSON.
    """
    equipamento_id = request.GET.get('equipamento_id')
    if not equipamento_id:
        return JsonResponse({'erro': 'ID do equipamento não fornecido'}, status=400)
    
    try:
        # Verifica se o equipamento existe
        equipamento = get_object_or_404(Equipamento, pk=equipamento_id)
        
        # Obtém as portas do equipamento
        portas = PortaSwitch.objects.filter(
            equipamento=equipamento
        ).values('id', 'numero', 'descricao')
        
        # Converte o QuerySet para uma lista de dicionários
        portas_list = list(portas)
        
        return JsonResponse({
            'equipamento': {
                'id': equipamento.id,
                'nome': equipamento.nome,
                'tipo': equipamento.get_tipo_display(),
            },
            'portas': portas_list
        })
        
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)
