from jurialmunkey.parser import try_int


def get_next_page(response_headers=None):
    num_pages = try_int(response_headers.get('x-pagination-page-count', 0))
    this_page = try_int(response_headers.get('x-pagination-page', 0))
    if this_page < num_pages:
        return [{'next_page': this_page + 1}]
    return []


class PaginatedItems():
    def __init__(self, items, page=None, limit=None):
        self.all_items = items or []
        self.limit = try_int(limit) or 20
        self.get_page(page)

    def get_page(self, page=None):
        self.page = try_int(page) or 1
        self.index_z = self.page * self.limit
        self.index_a = self.index_z - self.limit
        self.index_z = len(self.all_items) if len(self.all_items) < self.index_z else self.index_z
        self.items = self.all_items[self.index_a:self.index_z]
        self.headers = {
            'x-pagination-page-count': -(-len(self.all_items) // self.limit),
            'x-pagination-page': self.page}
        self.next_page = get_next_page(self.headers)
        return self.items

    def json(self):
        return self.items

    def get_dict(self):
        return {'items': self.items, 'headers': self.headers}
