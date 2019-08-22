from django.contrib.auth.models import AnonymousUser, User
from django.test import Client, RequestFactory, TestCase
from .models import Organisation, Profile, Header
from .helpers import create_org, create_profile
# Testing model methods in accordance with the coverage.py report
class ModelTestCase(TestCase):

    # def create_org(self):
    #     """Helper function for creating organisations."""
    #     return Organisation.objects.create(organisation_name="Test Org")

    # def create_profile(self):
    #     """Helper function for creating test user and test profile."""
    #     user = User.objects.create_user('Test')
    #     org = self.create_org()
    #     return Profile.objects.create(user=user, organisation_name=org)

    def test_org_name(self):
        new_org = create_org()
        self.assertTrue(isinstance(new_org, Organisation))
        self.assertEqual(new_org.organisation_name, str(new_org))

    def test_profile_name(self):
        profile = create_profile()
        self.assertTrue(isinstance(profile, Profile))
        self.assertEqual(profile.user.username, str(profile))

class FileUploadTestCase(TestCase):

    def setUp(self):
        # Dummy user profile
        self.client = Client(enforce_csrf_checks=True)

    def test_file_upload(self):
        demosuperuser = User.objects.create_superuser('admin', 'example.com', 'adminadmin')
        demo_org = Organisation.objects.create(organisation_name='ICMC')
        admin_profile = Profile.objects.create(user=demosuperuser, organisation_name=demo_org)
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(demosuperuser)

        url = '/venter/upload_csv/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        with open('log.txt', 'w') as f:
            f.write(str(response.context))
        # self.assertEqual(response.context['Organisation'], 'Test')

        # with open('MEDIA\Test Files\demoicmc.csv') as f:
        #     response = self.client.post(url, {'csv_file': f})
        # self.assertEqual(response.status_code, 200)
        
