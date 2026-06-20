from django.test import SimpleTestCase

from apps.navigation import TIP_MAIN_NAV
from apps.permissions import TIPPermission, TIPRole, permissions_for_role


class RolePermissionsTests(SimpleTestCase):
    def test_viewer_cannot_manage_integrations(self):
        perms = permissions_for_role(TIPRole.VIEWER)
        self.assertIn(TIPPermission.INTEGRATIONS_VIEW, perms)
        self.assertNotIn(TIPPermission.INTEGRATIONS_MANAGE, perms)

    def test_manager_can_sync_and_generate_reports(self):
        perms = permissions_for_role(TIPRole.MANAGER)
        self.assertIn(TIPPermission.DATA_SOURCES_SYNC, perms)
        self.assertIn(TIPPermission.REPORTS_GENERATE, perms)
        self.assertNotIn(TIPPermission.AI_INSIGHTS_RUN, perms)

    def test_admin_has_all_permissions(self):
        perms = permissions_for_role(TIPRole.ADMIN)
        self.assertEqual(len(perms), len(TIPPermission))

    def test_unknown_role_defaults_to_viewer(self):
        perms = permissions_for_role("unknown")
        self.assertEqual(perms, permissions_for_role(TIPRole.VIEWER))


class NavigationTests(SimpleTestCase):
    def test_menu_order(self):
        labels = [item["label"] for item in TIP_MAIN_NAV]
        self.assertEqual(
            labels,
            ["Dashboard", "Integrações", "Relatórios", "Análises", "Configurações"],
        )

    def test_each_nav_item_has_permission(self):
        for item in TIP_MAIN_NAV:
            self.assertTrue(item["permission"])
            self.assertTrue(item["path"].startswith("/"))
