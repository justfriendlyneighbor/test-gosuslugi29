import allure, pytest, re, aiohttp, pytest_aiohttp, json
import config.DepartmentsConfig as Departments, utils.utils as utils
from allure_commons.types import Severity


async def get_departments_pages(session):
    ConfigUrl = Departments.RegionalMunicipalOrgs
    UrlPart = ConfigUrl.pop("url")
    with allure.step(f"Асинхронно сделать запрос к странице {utils.buildurl(**UrlPart)}"):
        departmentsresponse = await session.request(
            **ConfigUrl, url=utils.buildurl(**UrlPart)
        )
        ConfigUrl["url"] = UrlPart
        departmentsresponsetext = await departmentsresponse.text()
    return [
        {
            "status": departmentsresponse.status,
            "text": departmentsresponsetext,
            "url": utils.buildurl(**UrlPart),
        }
    ]


@pytest.fixture(scope="session")
async def departments_pages(request):
    pages = {"ajax": [], "departments": []}
    async with aiohttp.ClientSession() as session:
        pages["ajax"] = await utils.get_service_pages(
            session, utils.RestServiceMethods
        )
        utils.update_services(pages["ajax"], utils.Headers)
        pages["departments"] = await get_departments_pages(session)
    return pages


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности вспомогательных страниц для Органов")
@allure.description(
    "Этот тест проверяет доступность страницы вспомогательных страниц для доступа к органам"
)
def test_departments_service_pages(departments_pages, check):
    ok = 200
    for page in departments_pages["ajax"]:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                assert (
                    page["status"] == ok
                ), f'Запрос {page["url"]} для получения доступа к странице органов вернул код отличный от {ok}, а именно {page["status"]}'
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест получения токена для Органов")
@allure.description("Этот тест проверяет получение токена для доступа к органам")
def test_departments_services():
    with allure.step(f"Проверить CSRF-токен {utils.Headers['X-CSRF-Token']}"):
        assert (
            utils.Headers["X-CSRF-Token"] != "Fetch"
        ), f"Не удалось получить CSRF-токен, список заголовков - {utils.Headers}"
    utils.Headers["X-CSRF-Token"] = "Fetch"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Услуг по Категории")
@allure.description("Этот тест проверяет доступность страниц категорий")
def test_departments_pages(request, departments_pages, check):
    ok = 200
    for page in departments_pages["departments"]:
        with check:
            with allure.step(f'Проверить Запрос к странице {page["url"]}'):
                assert (
                    page["status"] == ok
                ), f'Запрос к поиску по странице категории {page["url"]} вернул код отличный от {ok}, а именно {page["status"]}'
                request.config.departmentspages.append(page)
    pytest.skip("Completed succesfully, skipping from report")


def get_all_departments(pages):
    departmentids = {}
    for departmentpage in pages:
        with allure.step(f"Выделить органы на странице {departmentpage['url']}"):
            if utils.is_json(departmentpage["text"]):
                [
                    [
                        departmentids.setdefault(
                            departmentdict["id"], {"name": departmentdict["title"]}
                        )
                        for departmentdict in departmentlist
                    ]
                    for departmentlist in list(
                        utils.gen_dict_extract(
                            json.loads(departmentpage["text"])["result"], "list"
                        )
                    )
                ]
    return departmentids


@pytest.fixture
def departments(request):
    with allure.step(f"Получить список всех органов"):
        return get_all_departments(request.config.departmentspages)


@allure.severity(Severity.BLOCKER)
@allure.title("Тест наличия Органов")
@allure.description("Этот тест проверяет наличие на странице органов объектов")
def test_departments(departments):
    with allure.step(f"Количество органов {len(departments)}"):
        assert (
            len(departments) > 0
        ), f"Количество органов найденных на странице {len(departments)}"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест Органов")
@allure.description("Этот тест проверяет объекты органов на стандартное представление")
def test_department(request, departments, check):
    for department, name in departments.items():
        with check:
            with allure.step(f"Проверить орган {department} ({name['name']})"):
                assert re.compile(Departments.Regex).match(
                    department
                ), f'Орган {department} ({name["name"]}) не соответствует стандартному представлению'
    request.config.departments = departments
    pytest.skip("Completed succesfully, skipping from report")
