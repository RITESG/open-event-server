import unittest

from flask_jwt_extended import create_access_token

from app.api.helpers.db import get_or_create, save_to_db
from app.api.helpers.errors import ForbiddenError
from app.api.helpers.permission_manager import (
    accessible_role_based_events,
    has_access,
    permission_manager,
)
from app.factories.event import EventFactoryBasic
from app.factories.user import UserFactory
from app.models.users_events_role import UsersEventsRoles
from tests.all.integration.setup_database import Setup
from tests.all.integration.utils import OpenEventTestCase


class TestPermissionManager(OpenEventTestCase):
    def setUp(self):
        self.app = Setup.create_app()
        with self.app.test_request_context():
            user = UserFactory()
            save_to_db(user)

            event = EventFactoryBasic()
            event.user_id = user.id
            save_to_db(event)

            # Authenticate User
            self.auth = {
                'Authorization': "JWT " + create_access_token(user.id, fresh=True)
            }

    def test_has_access(self):
        """Method to test whether user has access to different roles"""

        with self.app.test_request_context(headers=self.auth):
            self.assertTrue(has_access('is_admin'))
            self.assertFalse(has_access('is_super_admin'))
            self.assertTrue(has_access('is_organizer', event_id=1))

    def test_accessible_role_based_events(self):
        """Method to test accessible role of a user based on an event"""

        with self.app.test_request_context(headers=self.auth, method="POST"):
            response = accessible_role_based_events(
                lambda *a, **b: b.get('user_id'), (), {}, (), {}
            )
            assert response is not None

    def test_is_organizer(self):
        """Method to test whether a user is organizer of an event or not"""

        with self.app.test_request_context(headers=self.auth, method="POST"):
            uer, _ = get_or_create(UsersEventsRoles, user_id=1, event_id=1)
            uer.role_id = 1
            save_to_db(uer)
            self.assertTrue(has_access('is_organizer', event_id=1))

    def test_is_coorganizer(self):
        """Method to test whether a user is coorganizer of an event or not"""

        with self.app.test_request_context(headers=self.auth, method="POST"):
            uer, _ = get_or_create(UsersEventsRoles, user_id=1, event_id=1)
            uer.role_id = 2
            save_to_db(uer)
            self.assertTrue(has_access('is_coorganizer', event_id=1))

    def test_is_moderator(self):
        """Method to test whether a user is moderator of an event or not"""

        with self.app.test_request_context(headers=self.auth, method="POST"):
            uer, _ = get_or_create(UsersEventsRoles, user_id=1, event_id=1)
            uer.role_id = 4
            save_to_db(uer)
            self.assertTrue(has_access('is_moderator', event_id=1))

    def test_is_track_organizer(self):
        """Method to test whether a user is track organizer of an event or not"""

        with self.app.test_request_context(headers=self.auth, method="POST"):
            uer, _ = get_or_create(UsersEventsRoles, user_id=1, event_id=1)
            uer.role_id = 4
            save_to_db(uer)
            self.assertTrue(has_access('is_moderator', event_id=1))

    def test_is_registrar(self):
        """Method to test whether a user is registrar of an event or not"""

        with self.app.test_request_context(headers=self.auth, method="POST"):
            uer, _ = get_or_create(UsersEventsRoles, user_id=1, event_id=1)
            uer.role_id = 6
            save_to_db(uer)
            self.assertTrue(has_access('is_registrar', event_id=1))

    def test_permission_manager_attributes(self):
        """Method to test attributes of permission manager"""

        with self.app.test_request_context():
            kwargs = {'leave_if': lambda a: True}
            perm = permission_manager(lambda *a, **b: True, [], {}, 'is_admin', **kwargs)
            self.assertTrue(perm)

            kwargs = {'check': lambda a: False}
            with self.assertRaises(ForbiddenError):
                permission_manager(lambda *a, **b: False, [], {}, 'is_admin', **kwargs)


if __name__ == '__main__':
    unittest.main()
