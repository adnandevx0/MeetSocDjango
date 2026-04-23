import pytest


@pytest.mark.django_db
def test_user_model_exists():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    assert User._meta.db_table == "users_user"
