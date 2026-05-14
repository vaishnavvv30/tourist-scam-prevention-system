# pyrefly: ignore [missing-import]
from django.shortcuts import render
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.http import JsonResponse
import json
# pyrefly: ignore [missing-import]
from .services import ai_chat_response, verify_price, find_similar_reports


@login_required
def ai_assistant(request):
    """AI Tourist Assistant page."""
    return render(request, 'ai_engine/assistant.html')


@login_required
def ai_chat_api(request):
    """API endpoint for AI chat."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()

            if not message:
                return JsonResponse({'error': 'Empty message'}, status=400)

            # Get context from recent scam reports
            # pyrefly: ignore [missing-import]
            from scams.models import ScamReport
            recent_reports = ScamReport.objects.order_by('-created_at')[:10]
            context = "\n".join([
                f"- {r.title} ({r.get_category_display()}, {r.location_name}): {r.ai_summary[:100] if r.ai_summary else r.description[:100]}"
                for r in recent_reports
            ])

            result = ai_chat_response(message, context=context)
            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({
                'response': f'Error processing request: {str(e)}',
                'suggestions': ['Try again']
            }, status=500)

    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def ai_price_verify_api(request):
    """API endpoint for quick price verification."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item = data.get('item', '')
            price = float(data.get('price', 0))
            city = data.get('city', '')
            currency = data.get('currency', 'INR')

            result = verify_price(item, price, city, currency)
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def ai_similar_reports(request):
    """Find similar scam reports."""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'results': []})

    similar = find_similar_reports(query)
    results = []
    for item in similar:
        report = item['report']
        results.append({
            'id': report.id,
            'title': report.title,
            'category': report.get_category_display(),
            'similarity': round(item['similarity'] * 100, 1),
            'location': report.location_name,
        })

    return JsonResponse({'results': results})
