from rest_framework import status
from django.utils import timezone
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from trains.services import TrainSearchService
from datetime import timedelta


class TrainSearchAPIView(APIView):

    class InputSerializer(serializers.Serializer):
        source_station_code = serializers.CharField(required=True)
        destination_station_code = serializers.CharField(required=True)
        journey_date = serializers.DateField(required=True, format='%Y-%m-%d')

        def validate_journey_date(self, value):
            today = timezone.now().date()
            max_date = today + timedelta(days=120)
            if value < today or value > max_date:
                raise serializers.ValidationError("Date cannot be in the past or more than 120 days from today")
            return value
    
    def get(self, request):
        serializer = self.InputSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        journey_date = serializer.validated_data['journey_date']
        source_station_code = serializer.validated_data['source_station_code']
        destination_station_code = serializer.validated_data['destination_station_code']
        print('inputs:', journey_date, source_station_code, destination_station_code)

        trains_data = TrainSearchService.search_trains(
            TrainSearchService.Input(
                journey_date=journey_date,
                source_station_code=source_station_code,
                destination_station_code=destination_station_code
            )
        )

        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': trains_data,
        })


        
        