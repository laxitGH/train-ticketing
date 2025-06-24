from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class Paginator(PageNumberPagination):
    page_size = 10
    max_page_size = 25
    page_size_query_param = 'page_size'
    
    def get_paginated_response(self, data):
        return Response({
            'status': True,
            'status_code': 200,
            'pagination': {
                'current_page': self.page.number,
                'count': self.page.paginator.count,
                'page_size': self.get_page_size(self.request),
                'total_pages': self.page.paginator.num_pages,
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link()
                },
            },
            'result': data
        }) 