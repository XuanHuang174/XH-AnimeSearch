import asyncio
import os
import unittest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

import main


class SecurityTests(unittest.TestCase):
    def request(self, method: str, path: str, **kwargs):
        async def send_request():
            async with AsyncClient(
                transport=ASGITransport(app=main.app),
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send_request())

    def test_missing_or_invalid_key_is_rejected(self):
        for headers in ({}, {"Authorization": "Bearer wrong-key"}):
            with self.subTest(headers=headers):
                response = self.request("GET", "/", headers=headers)

                self.assertEqual(response.status_code, 401)
                self.assertEqual(
                    response.json(),
                    {"detail": "Invalid or missing API Key"},
                )

    def test_healthz_ignores_missing_or_invalid_credentials(self):
        for headers in (
            {},
            {"Authorization": "Bearer wrong-key"},
            {"X-API-Key": "wrong-key"},
            {"Authorization": "Basic invalid", "X-API-Key": "wrong-key"},
        ):
            with self.subTest(headers=headers):
                response = self.request("GET", "/healthz", headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": "ok"})

    def test_healthz_exemption_does_not_expose_other_paths(self):
        for path in ("/search", "/health", "/healthz/extra"):
            with self.subTest(path=path):
                response = self.request("GET", path)
                self.assertEqual(response.status_code, 401)

    def test_bearer_and_custom_header_are_accepted(self):
        headers_to_test = (
            {"Authorization": f"Bearer {main.API_SECRET_KEY}"},
            {"X-API-Key": main.API_SECRET_KEY},
        )

        for headers in headers_to_test:
            with self.subTest(headers=headers):
                response = self.request("GET", "/", headers=headers)
                self.assertEqual(response.status_code, 200)

    def test_allowed_origin_can_complete_preflight(self):
        response = self.request(
            "OPTIONS",
            "/search",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://127.0.0.1:5173",
        )

    def test_disallowed_origin_is_rejected_by_preflight(self):
        response = self.request(
            "OPTIONS",
            "/search",
            headers={
                "Origin": "https://attacker.example",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-API-Key",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_auth_failure_keeps_cors_headers(self):
        response = self.request(
            "GET",
            "/",
            headers={"Origin": "https://xh-anime.com"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "https://xh-anime.com",
        )

    def test_production_requires_an_explicit_key(self):
        with patch.dict(os.environ, {"RENDER": "true"}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "API_SECRET_KEY must be set in production",
            ):
                main.get_api_secret_key()


if __name__ == "__main__":
    unittest.main()
