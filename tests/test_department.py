import allure, pytest, bs4, re, json, asyncio, aiohttp, pytest_aiohttp
import config.DepartmentConfig as Department, utils.utils as utils
from allure_commons.types import Severity

@pytest.fixture(scope="session")
async def department_pages(request):
    pages = {"ajax": [], "department": []}
    async with aiohttp.ClientSession() as session:
        pages["ajax"] = await utils.get_service_pages(
            session, utils.RestServiceMethods
        )
        utils.update_services(pages["ajax"], utils.Headers)
        pages["department"] = await utils.get_pubblockurl_pages(
            session,
            request.config.departments,
            {
                "f": "",
                "department": "",
                "g": "department",
                "id": "",
                "name": "department",
                "link": "pgu/department/services/showmore",
            },
        )
    return pages


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности вспомогательных страниц для Органов")
@allure.description(
    "Этот тест проверяет доступность страницы вспомогательных страниц для доступа к органам"
)
def test_department_service_pages(department_pages, check):
    ok = 200
    for page in department_pages["ajax"]:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                assert (
                    page["status"] == ok
                ), f'Запрос {page["url"]} для получения доступа к странице категории вернул код отличный от {ok}, а именно {page["status"]}'
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест получения токена для Органа")
@allure.description("Этот тест проверяет получение токена для доступа к органов")
def test_department_services():
    with allure.step(f"Проверить CSRF-токен {utils.Headers['X-CSRF-Token']}"):
        assert (
            utils.Headers["X-CSRF-Token"] != "Fetch"
        ), f"Не удалось получить CSRF-токен, список заголовков - {utils.Headers}"
    utils.Headers["X-CSRF-Token"] = "Fetch"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Услуг по Органу")
@allure.description("Этот тест проверяет доступность страниц органов")
def test_department_pages(request, department_pages, check):
    ok = 200
    for page in department_pages["department"]:
        with check:
            with allure.step(f'Проверить Запрос к странице {utils.buildurl(**page["url"])}'):
                assert (
                    page["status"] == ok
                ), f'Запрос к поиску по странице категории {utils.buildurl(**page["url"])} вернул код отличный от {ok}, а именно {page["status"]}'
                request.config.departmentpages.append(page)
    pytest.skip("Completed succesfully, skipping from report")


def get_departmentids(pages):
    serviceids = {}
    for departmentpage in pages:
        with allure.step(
            f"Выделить услуги на странице {utils.buildurl(**departmentpage['url'])}"
        ):
            if utils.is_json(departmentpage["text"]):
                soup = bs4.BeautifulSoup(
                    json.loads(departmentpage["text"])["result"], "lxml"
                )
            else:
                soup = bs4.BeautifulSoup(departmentpage["text"], "lxml")
            serviceattrs = {
                service.attrs[Department.Attribute]: {
                    "name": " ".join(
                        [
                            title.text
                            for title in service.select(Department.ElementName)
                        ]
                    )
                }
                for service in soup.select(Department.Element)
            }
            if serviceids.get(departmentpage["lst"]) == None:
                serviceids[departmentpage["lst"]] = serviceattrs
            else:
                serviceids[departmentpage["lst"]].update(serviceattrs)
    return serviceids


@pytest.fixture
def alldepartmentids(request):
    return utils.get_ids(request.config.departmentpages,Department)


@allure.severity(Severity.BLOCKER)
@allure.title("Тест Услуг по Органу")
@allure.description("Этот тест проверяет объекты услуг на стандартное представление")
def test_service(request, alldepartmentids, check):
    attribute = re.compile(Department.Regex)
    for departmentid, serviceids in alldepartmentids.items():
        for serviceid, nameinfo in serviceids.items():
            with check:
                with allure.step(f"Проверить услугу {serviceid} ({nameinfo['name']})"):
                    assert attribute.match(
                        serviceid
                    ), f'Услуга {serviceid} ({nameinfo["name"]}) не соответствует стандартному представлению'
        request.config.departments[departmentid].update(
            {
                key: value
                for key, value in request.config.services.items()
                if key in serviceids
            }
        )
    pytest.skip("Completed succesfully, skipping from report")
