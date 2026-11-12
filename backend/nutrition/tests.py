from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.test import APIRequestFactory

from .views import FoodScanViewSet


class FoodScanParserTests(SimpleTestCase):
    def test_create_accepts_multipart_form_data(self):
        request = APIRequestFactory().post(
            "/api/nutrition/scans/",
            {
                "image": SimpleUploadedFile("meal.jpg", b"image-data", content_type="image/jpeg"),
                "meal_type": "LUNCH",
                "note": "Test upload",
            },
            format="multipart",
        )

        drf_request = FoodScanViewSet().initialize_request(request)

        self.assertIsInstance(drf_request.parsers[0], JSONParser)
        self.assertIsInstance(drf_request.parsers[1], MultiPartParser)
        self.assertIsInstance(drf_request.parsers[2], FormParser)
        self.assertIn("image", drf_request.FILES)
        self.assertEqual(drf_request.data["meal_type"], "LUNCH")
