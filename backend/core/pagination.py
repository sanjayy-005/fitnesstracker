from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Page based pagination used by every list endpoint.

    GET /api/members/?page=2&page_size=20
    Response: {"count": 57, "next": "...", "previous": "...", "results": [...]}
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
