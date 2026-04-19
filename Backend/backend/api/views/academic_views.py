"""
Academic Data Views - Handles academic programmes, batches, and curriculum data
Extracted from the monolithic views.py for enterprise architecture
"""

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from ..models import Batch, Programme
from ..serializers import BatchSerializer, ProgrammeSerializer


@api_view(['GET'])
def get_all_batches(request):
    """Get all academic batches"""
    records = Batch.objects.all().order_by('-year')
    serializer = BatchSerializer(records, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_all_programmes(request):
    """Get all academic programmes"""
    records = Programme.objects.all().order_by('name')
    serializer = ProgrammeSerializer(records, many=True)
    return Response(serializer.data)