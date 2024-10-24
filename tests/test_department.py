import allure, pytest, bs4, re, json, asyncio, aiohttp, copy, functools, pytest_aiohttp, functools, itertools
import config.DepartmentConfig as Department
from utils.utils import *
from allure_commons.types import Severity

async def get_department_service_pages(session):
    ajaxpages = []
    for ConfigUrl in Department.DepartmentServiceMethods:
        UrlPart = ConfigUrl.pop("url")
        with allure.step(f"Асинхронно сделать запрос к вспомогательной странице {buildurl(**UrlPart)}"):
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

def update_department_services(pages):
    CSRFpattern = re.compile(r"\w{32}")
    for departmentpage in pages:
        with allure.step(f"Найти CSRF-токен {departmentpage['url']}"):
            if is_json(departmentpage["text"]):
                jsonres = json.loads(departmentpage["text"])
                if "result" in jsonres and isinstance(jsonres["result"], str):
                    if CSRFpattern.match(jsonres["result"]):
                        Department.Headers["X-CSRF-Token"] = jsonres["result"]


async def get_department_pages(session, departments):
    departmentpages = []
    for department, _ in departments.items():
        loadmore = True
        loadmoreelement = []
        f = 1
        with allure.step(f"Асинхронно сделать запрос к странице категории {department}"):
            while loadmore:
                copys = []
                for _ in range(2):
                    Department.PubBlockUrl["data"] = json.loads(
                        Department.PubBlockUrl["data"]
                    )
                    Department.PubBlockUrl["data"]["params"][2]["map"] = {
                        "f": f,
                        "department": department,
                        "g": "department",
                        "id": department,
                    }
                    Department.PubBlockUrl["data"] = json.dumps(
                        Department.PubBlockUrl["data"]
                    )
                    copys.append(copy.deepcopy(Department.PubBlockUrl))
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
                                "department": department,
                            }
                        )
                        soup = bs4.BeautifulSoup(searchresponse[0], "lxml")
                        loadmoreelement.append(
                            len(soup.select(Department.LoadMoreElement)) != 0
                        )
                    except Exception as e:
                        print(e.message)
                loadmore = all(loadmoreelement)
    return departmentpages


@pytest.fixture(scope="session")
async def department_pages(request):
    pages = {"ajax": [], "department": []}
    async with aiohttp.ClientSession() as session:
        pages["ajax"] = await get_department_service_pages(session)
        request.config.departmentservicepages.extend(pages["ajax"])
        update_department_services(request.config.departmentservicepages)
        pages["department"] = await get_department_pages(session, request.config.departments)
    return pages


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности вспомогательных страниц для Категорий")
@allure.description(
    "Этот тест проверяет доступность страницы вспомогательных страниц для доступа к категориям"
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
@allure.title("Тест получения токена для Категорий")
@allure.description("Этот тест проверяет получение токена для доступа к категориям")
def test_department_services():
    with allure.step(f"Проверить CSRF-токен {Department.Headers['X-CSRF-Token']}"):
        assert (
            Department.Headers["X-CSRF-Token"] != "Fetch"
        ), f"Не удалось получить CSRF-токен, список заголовков - {Department.Headers}"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Услуг по Категории")
@allure.description("Этот тест проверяет доступность страниц категорий")
def test_department_pages(request, department_pages, check):
    ok = 200
    for page in department_pages["department"]:
        with check:
            with allure.step(f'Проверить Запрос к странице {buildurl(**page["url"])}'):
                assert (
                    page["status"] == ok
                ), f'Запрос к поиску по странице категории {buildurl(**page["url"])} вернул код отличный от {ok}, а именно {page["status"]}'
                request.config.departmentpages.append(page)
    pytest.skip("Completed succesfully, skipping from report")


def get_departmentids(pages):
    serviceids = {}
    for departmentpage in pages:
        with allure.step(
            f"Выделить услуги на странице категорий {buildurl(**departmentpage['url'])}"
        ):
            if is_json(departmentpage["text"]):
                soup = bs4.BeautifulSoup(
                    json.loads(departmentpage["text"])["result"], "lxml"
                )
            else:
                soup = bs4.BeautifulSoup(departmentpage["text"], "lxml")
            if serviceids.get(departmentpage["department"]) == None:
                serviceids[departmentpage["department"]] = {
                    service.attrs["data-pgu-service"]: {
                        "name": " ".join(
                            [
                                title.text
                                for title in service.select('span[class="js-word"]')
                            ]
                        )
                    }
                    for service in soup.select(Department.Element)
                }
            else:
                serviceids[departmentpage["department"]].update(
                    {
                        service.attrs["data-pgu-service"]: {
                            "name": " ".join(
                                [
                                    title.text
                                    for title in service.select('span[class="js-word"]')
                                ]
                            )
                        }
                        for service in soup.select(Department.Element)
                    }
                )
    return serviceids

@pytest.fixture
def alldepartmentids(request):
    return get_departmentids(request.config.departmentpages)

@allure.severity(Severity.BLOCKER)
@allure.title("Тест Услуг по Категории")
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
        request.config.departments[departmentid].update({key:value for key,value in request.config.services.items() if key in serviceids})
    pytest.skip("Completed succesfully, skipping from report")