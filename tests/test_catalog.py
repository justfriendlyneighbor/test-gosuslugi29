import allure, pytest, bs4, re, aiohttp, pytest_aiohttp
import config.CatalogConfig as Catalog
from utils.utils import *
from allure_commons.types import Severity


@pytest.fixture
async def catalog_pages(request):
    async with aiohttp.ClientSession() as session:
        catalogpages = []
        for category in [Catalog.PageUrl, Catalog.SearchUrl]:
            UrlPart = category.pop("url")
            with allure.step(f"Открыть страницу категорий {buildurl(**UrlPart)}"):
                response = await session.request(**category, url=buildurl(**UrlPart))
                category["url"] = UrlPart
                responsetext = await response.text()
                catalogpages.append(
                    {
                        "status": response.status,
                        "text": responsetext,
                        "url": buildurl(**UrlPart),
                    }
                )
        return catalogpages


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Категорий")
@allure.description("Этот тест проверяет доступность страницы категорий")
def test_catalog_pages(request, catalog_pages, check):
    ok = 200
    for page in catalog_pages:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                assert (
                    page["status"] == ok
                ), f'Запрос к странице категорий вернул код отличный от {ok}, а именно {page["status"]}'
                request.config.catalogpages.append(page)
    pytest.skip("Completed succesfully, skipping from report")


def get_all_categories(pages):
    for catalogpage in pages:
        if "search" in catalogpage["url"]:
            soup = bs4.BeautifulSoup(catalogpage["text"], "lxml")
            categories = soup.select(Catalog.Element)
            categoryids = {
                category.attrs[Catalog.Attribute]: {
                    "name": " ".join(
                        [
                            span.text
                            for span in category.select('h2>span>span[class="js-word"]')
                        ]
                    )
                }
                for category in categories
            }
            return categoryids


@pytest.fixture
def categories(request):
    with allure.step(f"Получить список всех категорий"):
        return get_all_categories(request.config.catalogpages)


@allure.severity(Severity.BLOCKER)
@allure.title("Тест наличия Категорий")
@allure.description("Этот тест проверяет наличие на странице категорий объектов")
def test_categories(categories):
    with allure.step(f"Количество категорий {len(categories)}"):
        assert (
            len(categories) > 0
        ), f"Количество категорий найденных на странице категорий {len(categories)}"
    pytest.skip("Completed succesfully, skipping from report")


@allure.severity(Severity.BLOCKER)
@allure.title("Тест Категорий")
@allure.description(
    "Этот тест проверяет объекты категорий на стандартное представление"
)
def test_category(request, categories, check):
    for category, name in categories.items():
        with check:
            with allure.step(f"Проверить категорию {category} ({name['name']})"):
                assert re.compile(Catalog.Regex).match(
                    category
                ), f'Категория {category} ({name["name"]}) не соответствует стандартному представлению'
    request.config.categories = categories
    pytest.skip("Completed succesfully, skipping from report")
