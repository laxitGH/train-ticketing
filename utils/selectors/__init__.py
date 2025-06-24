from typing import Any, Optional
from django.db.models import QuerySet, Model


class BaseSelectors:
	model: Model = None

	@classmethod
	def generate_queryset(cls, options: 'BaseSelectors.Options | None' = None) -> QuerySet:
		if not cls.model:
			raise ValueError('Model is not set')
		if not options:
			options = cls.Options()
		
		queryset = cls.model.all_objects if options.include_deleted else cls.model.objects
		if options.filters:
			queryset = queryset.filter(**options.filters)
		if options.exclude:
			queryset = queryset.exclude(**options.exclude)
		if options.select_related:
			queryset = queryset.select_related(*options.select_related)
		if options.order_by:
			queryset = queryset.order_by(*options.order_by)
		
		return queryset

	class Options:
		def __init__(
			self,
			filters: Optional[dict] = None,
			exclude: Optional[dict] = None,
			include_deleted: Optional[bool] = None,
			select_related: Optional[list[str]] = None,
			order_by: Optional[list[str]] = None,
		):
			self.filters = filters or {}
			self.exclude = exclude or {}
			self.order_by = order_by or []
			self.select_related = select_related or []
			self.include_deleted = include_deleted or False			
		
		def add_filter(self, key: str, value: Any) -> None:
			if self.filters is None:
				self.filters = {}
			self.filters[key] = value
		
		def add_exclude(self, key: str, value: Any) -> None:
			if self.exclude is None:
				self.exclude = {}
			self.exclude[key] = value

		def add_select_related(self, key: str) -> None:
			if self.select_related is None:
				self.select_related = []
			self.select_related.append(key)

		def add_order_by(self, key: str) -> None:
			if self.order_by is None:
				self.order_by = []
			self.order_by.append(key)

		def add_multiple_filters(self, filters: dict) -> None:
			if self.filters is None:
				self.filters = {}
			self.filters.update(filters)

		def add_multiple_excludes(self, excludes: dict) -> None:
			if self.exclude is None:
				self.exclude = {}
			self.exclude.update(excludes)
