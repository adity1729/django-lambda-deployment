from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint
    """
    return Response({
        'status': 'healthy',
        'message': 'API is running successfully',
        'timestamp': datetime.now().isoformat()
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def calculate(request):
    """
    Simple calculator endpoint
    Accepts two numbers and an operation (add, subtract, multiply, divide)
    """
    try:
        num1 = float(request.data.get('num1', 0))
        num2 = float(request.data.get('num2', 0))
        operation = request.data.get('operation', 'add')
        
        result = None
        
        if operation == 'add':
            result = num1 + num2
        elif operation == 'subtract':
            result = num1 - num2
        elif operation == 'multiply':
            result = num1 * num2
        elif operation == 'divide':
            if num2 == 0:
                return Response({
                    'error': 'Cannot divide by zero'
                }, status=status.HTTP_400_BAD_REQUEST)
            result = num1 / num2
        else:
            return Response({
                'error': 'Invalid operation. Use: add, subtract, multiply, or divide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'num1': num1,
            'num2': num2,
            'operation': operation,
            'result': result
        }, status=status.HTTP_200_OK)
        
    except (ValueError, TypeError) as e:
        return Response({
            'error': 'Invalid input. Please provide valid numbers.'
        }, status=status.HTTP_400_BAD_REQUEST)


import asyncio
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
@require_http_methods(["GET"])
async def hello_async(request):
    # Simulate async operation
    await asyncio.sleep(0.1)
    
    return JsonResponse({
        'message': 'Hello from Django!',
        'async': True,
        'status': 'success'
    })
@require_http_methods(["POST"])
async def process_data(request):
    # Process data asynchronously
    import json
    data = json.loads(request.body)
    
    # Simulate async processing
    await asyncio.sleep(0.2)
    
    return JsonResponse({
        'received': data,
        'processed': True
    })
