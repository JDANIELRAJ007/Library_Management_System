from datetime import datetime


def format_date(dt, fmt='%d %b %Y'):
    if dt is None:
        return '—'
    return dt.strftime(fmt)


def time_ago(dt):
    if dt is None:
        return ''
    delta = datetime.utcnow() - dt
    if delta.days > 365:
        return f'{delta.days // 365}y ago'
    if delta.days > 30:
        return f'{delta.days // 30}mo ago'
    if delta.days > 0:
        return f'{delta.days}d ago'
    hours = delta.seconds // 3600
    if hours > 0:
        return f'{hours}h ago'
    minutes = delta.seconds // 60
    if minutes > 0:
        return f'{minutes}m ago'
    return 'Just now'


def paginate_query(query, page, per_page=12):
    return query.paginate(page=page, per_page=per_page, error_out=False)
