from datetime import date
from dataclasses import dataclass
from django.db.models import Prefetch
from trains.models import Route, RouteStation, RouteSchedule
from trains.serializers import RouteSerializer, RouteStationWithStationSerializer, RouteScheduleSerializer, TrainSerializer
from utils.queries import QueryUtils


class TrainSearchService:

    @dataclass
    class Input:
        date: date
        source_station_code: str
        destination_station_code: str
        
    class Output(RouteSerializer):
        train = TrainSerializer()
        schedule = RouteScheduleSerializer()
        route_stations = RouteStationWithStationSerializer(many=True)
        destination_route_station = RouteStationWithStationSerializer()
        source_route_station = RouteStationWithStationSerializer()

    @staticmethod
    @QueryUtils.log_queries
    def search_trains(input: Input):
        weekday = input.date.strftime('%a').upper()[:3]
        routes = Route.objects.filter(
            route_stations__station__code__in=[input.source_station_code, input.destination_station_code],
            route_schedules__weekday=weekday
        ).select_related('train').prefetch_related(
            Prefetch(
                'route_stations',
                queryset=RouteStation.objects.select_related('station').order_by('order')
            ),
            Prefetch(
                'route_schedules',
                queryset=RouteSchedule.objects.filter(weekday=weekday)
            )
        ).distinct()

        valid_routes: list[Route] = []
        
        for route in routes:
            print('route:', route)
            route_stations: list[RouteStation] = list(route.route_stations.all())            
            source_route_station: RouteStation = None
            destination_route_station: RouteStation = None
            
            for rs in route_stations:
                print('route_station:', rs)
                if rs.station.code == input.source_station_code:
                    source_route_station = rs
                elif rs.station.code == input.destination_station_code:
                    destination_route_station = rs
            
            if (
                source_route_station and 
                destination_route_station and 
                source_route_station.order < destination_route_station.order
            ):
                valid_routes.append(route)
            
            print()
        
        output_data = []
        for route in valid_routes:
            route_stations = list(route.route_stations.all())
            source_route_station = next((rs for rs in route_stations if rs.station.code == input.source_station_code), None)
            destination_route_station = next((rs for rs in route_stations if rs.station.code == input.destination_station_code), None)
            setattr(route, 'destination_route_station', destination_route_station)
            setattr(route, 'source_route_station', source_route_station)
            
            route_schedules = list(route.route_schedules.all())
            for schedule in route_schedules:
                setattr(route, 'schedule', schedule)
                serializer = TrainSearchService.Output(route)
                output_data.append(serializer.data)

        return output_data
