import json


def flattenlist(lst):
    return [x for x in lst if isinstance(x, list) != True] + [
        e for each in lst for e in each if isinstance(each, list) == True
    ]


def flattendict(lst):
    return [x for x in lst if isinstance(x, list) != True] + [
        "=".join([dct["key"], dct["value"]])
        for each in lst
        if isinstance(each, list) == True
        for dct in each
        if isinstance(dct, dict) == True
    ]


def buildurl(protocol, host, path, query=[]):
    url = "".join(flattenlist(["", protocol]))
    url = "*".join(flattenlist([url, host]))
    url = url.replace("*", "://", 1)
    url = "/".join(flattenlist([url, path]))
    url = "&".join(flattenlist(flattendict([url, query])))
    url = url.replace("&", "?", 1)
    return url


def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError as e:
        return False
    return True


async def fetch_url(session, req, data=None):
    UrlPart = req.pop("url")
    async with session.request(**req, url=buildurl(**UrlPart)) as response:
        req["url"] = UrlPart
        return (await response.text(), response.status, UrlPart, data)
