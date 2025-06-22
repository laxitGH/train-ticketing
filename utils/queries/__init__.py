from django.db import connection
from django.conf import settings


class QueryUtils:

    class QueryCounter:
        def __init__(self, description=""):
            self.initial_queries = 0
            self.description = description

        def __enter__(self):
            if settings.DEBUG:
                self.initial_queries = len(connection.queries)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if settings.DEBUG:
                total_queries = len(connection.queries) - self.initial_queries
                for query in connection.queries[self.initial_queries:]:
                    print("--------------------------------Query--------------------------------")
                    print(query['sql'])

                print()
                print(f"Query count for function [{self.description}]: {total_queries}")
                if total_queries > 5:
                    print(f"Potential N+1 query detected! {total_queries} queries executed")

    @staticmethod
    def log_queries(func):
        def wrapper(*args, **kwargs):
            with QueryUtils.QueryCounter(f"{func.__name__}"):
                return func(*args, **kwargs)
        return wrapper
