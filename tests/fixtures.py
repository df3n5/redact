import pytest

from redact.db import get_redis_conn
from redact.model import BaseModel
from redact.model import KeyValueField
from redact.model import model_save


class TestModel(BaseModel):
    def __init__(self, key, test_str_value_1=None, test_str_value_2=None, test_str_value_3=None):
        super(TestModel, self).__init__(key)
        self.test_str_1 = KeyValueField('t1', test_str_value_1)
        self.test_str_2 = KeyValueField('t2', test_str_value_2)
        self.test_str_3 = KeyValueField('t3', test_str_value_3)


class TestMigratedModel(BaseModel):
    def __init__(self, key, test_str_value_1=None, test_str_value_2=None, test_str_value_3=None, test_extra_value_1=None, test_extra_value_2=None):
        super(TestMigratedModel, self).__init__(key)
        self.test_str_1 = KeyValueField('t1', test_str_value_1)
        self.test_str_2 = KeyValueField('t2', test_str_value_2)
        self.test_str_3 = KeyValueField('t3', test_str_value_3)
        self.test_extra_value_1 = KeyValueField('e1', test_extra_value_1)
        self.test_extra_value_2 = KeyValueField('e2', test_extra_value_2)

    def get_migrations(self):
        def migration_1(base_model):
            base_model.test_extra_value_1.value = "TEST_MIGRATION_VALUE_1"

        def migration_2(base_model):
            base_model.test_extra_value_2.value = "TEST_MIGRATION_VALUE_2"
        return [migration_1, migration_2]


### Test fixtures
@pytest.fixture
def model(request):
    model = TestModel('test_model_1', 'a', 'b', 'c')

    def fin():
        get_redis_conn().delete(model.key)
    request.addfinalizer(fin)
    return model


@pytest.fixture
def saved_model(request):
    model = TestModel('test_model_1', 'a', 'b', 'c')
    model_save(model)

    def fin():
        get_redis_conn().delete(model.key)
    request.addfinalizer(fin)
    return model
