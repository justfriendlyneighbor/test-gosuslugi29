import allure, pytest, bs4, re, asyncio, aiohttp, pytest_aiohttp
import config.ServiceConfig as Service
from utils.utils import *
from allure_commons.types import Severity


async def get_service_pages(session, categories):
    servicepages = {}
    for category, services in categories.items():
        thisservicepages = []
        n = 100
        urls = [
            [
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
                },
                False,
            ]
            for service in services
            if service != "name"
        ]
        while not all([url[1] for url in urls]):
            for i in range(0, len(urls), n):
                with allure.step(
                    f"Асинхронно сделать {n} запросов с {i} по {i+n} к страницам категории {category}"
                ):
                    tasks = [
                        (fetch_url(session, url[0], url)) for url in urls[i : i + n]
                    ]
                    responses = asyncio.gather(*tasks)
                    await responses
                    for searchresponse in responses.result():
                        try:
                            assert searchresponse[1] == 200
                            soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                            serviceid = [
                                servicetarget.attrs["data-serviceid"]
                                for servicetarget in soup.select(Service.Element)
                            ]
                            assert len(set(serviceid)) == 1
                            thisservicepages.append(
                                {
                                    "status": searchresponse[1],
                                    "soup": soup,
                                    "url": searchresponse[2],
                                    "service": searchresponse[3],
                                }
                            )
                        except AssertionError:
                            continue
                        searchresponse[3][1] = True
            urls = list(filter(lambda x: not x[1], urls))
        servicepages[category] = thisservicepages
    return servicepages


@pytest.fixture(scope="session")
async def service_pages(request):
    pages = {}
    async with aiohttp.ClientSession() as session:
        pages = await get_service_pages(session, request.config.categories)
    return pages


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Подуслуг по Услуге")
@allure.description("Этот тест проверяет доступность страниц услуг")
def test_service_pages(request, service_pages, check):
    ok = 200
    for category, pages in service_pages.items():
        for page in pages:
            with check:
                with allure.step(
                    f'Проверить Запрос к странице {buildurl(**page["url"])}'
                ):
                    assert (
                        page["status"] == ok
                    ), f'Запрос к поиску по странице категории {buildurl(**page["url"])} вернул код отличный от {ok}, а именно {page["status"]}'
                    if request.config.servicepages.get(category) == None:
                        request.config.servicepages[category] = [page]
                    else:
                        request.config.servicepages[category].append(page)
    pytest.skip("Completed succesfully, skipping from report")


def get_serviceitargetids(pages):
    categoryservices = {}
    for category, servicepages in pages.items():
        for servicepage in servicepages:
            with allure.step(
                f"Выделить подуслуги на странице услуги {buildurl(**servicepage['url'])}"
            ):
                soup = servicepage["soup"]
                sections = [
                    category for category in soup.select(Service.CategoryElement)
                ]
                sectarg = {"sections": []}
                for section in sections:
                    sectionnames = [
                        sectionname.text
                        for sectionname in section.select(Service.CategoryName)
                    ]
                    sectarg.update(
                        {
                            servicetarget.attrs["data-targetid"]: {
                                "name": " ".join(
                                    [
                                        namespan.text
                                        for namespan in servicetarget.select(
                                            Service.ElementName
                                        )
                                    ]
                                ),
                                "type":sectionnames[0]
                            }
                            for servicetarget in section.select(Service.Element)
                        }
                    )
                    sectarg["sections"].append(sectionnames)
                categoryservices.update(
                    {servicepage["url"]["query"][0]["value"]: sectarg}
                )
    return categoryservices


@pytest.fixture(scope="session")
def allserviceitargetids(request):
    return get_serviceitargetids(request.config.servicepages)


@allure.severity(Severity.BLOCKER)
@allure.title("Тест наличия групп Подуслуг по Услуге")
@allure.description("Этот тест проверяет наличие на страницах услуг групп подуслуг")
def test_service_section_names(allserviceitargetids, check):
    for serviceid, service in allserviceitargetids.items():
        with check:
            with allure.step(f"Проверить количество групп услуги {serviceid}"):
                assert (
                    len(service["sections"]) > 0
                ), f'Количество групп (электронные / неэлектронные) найденных на странице подуслуги {len(service["sections"])}'
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест групп Подуслуг по Услуге")
@allure.description("Этот тест проверяет группы подуслуг на стандартное представление")
def test_service_section_name(allserviceitargetids, check):
    for serviceid, service in allserviceitargetids.items():
        with check:
            with allure.step(f"Проверить группы услуги {serviceid}"):
                assert all(
                    [
                        len(set(sectionname)) == 1
                        for sectionname in service["sections"]
                    ]
                ), f'У группы подуслуг (электронные / неэлектронные) обнаружено несколько названий, а именно {service["sections"]}'
                service.pop("sections", None)
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест Подуслуг по Услуге")
@allure.description("Этот тест проверяет подуслуги на стандартное представление")
def test_service_target(request, allserviceitargetids, check):
    attribute = re.compile(Service.Regex)
    for serviceid, targets in allserviceitargetids.items():
        for targetid, targetname in targets.items():
            with check:
                with allure.step(
                    f"Проверить подуслугу {targetid} ({targetname['name']})"
                ):
                    assert attribute.match(
                        targetid
                    ), f'Подуслуга {targetid} ({targetname["name"]}) не соответствует стандартному представлению'
        request.config.servicetargets.update(targets)
        request.config.services[serviceid].update(targets)
    pytest.skip("Completed succesfully, skipping from report")
