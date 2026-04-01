from django.test import TestCase, override_settings
from django.urls import reverse


class PagesViewTests(TestCase):
    """Smoke tests: every page returns 200 and uses the correct template."""

    def test_home_page(self):
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertContains(response, "MOLONARI1D")

    def test_about_page(self):
        response = self.client.get(reverse("pages:about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/about.html")

    def test_hardware_page(self):
        response = self.client.get(reverse("pages:hardware"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/hardware.html")

    def test_software_page(self):
        response = self.client.get(reverse("pages:software"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/software.html")

    def test_contact_page(self):
        response = self.client.get(reverse("pages:contact"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/contact.html")

    def test_navigation_links_present(self):
        """The base template should contain links to all pages."""
        response = self.client.get(reverse("pages:home"))
        for name in ("pages:home", "pages:about", "pages:hardware",
                     "pages:software", "pages:contact"):
            self.assertContains(response, reverse(name))
