from __future__ import annotations

import re

from django.test import TestCase
from django.urls import reverse


class PwaIntegrationTests(TestCase):
    def test_manifest_and_service_worker_routes_are_public_and_cache_safe(self):
        manifest_response = self.client.get(reverse("web_manifest"))
        self.assertEqual(manifest_response.status_code, 200)
        self.assertEqual(manifest_response["Content-Type"], "application/manifest+json")
        self.assertEqual(manifest_response["Cache-Control"], "no-cache")
        manifest_payload = manifest_response.json()
        self.assertEqual(manifest_payload["display"], "standalone")
        self.assertEqual(len(manifest_payload["icons"]), 3)

        sw_response = self.client.get(reverse("service_worker"))
        self.assertEqual(sw_response.status_code, 200)
        self.assertIn("application/javascript", sw_response["Content-Type"])
        self.assertEqual(sw_response["Cache-Control"], "no-cache")
        self.assertRegex(
            sw_response.content.decode(),
            r'const CACHE_NAME = "clubshub-pwa-v\d+";',
        )
        self.assertContains(sw_response, 'const OFFLINE_URL = "/offline/";')

    def test_offline_page_is_public_and_contains_recovery_actions(self):
        response = self.client.get(reverse("core:offline"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ClubsHub is temporarily unavailable")
        self.assertContains(response, "Try again")
