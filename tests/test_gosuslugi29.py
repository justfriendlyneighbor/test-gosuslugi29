import allure, pytest, bs4, lxml, re, json, asyncio, aiohttp, copy, time, urllib, allure_subtests
import config.CatalogConfig as Catalog, config.CategoryConfig as Category, config.ServiceConfig as Service, config.TargetConfig as Target, config.AuthorizationConfig as Authorization
from utils.utils import *


@allure.title("Find Categories")
@pytest.mark.asyncio
async def test_getLinksCategoriesAsync(request):
    async with aiohttp.ClientSession() as session:
        UrlPart = Catalog.PageUrl.pop("url")
        pageresponse = await session.request(**Catalog.PageUrl, url=buildurl(**UrlPart))
        Catalog.PageUrl["url"] = UrlPart
        assert pageresponse.status == 200
        UrlPart = Catalog.SearchUrl.pop("url")
        searchresponse = await session.request(
            **Catalog.SearchUrl, url=buildurl(**UrlPart)
        )
        searchresponsetext, searchresponsestatus = (
            await searchresponse.text(),
            searchresponse.status,
        )
        Catalog.SearchUrl["url"] = UrlPart
        assert pageresponse.status == 200 and searchresponsestatus == 200
        soup = bs4.BeautifulSoup(searchresponsetext, "lxml")
        categories = soup.select(Catalog.Element)
        attribute = re.compile(Catalog.Regex)
        categoryids = [category.attrs["data-objid"] for category in categories]
        assert len(categories) > 0
        assert all(attribute.match(categoryid) for categoryid in categoryids)
        request.config.categories = dict.fromkeys(categoryids, "")


@allure.title("Find Services per Category")
@pytest.mark.asyncio
async def test_getLinksServicesAsync(request):
    async with aiohttp.ClientSession() as session:
        for ConfigUrl in [
            Category.ListMethods,
            Category.TokenEnabledUrl,
            Category.RestTokenUrl,
        ]:
            UrlPart = ConfigUrl.pop("url")
            ajaxresponse = await session.request(**ConfigUrl, url=buildurl(**UrlPart))
            ajaxresponsetext, ajaxresponsecode = (
                await ajaxresponse.text(),
                ajaxresponse.status,
            )
            ConfigUrl["url"] = UrlPart
            if is_json(ajaxresponsetext):
                jsonres = json.loads(ajaxresponsetext)
                if "result" in jsonres and isinstance(jsonres["result"], str):
                    CSRFpattern = re.compile("\w{32}")
                    if CSRFpattern.match(jsonres["result"]):
                        ConfigUrl["headers"]["X-CSRF-Token"] = jsonres["result"]
        assert Category.Headers["X-CSRF-Token"] != "Fetch"
        for category, _ in request.config.categories.items():
            loadmore = True
            loadmoreelement = []
            f = 1
            serviceids = []
            while loadmore:
                copys = []
                for _ in range(7):
                    Category.PubBlockUrl["data"] = json.loads(
                        Category.PubBlockUrl["data"]
                    )
                    Category.PubBlockUrl["data"]["params"][2]["map"] = {
                        "f": f,
                        "category": category,
                        "g": "tiles",
                        "isTemplate": "24326@egClassification",
                        "id": category,
                    }
                    Category.PubBlockUrl["data"] = json.dumps(
                        Category.PubBlockUrl["data"]
                    )
                    copys.append(copy.deepcopy(Category.PubBlockUrl))
                    f += 12
                tasks = [(fetch_url(session, url)) for url in copys]
                responses = asyncio.gather(*tasks)
                await responses
                for searchresponse in responses.result():
                    assert ajaxresponsecode == 200 and searchresponse[1] == 200
                    soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                    loadmoreelement.append(
                        len(soup.select(Category.LoadMoreElement)) != 0
                    )
                    attribute = re.compile(Category.Regex)
                    serviceids.append(
                        [
                            service.attrs["data-pgu-service"]
                            for service in soup.select(Category.Element)
                        ]
                    )
                    serviceids = flattenlist(serviceids)
                    assert all(attribute.match(serviceid) for serviceid in serviceids)
                loadmore = all(loadmoreelement)
            request.config.categories[category] = dict.fromkeys(serviceids, "")


@allure.title("Find Targets per Service")
@pytest.mark.asyncio
async def test_getLinksTargetsAsync(request):
    async with aiohttp.ClientSession() as session:
        for category, _ in request.config.categories.items():
            serviceandtargetids = []
            n = 100
            urls = [
                {
                    key: (
                        value
                        if key != "url"
                        else {
                            k: v if k != "query" else [{"key": "id", "value": service}]
                            for k, v in value.items()
                        }
                    )
                    for key, value in Service.PageUrl.items()
                }
                for service in request.config.categories[category].keys()
            ]
            for i in range(0, len(urls), n):
                tasks = [(fetch_url(session, url)) for url in urls[i : i + n]]
                responses = asyncio.gather(*tasks)
                await responses
                for searchresponse in responses.result():
                    assert searchresponse[1] == 200
                    soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                    attribute = re.compile(Service.Regex)
                    serviceid = [
                        servicetarget.attrs["data-serviceid"]
                        for servicetarget in soup.select(Service.Element)
                    ]
                    assert len(set(serviceid)) == 1
                    serviceid = serviceid[0]
                    targetids = [
                        servicetarget.attrs["data-targetid"]
                        for servicetarget in soup.select(Service.Element)
                    ]
                    assert all(attribute.match(targetid) for targetid in targetids)
                    sections = [
                        category for category in soup.select(Service.CategoryElement)
                    ]
                    sectionnames = [
                        [
                            sectionname.text
                            for sectionname in section.select(Service.CategoryName)
                        ]
                        for section in sections
                    ]
                    assert (
                        all(
                            [len(set(sectionname)) == 1 for sectionname in sectionnames]
                        )
                        and len(sectionnames) > 0
                    )
                    targetids = [
                        [
                            servicetarget.attrs["data-targetid"]
                            for servicetarget in section.select(Service.Element)
                        ]
                        for section in sections
                    ]
                    serviceandtargetids.append(
                        {
                            serviceid: [
                                {
                                    [
                                        sectionname.text
                                        for sectionname in section.select(
                                            Service.CategoryName
                                        )
                                    ][0]: [
                                        {servicetarget.attrs["data-targetid"]: {}}
                                        for servicetarget in section.select(
                                            Service.Element
                                        )
                                    ]
                                }
                                for section in sections
                            ]
                        }
                    )
            request.config.categories[category] = serviceandtargetids


@allure.title("Find Details per Target")
@pytest.mark.asyncio
async def test_getDetailsTargetsAsync(request, allure_subtests):
    async with aiohttp.ClientSession() as session:
        for ConfigUrl in [
            Authorization.ListMethods,
            Authorization.TokenEnabledUrl,
            Authorization.RestTokenUrl,
            Authorization.TokenUrl,
        ]:
            UrlPart = ConfigUrl.pop("url")
            ajaxresponse = await session.request(**ConfigUrl, url=buildurl(**UrlPart))
            ajaxresponsetext, ajaxresponsecode = (
                await ajaxresponse.text(),
                ajaxresponse.status,
            )
            ConfigUrl["url"] = UrlPart
            assert ajaxresponsecode == 200
            if is_json(ajaxresponsetext):
                jsonres = json.loads(ajaxresponsetext)
                if "result" in jsonres and isinstance(jsonres["result"], str):
                    CSRFpattern = re.compile("\w{32}")
                    if CSRFpattern.match(jsonres["result"]):
                        ConfigUrl["headers"]["X-CSRF-Token"] = jsonres["result"]
                        Authorization.authdata["_t"] = jsonres["result"]
                        Authorization.AuthUrl["url"]["query"][0]["value"] = jsonres[
                            "result"
                        ]
        with aiohttp.MultipartWriter("form-data") as mp:
            for key, value in Authorization.authdata.items():
                part = mp.append(value)
                part.set_content_disposition("form-data", name=key)
            UrlPart = Authorization.AuthUrl.pop("url")
            authresponse = await session.request(
                **Authorization.AuthUrl, url=buildurl(**UrlPart)
            )
            authresponsetext = await authresponse.text()
            Authorization.AuthUrl["url"] = UrlPart
            soup = bs4.BeautifulSoup(authresponsetext, "lxml")
            testauth = soup.select(Authorization.Element)
            assert len(
                set(testauth)
            ) == 1 and Authorization.Regex in urllib.parse.unquote(testauth[0].text)
        for category, _ in request.config.categories.items():
            urls = []
            n = 50
            for service in request.config.categories[category]:
                for servicevariants in service.values():
                    for servicevariant in servicevariants:
                        for servicetargets in servicevariant.values():
                            for servicetarget in servicetargets:
                                [
                                    (
                                        config["url"]["query"].clear(),
                                        config["url"]["query"].extend(
                                            [
                                                {
                                                    "key": "id",
                                                    "value": list(servicetarget.keys())[
                                                        0
                                                    ],
                                                },
                                                {
                                                    "key": "serviceId",
                                                    "value": list(service.keys())[0],
                                                },
                                            ]
                                        ),
                                    )
                                    for config in [
                                        Target.DetailsPageUrl,
                                        Target.MainPageUrl,
                                    ]
                                ]
                                urls.extend(
                                    [
                                        (
                                            copy.deepcopy(Target.MainPageUrl),
                                            servicetarget,
                                        ),
                                        (
                                            copy.deepcopy(Target.DetailsPageUrl),
                                            servicetarget,
                                        ),
                                    ]
                                )

            for i in range(0, len(urls), n):
                # Requestsstart_time = time.time()
                tasks = [
                    (fetch_url(session, url[0], url[1])) for url in urls[i : i + n]
                ]
                responses = asyncio.gather(*tasks)
                await responses
                # Requestend_time = time.time()
                for searchresponse in responses.result():
                    with allure_subtests.test(subtest_name=f"custom message:{i=}"):
                        asserts = []
                        details = {}
                        soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                        tree = lxml.etree.HTML(searchresponse[0])
                        assert searchresponse[1] == 200
                        if "targets.htm" in searchresponse[2]["path"]:
                            servtypes = soup.select(Target.serviceType["elem"])
                            if len(servtypes) > 1 and set(
                                [stype.text for stype in servtypes]
                            ) == set(
                                [
                                    Target.serviceType["electronic"],
                                    Target.serviceType["nonelectronic"],
                                ]
                            ):
                                elements = Target.OnMainPageElements
                            elif len(servtypes) > 0 and set(
                                [stype.text for stype in servtypes]
                            ) == set([Target.serviceType["nonelectronic"]]):
                                elements = Target.OffMainPageElements
                            else:
                                elements = []
                        elif "details.htm" in searchresponse[2]["path"]:
                            elements = Target.DetailsPageConfigElements
                        else:
                            elements = []
                        if len(elements) > 0:
                            for csselement in elements["css"]:
                                details[csselement["name"]] = [
                                    (
                                        cssel.text
                                        if csselement["value"] == "text"
                                        else cssel.attrs[csselement["value"]]
                                    )
                                    for cssel in soup.select(csselement["elem"])
                                ]

                                asserts.append(len(details[csselement["name"]]) != 0)
                            for xpathelement in elements["xpath"]:
                                details[xpathelement["name"]] = [
                                    (
                                        xpathel.text
                                        if xpathelement["value"] == "text"
                                        else xpathel.attrib[xpathelement["value"]]
                                    )
                                    for xpathel in tree.xpath(xpathelement["elem"])
                                ]
                                asserts.append(len(details[xpathelement["name"]]) != 0)
                        details["assert"] = (
                            details["assert"] and all(asserts)
                            if "assert" in details
                            else all(asserts)
                        )
                        searchresponse[3][
                            searchresponse[2]["query"][0]["value"]
                        ].update(details)
                        assert all(asserts), f'На странице {buildurl(**searchresponse[2])} не соответствуют пункты: {*[detail for detail in details if details[detail]==[]],}'
                # print(f"Responses search time --- {time.time() - Requestend_time} seconds --- Requests time --- {Requestend_time - Requestsstart_time} seconds ---")


def test_dump_found(request):
    with open("results/data.json", "w") as f:
        allure.attach(json.dumps(request.config.categories).encode(),name='All details collection',attachment_type='application/json')
        json.dump(request.config.categories, f)
