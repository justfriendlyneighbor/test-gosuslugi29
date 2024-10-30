def pytest_configure(config):
    # test_categories.py
    config.categoriespages = []
    config.categories = {}
    # test_category.py
    config.categorypages = []
    # test_departments.py
    config.departmentspages = []
    config.departments = {}
    # test_department.py
    config.departmentpages = []
    # test_service.py
    config.servicepages = []
    config.services = {}
    # test_target.py
    config.servicetargets = {}
    config.servicetargetsretry = {}


def pytest_collection_modifyitems(items):
    indexafter = [
        items.index(item)
        for item in items
        if "test_departments" in item.module.__name__
    ][-1]
    moveindexes = [
        items.index(item) for item in items if "test_department" == item.module.__name__
    ]
    [
        items.insert(indexafter, items.pop(moveindexes[0]))
        for _ in range(len(moveindexes))
    ]
