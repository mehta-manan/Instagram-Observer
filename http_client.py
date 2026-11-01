from urllib import request, parse

import logging
logger = logging.getLogger(__name__)

def fetch(
    url,
    method='GET',
    params=None,
    data=None,
    headers=None):
        
    if params:
        query_string = parse.urlencode(params)
        url = f"{url}?{query_string}"

    req = request.Request(
        url,
        method=method,
        data=data,
        headers=headers or {})

    with request.urlopen(req) as res:
        logger.info("HTTP %s → %s", method, url)
        return res.read()