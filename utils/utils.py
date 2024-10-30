import json, aiohttp, asyncio, random, allure, re, urllib, copy, bs4, functools, itertools

LoadMoreElement = 'a[class*="btn"][data-behavior*="getMoreTiles"]'
CSRF = "Fetch"
Headers = {"content-type": "text/plain", "X-CSRF-Token": CSRF}
AjaxUrl = {
    "protocol": "https",
    "host": "gosuslugi29.ru",
    "path": ["util", "ajaxRpc.sx"],
}
ListMethods = {
    "method": "GET",
    "url": {
        **AjaxUrl,
        "query": [
            {
                "key": "v",
                "value": urllib.parse.quote(
                    '{"id":1, method:"system.listMethods", "params":[]}'
                ),
            }
        ],
    },
    "headers": Headers,
    "ssl": False,
}
TokenEnabledUrl = {
    "method": "POST",
    "url": {
        **AjaxUrl,
        "query": [{"key": "_", "value": "securitypreventiontoken.isEnabled"}],
    },
    "data": json.dumps(
        {"method": "securitypreventiontoken.isEnabled", "params": [], "id": 2}
    ),
    "headers": Headers,
    "ssl": False,
}
RestTokenUrl = {
    "method": "POST",
    "url": {
        **AjaxUrl,
        "query": [{"key": "_", "value": "securitypreventiontoken.getRestToken"}],
    },
    "data": json.dumps(
        {"method": "securitypreventiontoken.getRestToken", "params": [], "id": 3}
    ),
    "headers": Headers,
    "ssl": False,
}
TokenUrl = {
    "method": "POST",
    "url": {
        **AjaxUrl,
        "query": [{"key": "_", "value": "securitypreventiontoken.getToken"}],
    },
    "data": json.dumps(
        {"method": "securitypreventiontoken.getToken", "params": [], "id": 3}
    ),
    "headers": Headers,
    "ssl": False,
}
PubBlockUrl = {
    "method": "POST",
    "url": {**AjaxUrl, "query": [{"key": "_", "value": "pubblock.renderZone"}]},
    "data": json.dumps(
        {
            "method": "pubblock.renderZone",
            "params": [
                "",
                "center",
                {
                    "javaClass": "java.util.HashMap",
                    "map": {
                        "f": '',
                        "id": '',
                    },
                },
            ],
            "id": 4,
        }
    ),
    "headers": Headers,
    "ssl": False,
}

RestServiceMethods = [ListMethods, TokenEnabledUrl, RestTokenUrl]
AuthorizationServiceMethods = [ListMethods, TokenEnabledUrl, RestTokenUrl, TokenUrl]

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


def gen_dict_extract(var, key):
    if hasattr(var, "items"):  # hasattr(var,'items') for python 3
        for k, v in var.items():  # var.items() for python 3
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(v, key):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(d, key):
                        yield result


async def fetch_url(session, req, data=None):
    try:
        UrlPart = req.pop("url")
        async with session.request(**req, url=buildurl(**UrlPart)) as response:
            req["url"] = UrlPart
            return (await response.text(), response.status, UrlPart, data)
    except aiohttp.client_exceptions.ClientOSError as e:
        await asyncio.sleep(3 + random.randint(0, 9))
        async with session.request(**req, url=buildurl(**UrlPart)) as response:
            req["url"] = UrlPart
            return (await response.text(), response.status, UrlPart, data)
    except Exception as e:
        result = str(e)
    return (result, 0, UrlPart, data)


async def get_service_pages(session, methods):
    ajaxpages = []
    for ConfigUrl in methods:
        UrlPart = ConfigUrl.pop("url")
        with allure.step(
            f"Асинхронно сделать запрос к вспомогательной странице {buildurl(**UrlPart)}"
        ):
            ajaxresponse = await session.request(**ConfigUrl, url=buildurl(**UrlPart))
            ConfigUrl["url"] = UrlPart
            ajaxresponsetext = await ajaxresponse.text()
            ajaxpages.append(
                {
                    "status": ajaxresponse.status,
                    "text": ajaxresponsetext,
                    "url": buildurl(**UrlPart),
                }
            )
    return ajaxpages


def update_services(pages, headers):
    CSRFpattern = re.compile(r"\w{32}")
    for catalogpage in pages:
        with allure.step(f"Найти CSRF-токен {catalogpage['url']}"):
            if is_json(catalogpage["text"]):
                jsonres = json.loads(catalogpage["text"])
                if "result" in jsonres and isinstance(jsonres["result"], str):
                    if CSRFpattern.match(jsonres["result"]):
                        headers["X-CSRF-Token"] = jsonres["result"]


async def get_pubblockurl_pages(session, expandingpages, upddict):
    departmentpages = []
    variant,link = upddict.pop("name"), upddict.pop("link")
    for page, _ in expandingpages.items():
        loadmore = True
        loadmoreelement = []
        f = 1
        with allure.step(f"Асинхронно сделать запрос к странице {page}"):
            while loadmore:
                copys = []
                for _ in range(2):
                    PubBlockUrl["data"] = json.loads(PubBlockUrl["data"])
                    upddict.update({"f": f, "id": page, variant: page})
                    PubBlockUrl["data"]["params"][2]["map"] = upddict
                    PubBlockUrl["data"]["params"][0] = link
                    PubBlockUrl["data"] = json.dumps(PubBlockUrl["data"])
                    copys.append(copy.deepcopy(PubBlockUrl))
                    f += 12
                tasks = [(fetch_url(session, url)) for url in copys]
                responses = asyncio.gather(*tasks)
                await responses
                for searchresponse in responses.result():
                    try:
                        departmentpages.append(
                            {
                                "status": searchresponse[1],
                                "text": searchresponse[0],
                                "url": searchresponse[2],
                                "lst": page,
                            }
                        )
                        soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                        loadmoreelement.append(
                            len(soup.select(LoadMoreElement)) != 0
                        )
                    except Exception as e:
                        print(e.message)
                loadmore = all(loadmoreelement)
    return departmentpages

def get_ids(pages,cls):
    serviceids = {}
    for page in pages:
        with allure.step(
            f"Выделить услуги на странице {buildurl(**page['url'])}"
        ):
            if is_json(page["text"]):
                soup = bs4.BeautifulSoup(json.loads(page["text"])["result"], "lxml")
            else:
                soup = bs4.BeautifulSoup(page["text"], "lxml")
            serviceattrs = {service.attrs[cls.Attribute]: {"name": " ".join([title.text for title in service.select(cls.ElementName)])}for service in soup.select(cls.Element)}
            if serviceids.get(page["lst"]) == None:
                serviceids[page["lst"]] = serviceattrs
            else:
                serviceids[page["lst"]].update(serviceattrs)
    with allure.step(f"Отфильтровать услуги"):
        unique = functools.reduce(set.union,(itertools.starmap(set.symmetric_difference,itertools.combinations(map(set, serviceids.values()), 2),)),)
        [[unique.remove(service) if service in unique else services.pop(service) for service in list(services)]for services in serviceids.values()]
    return serviceids