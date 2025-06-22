from trains.models import Route, Stop


class StationModelUtils:
    pass


class TrainModelUtils:
    pass


class RouteModelUtils:
    
    @staticmethod
    def get_total_duration_minutes(
        source_stop: Stop | None = None,
        destination_stop: Stop | None = None,
        stops_of_route: list[Stop] | None = None,
        route: Route | None = None,
    ) -> int:
        if source_stop and destination_stop:
            ordered_stops = sorted([source_stop, destination_stop], key=lambda x: x.order)
        elif stops_of_route:
            ordered_stops = sorted(list(stops_of_route), key=lambda x: x.order)
        elif route:
            ordered_stops = sorted(list(route.stops_of_route.all()), key=lambda x: x.order)
        else:
            raise ValueError('Either source_stop, destination_stop or route must be provided')
        
        return int(ordered_stops[-1].arrival_minutes_from_source - ordered_stops[0].departure_minutes_from_source)
    
    @staticmethod
    def get_total_distance_kms(
        source_stop: Stop | None = None,
        destination_stop: Stop | None = None,
        stops_of_route: list[Stop] | None = None,
        route: Route | None = None,
    ) -> float:
        if source_stop and destination_stop:
            ordered_stops = sorted([source_stop, destination_stop], key=lambda x: x.order)
        elif stops_of_route:
            ordered_stops = sorted(list(stops_of_route), key=lambda x: x.order)
        elif route:
            ordered_stops = sorted(list(route.stops_of_route.all()), key=lambda x: x.order)
        else:
            raise ValueError('Either source_stop, destination_stop or route must be provided')
        
        return float(ordered_stops[-1].distance_kms_from_source - ordered_stops[0].distance_kms_from_source)


class StopModelUtils:
    pass


class ScheduleModelUtils:
    pass