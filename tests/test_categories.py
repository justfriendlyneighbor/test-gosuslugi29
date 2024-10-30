import allure, pytest, bs4, re, aiohttp, pytest_aiohttp
import config.CategoriesConfig as Categories, utils.utils as utils
from allure_commons.types import Severity


@pytest.fixture(scope="session")
async def categories_pages(request):
    pages = []
    async with aiohttp.ClientSession() as session:
        pages = await utils.get_service_pages(session, Categories.CategoriesServiceMethods)
    return pages


@allure.severity(Severity.BLOCKER)
@allure.title("Тест доступности Категорий")
@allure.description("Этот тест проверяет доступность страницы категорий")
def test_categories_pages(request, categories_pages, check):
    ok = 200
    for page in categories_pages:
        with check:
            with allure.step(f"Проверить Запрос к странице {page['url']}"):
                assert (
                    page["status"] == ok
                ), f'Запрос к странице категорий вернул код отличный от {ok}, а именно {page["status"]}'
                request.config.categoriespages.append(page)
    pytest.skip("Completed succesfully, skipping from report")


def get_all_categories(pages):
    for categorypage in pages:
        if "search" in categorypage["url"]:
            soup = bs4.BeautifulSoup(categorypage["text"], "lxml")
            categories = soup.select(Categories.Element)
            categoryids = {
                category.attrs[Categories.Attribute]: {
                    "name": " ".join(
                        [span.text for span in category.select(Categories.NameElement)]
                    )
                }
                for category in categories
            }
            return categoryids


@pytest.fixture
def categories(request):
    with allure.step(f"Получить список всех категорий"):
        return get_all_categories(request.config.categoriespages)


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
                assert re.compile(Categories.Regex).match(
                    category
                ), f'Категория {category} ({name["name"]}) не соответствует стандартному представлению'
    request.config.categories = categories
    pytest.skip("Completed succesfully, skipping from report")
