from rest_framework import status
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from trains.services import TrainSearchService


class TrainSearchAPIView(APIView):

    class InputSerializer(serializers.Serializer):
        source_station_code = serializers.CharField(required=True)
        destination_station_code = serializers.CharField(required=True)
        date = serializers.DateField(required=True, format='%Y-%m-%d')

        def validate_date(self, value):
            today = timezone.now().date()
            if value < today:
                raise serializers.ValidationError("Date cannot be in the past")
            return value
    
    def get(self, request):
        serializer = self.InputSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        date = serializer.validated_data['date']
        source_station_code = serializer.validated_data['source_station_code']
        destination_station_code = serializer.validated_data['destination_station_code']
        print('inputs:', date, source_station_code, destination_station_code)

        trains_data = TrainSearchService.search_trains(
            TrainSearchService.Input(
                date=date,
                source_station_code=source_station_code,
                destination_station_code=destination_station_code
            )
        )

        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': trains_data,
        })


        
        