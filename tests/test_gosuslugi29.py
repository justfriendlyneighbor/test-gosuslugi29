import allure, pytest, bs4, lxml, re, json, asyncio, aiohttp, copy, time, urllib, allure_subtests
import config.CatalogConfig as Catalog, config.CategoryConfig as Category, config.ServiceConfig as Service, config.TargetConfig as Target, config.AuthorizationConfig as Authorization
from utils.utils import *
from allure_commons.types import Severity


@allure.severity(Severity.BLOCKER)
@allure.title("Тест Категорий")
@allure.description("Этот тест собирает список категорий услуг на сайте, проверяя доступность страницы категорий и наличия на странице категорий объектов")
@pytest.mark.asyncio
async def test_getLinksCategoriesAsync(request):
    async with aiohttp.ClientSession() as session:
        UrlPart = Catalog.PageUrl.pop("url")
        with allure.step(f"Открыть страницу категорий {buildurl(**UrlPart)}"):
            pageresponse = await session.request(**Catalog.PageUrl, url=buildurl(**UrlPart))
            Catalog.PageUrl["url"] = UrlPart
            assert pageresponse.status == 200, f'Запрос к странице категорий вернул код отличный от 200, а именно {pageresponse.status}'
        UrlPart = Catalog.SearchUrl.pop("url")
        with allure.step(f"Получить полную страницу категорий {buildurl(**UrlPart)}"):
            searchresponse = await session.request(
                **Catalog.SearchUrl, url=buildurl(**UrlPart)
            )
            searchresponsetext, searchresponsestatus = (
                await searchresponse.text(),
                searchresponse.status,
            )
            Catalog.SearchUrl["url"] = UrlPart
            assert pageresponse.status == 200 and searchresponsestatus == 200, f'Запрос к поиску по странице категорий вернул код отличный от 200, а именно {searchresponsestatus}'
        with allure.step("Найти все категории на странице"):
            soup = bs4.BeautifulSoup(searchresponsetext, "lxml")
            categories = soup.select(Catalog.Element)
            attribute = re.compile(Catalog.Regex)
            categoryids = [category.attrs["data-objid"] for category in categories]
            assert len(categories) > 0, f'Количество категорий найденных на странице {len(categories)}'
            assert all(attribute.match(categoryid) for categoryid in categoryids), f'Не все категории на странице соответствуют стандартному представлению, а именно {[categoryid for categoryid in categoryids if attribute.match(categoryid)==None]}'
            request.config.categories = dict.fromkeys(categoryids, "")

@allure.severity(Severity.BLOCKER)
@allure.title("Тест поиска Услуг по Категории")
@allure.description("Этот тест собирает список услуг по категории на сайте, проверяя доступность страницы категории и наличия на странице категории услуг")
@pytest.mark.asyncio
async def test_getLinksServicesAsync(request):
    async with aiohttp.ClientSession() as session:
        for ConfigUrl in [
            Category.ListMethods,
            Category.TokenEnabledUrl,
            Category.RestTokenUrl,
        ]:
            UrlPart = ConfigUrl.pop("url")
            with allure.step(f"Сделать запрос к {buildurl(**UrlPart)}"):
                ajaxresponse = await session.request(**ConfigUrl, url=buildurl(**UrlPart))
                ajaxresponsetext, ajaxresponsecode = (
                    await ajaxresponse.text(),
                    ajaxresponse.status,
                )
                ConfigUrl["url"] = UrlPart
                assert ajaxresponsecode == 200, f'Запрос {ConfigUrl} для получения доступа к странице категории вернул код отличный от 200, а именно {ajaxresponsecode}' 
                if is_json(ajaxresponsetext):
                    jsonres = json.loads(ajaxresponsetext)
                    if "result" in jsonres and isinstance(jsonres["result"], str):
                        CSRFpattern = re.compile("\w{32}")
                        if CSRFpattern.match(jsonres["result"]):
                            ConfigUrl["headers"]["X-CSRF-Token"] = jsonres["result"]
        assert Category.Headers["X-CSRF-Token"] != "Fetch", f'Не удалось получить CSRF-токен, список заголовков - {Category.Headers}'
        for category, _ in request.config.categories.items():
            loadmore = True
            loadmoreelement = []
            f = 1
            serviceids = []
            with allure.step(f"Асинхронно сделать запросы к странице категории {category}"):
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
                        assert searchresponse[1] == 200, f'Запрос к поиску по странице категории вернул код отличный от 200, а именно {searchresponse[1]}'
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
                        assert all(attribute.match(serviceid) for serviceid in serviceids), f'Не все услуги на странице соответствуют стандартному представлению, а именно {[serviceid for serviceid in serviceids if attribute.match(serviceid)==None]}'
                    loadmore = all(loadmoreelement)
                request.config.categories[category] = dict.fromkeys(serviceids, "")

@allure.severity(Severity.BLOCKER)
@allure.title("Тест поиска Подуслуг по Услуге")
@allure.description("Этот тест собирает список подуслуг по услуге на сайте, проверяя доступность страницы услуги и наличия на странице услуги групп подуслуг и входящих в эти группы подуслуг")
@pytest.mark.asyncio
async def test_getLinksTargetsAsync(request):
    async with aiohttp.ClientSession() as session:
        for category, _ in request.config.categories.items():
            serviceandtargetids = []
            n = 100
            urls = [
                [{
                    key: (
                        value
                        if key != "url"
                        else {
                            k: v if k != "query" else [{"key": "id", "value": service}]
                            for k, v in value.items()
                        }
                    )
                    for key, value in Service.PageUrl.items()
                },False]
                for service in request.config.categories[category].keys()
            ]
            while not all([url[1] for url in urls]):
                for i in range(0, len(urls), n):
                    with allure.step(f"Асинхронно сделать запросы к страницам услуг {[[query['value'] for query in url[0]['url']['query']] for url in urls[i : i + n]]}"):
                        tasks = [(fetch_url(session, url[0],url)) for url in urls[i : i + n]]
                        responses = asyncio.gather(*tasks)
                        await responses
                        for searchresponse in responses.result():
                            try:
                                assert searchresponse[1] == 200, f'Запрос к поиску по странице услуги вернул код отличный от 200, а именно {searchresponse[1]}'
                            except AssertionError:
                                continue
                            soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                            attribute = re.compile(Service.Regex)
                            serviceid = [
                                servicetarget.attrs["data-serviceid"]
                                for servicetarget in soup.select(Service.Element)
                            ]
                            try:
                                assert len(set(serviceid)) == 1, f'Не все подуслуги на странице имеют одинаковый код услуги, а именно { {servicetarget: servicetarget.attrs["data-serviceid"] for servicetarget in soup.select(Service.Element)} }'
                            except AssertionError:
                                continue
                            serviceid = serviceid[0]
                            targetids = [
                                servicetarget.attrs["data-targetid"]
                                for servicetarget in soup.select(Service.Element)
                            ]
                            assert all(attribute.match(targetid) for targetid in targetids), f'Не все подуслуги на странице соответствуют стандартному представлению, а именно {[targetid for targetid in targetids if attribute.match(targetid)==None]}'
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
                            assert len(sectionnames) > 0 , f'Количество групп (электронные / неэлектронные) найденных на странице подуслуги {len(sectionnames)}'
                            assert (
                                all(
                                    [len(set(sectionname)) == 1 for sectionname in sectionnames]
                                ) 
                            ), f'У группы подуслуг (электронные / неэлектронные) обнаружено несколько названий, а именно {sectionnames}'
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
                            searchresponse[3][1]=True
                urls = list(filter(lambda x: not x[1], urls))
            request.config.categories[category] = serviceandtargetids

@allure.severity(Severity.NORMAL)
@allure.title("Тест поиска проверяемых Параметров по Подуслуге")
@allure.description("Этот тест авторизуется на сайте, собирает список проверяемых параметров по подуслуге на сайте, проверяя доступность страницы подуслуги и наличия на странице подуслуги проверяемых параметров")
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
            with allure.step(f"Сделать запрос к {buildurl(**UrlPart)} для подготовки к авторизации"):
                ajaxresponse = await session.request(**ConfigUrl, url=buildurl(**UrlPart))
                ajaxresponsetext, ajaxresponsecode = (
                    await ajaxresponse.text(),
                    ajaxresponse.status,
                )
                ConfigUrl["url"] = UrlPart
                assert ajaxresponsecode == 200, f'Запрос {ConfigUrl} для получения доступа к странице авторизации вернул код отличный от 200, а именно {ajaxresponsecode}' 
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
            with allure.step(f"Сделать запрос к {buildurl(**UrlPart)} для авторизации"):
                authresponse = await session.request(
                    **Authorization.AuthUrl, url=buildurl(**UrlPart)
                )
                authresponsetext = await authresponse.text()
                Authorization.AuthUrl["url"] = UrlPart
                soup = bs4.BeautifulSoup(authresponsetext, "lxml")
                testauth = soup.select(Authorization.Element)
                assert len(set(testauth)) == 1, f'Количество записей об успешной авторизации найденных на странице не 1, а {len(set(testauth))}'
                assert Authorization.Regex in urllib.parse.unquote(testauth[0].text), f'Запись об успешной авторизации найденных на странице не 1, а {len(set(testauth))}'
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
                with allure.step(f"Асинхронно сделать запросы к страницам подуслуг {[[query['value'] for query in url[0]['url']['query']] for url in urls[i : i + n]]}"):
                    tasks = [
                        (fetch_url(session, url[0], url[1])) for url in urls[i : i + n]
                    ]
                    responses = asyncio.gather(*tasks)
                    await responses
                    # Requestend_time = time.time()
                    for searchresponse in responses.result():
                        with allure_subtests.test(subtest_name=f"Проверить параметры подуслуги {buildurl(**searchresponse[2])}"):
                            asserts = []
                            details = {}
                            soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                            tree = lxml.etree.HTML(searchresponse[0])
                            assert searchresponse[1] == 200, f'Запрос к поиску по странице подуслуги {buildurl(**searchresponse[2])} вернул код отличный от 200, а именно {searchresponse[1]}'
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
    with allure.step(f"Прикрепить файл результатов пройденных и непройденных проверок"):
        with open("results/data.json", "w") as f:
            allure.attach(json.dumps(request.config.categories).encode(),name='All details collection',attachment_type='application/json')
            json.dump(request.config.categories, f)
