import allure, pytest, bs4, re, json, asyncio, aiohttp, functools, pytest_aiohttp, functools, itertools
import config.CategoryConfig as Category, utils.utils as utils
from allure_commons.types import Severity

@pytest.fixture(scope="session")
async def category_pages(request):
    pages = {"ajax": [], "category": []}
    async with aiohttp.ClientSession() as session:
        pages["ajax"] = await utils.get_service_pages(
            session, utils.RestServiceMethods
        )
        utils.update_services(pages["ajax"], utils.Headers)
        pages["category"] = await utils.get_pubblockurl_pages(
            session,
            request.config.categories,
            {
                "f": "",
                "g": "tiles",
                "isTemplate": "24326@egClassification",
                "id": "",
                "category": "",
                "name": "category",
                "link": "pgu/categories/info/showmore"
            },
        )
    return pages


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности вспомогательных страниц для Категорий")
@allure.description(
    "Этот тест проверяет доступность страницы вспомогательных страниц для доступа к категориям"
)
def test_category_service_pages(request, category_pages, check):
    ok = 200
    for page in category_pages["ajax"]:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                assert (
                    page["status"] == ok
                ), f'Запрос {page["url"]} для получения доступа к странице категории вернул код отличный от {ok}, а именно {page["status"]}'
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест получения токена для Категорий")
@allure.description("Этот тест проверяет получение токена для доступа к категориям")
def test_category_services():
    with allure.step(f"Проверить CSRF-токен {utils.Headers['X-CSRF-Token']}"):
        assert (
            utils.Headers["X-CSRF-Token"] != "Fetch"
        ), f"Не удалось получить CSRF-токен, список заголовков - {utils.Headers}"
    utils.Headers["X-CSRF-Token"] = "Fetch"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Услуг по Категории")
@allure.description("Этот тест проверяет доступность страниц категорий")
def test_category_pages(request, category_pages, check):
    ok = 200
    for page in category_pages["category"]:
        with check:
            with allure.step(f'Проверить Запрос к странице {utils.buildurl(**page["url"])}'):
                assert (
                    page["status"] == ok
                ), f'Запрос к поиску по странице категории {utils.buildurl(**page["url"])} вернул код отличный от {ok}, а именно {page["status"]}'
                request.config.categorypages.append(page)
    pytest.skip("Completed succesfully, skipping from report")


def get_serviceids(pages):
    serviceids = {}
    for categorypage in pages:
        with allure.step(
            f"Выделить услуги на странице {utils.buildurl(**categorypage['url'])}"
        ):
            if utils.is_json(categorypage["text"]):
                soup = bs4.BeautifulSoup(
                    json.loads(categorypage["text"])["result"], "lxml"
                )
            else:
                soup = bs4.BeautifulSoup(categorypage["text"], "lxml")
            serviceattrs = {
                service.attrs[Category.Attribute]: {
                    "name": " ".join(
                        [title.text for title in service.select(Category.ElementName)]
                    )
                }
                for service in soup.select(Category.Element)
            }
            if serviceids.get(categorypage["lst"]) == None:
                serviceids[categorypage["lst"]] = serviceattrs
            else:
                serviceids[categorypage["lst"]].update(serviceattrs)
    with allure.step(f"Отфильтровать услуги"):
        unique = functools.reduce(
            set.union,
            (
                itertools.starmap(
                    set.symmetric_difference,
                    itertools.combinations(map(set, serviceids.values()), 2),
                )
            ),
        )
        [
            [
                unique.remove(service) if service in unique else services.pop(service)
                for service in list(services)
            ]
            for services in serviceids.values()
        ]
    return serviceids


@pytest.fixture
def allserviceids(request):
    return utils.get_ids(request.config.categorypages,Category)


@allure.severity(Severity.BLOCKER)
@allure.title("Тест Услуг по Категории")
@allure.description("Этот тест проверяет объекты услуг на стандартное представление")
def test_service(request, allserviceids, check):
    attribute = re.compile(Category.Regex)
    for categoryid, serviceids in allserviceids.items():
        for serviceid, nameinfo in serviceids.items():
            with check:
                with allure.step(f"Проверить услугу {serviceid} ({nameinfo['name']})"):
                    assert attribute.match(
                        serviceid
                    ), f'Услуга {serviceid} ({nameinfo["name"]}) не соответствует стандартному представлению'
        request.config.services.update(serviceids)
        request.config.categories[categoryid].update(serviceids)
    pytest.skip("Completed succesfully, skipping from report")
