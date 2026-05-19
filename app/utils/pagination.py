def paginate_query(query, page: int = 1, per_page: int = 20):
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "data": pagination.items,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": pagination.pages,
    }
