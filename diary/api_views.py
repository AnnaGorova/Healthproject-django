from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import HealthRecordSerializer
from .models import HealthRecord




@api_view(['GET'])
def records_list_api(request):
    records = HealthRecord.objects.filter(is_active=True)
    serializer = HealthRecordSerializer(records, many=True)
    return Response(serializer.data)





