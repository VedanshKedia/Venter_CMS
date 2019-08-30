import ast
import json
import os

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Permission, User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import RequestFactory, TestCase, override_settings
from django.test.client import Client
from django.urls import reverse

from Backend.settings import ADMINS, BASE_DIR, MEDIA_ROOT
from Venter.forms import ContactForm, CSVForm, ExcelForm, ProfileForm, UserForm
from Venter.models import (Category, Domain, File, Header, Keyword,
                           Organisation, Profile, Proposal)
from Venter.views import CategoryListView
from Venter.wordcloud import generate_wordcloud


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LoginTestCase(TestCase):
    """
            Test case for user to log in with valid and invalid credentials
    """
    fixtures = ["Venter/fixtures/fixture_new_1.json"]

    def setUp(self):
        self.client = Client()

    def test_login_admin_civis(self):
        response = self.client.get('/venter/login/')
        self.assertEqual(response.status_code, 200)
        self.client.login(username='admin.civis', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

    def test_login_admin_icmc(self):
        response = self.client.get('/venter/login/')
        self.assertEqual(response.status_code, 200)
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

    def test_login_employee_civis(self):
        response = self.client.get('/venter/login/')
        self.assertEqual(response.status_code, 200)
        self.client.login(username='user1.civis', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

    def test_login_employee_icmc(self):
        response = self.client.get('/venter/login/')
        self.assertEqual(response.status_code, 200)
        self.client.login(username='user1.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

    def test_login_invalid_credentials(self):
        response = self.client.get('/venter/login/')
        self.assertEqual(response.status_code, 200)
        form = AuthenticationForm(data={'username': 'admin.civis', 'password': 'wrong'})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LogoutTestCase(TestCase):
    """
            Test case for user to log out
    """
    fixtures = ["Venter/fixtures/fixture_new_1.json"]

    def setUp(self):
        self.client = Client()

    def test_logout_admin_civis(self):
        self.client.login(username='admin.civis', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_logout_admin_icmc(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_logout_employee_civis(self):
        self.client.login(username='user1.civis', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_logout_employee_icmc(self):
        self.client.login(username='user1.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class UploadFileTestCase(TestCase):
    """
        Test case for user to upload csv/xlsx file
    """
    fixtures = ["Venter/fixtures/fixture_new_1.json"]

    def setUp(self):
        self.client = Client()

    def test_upload_valid_file_civis(self):
        self.client.login(username='admin.civis', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        data = open(os.path.join(MEDIA_ROOT, 'Coverage Test/responses_1.xlsx'), 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        valid_data = {
            "input_file": file_to_upload
        }
        response = self.client.post(reverse('upload_file'), valid_data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')

    def test_upload_invalid_file_civis(self):
        self.client.login(username='admin.civis', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        data = open(os.path.join(MEDIA_ROOT, 'Coverage Test/15_rows_icmc.csv'), 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        invalid_data = {
            "input_file": file_to_upload
        }
        response = self.client.post(reverse('upload_file'), invalid_data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')
        self.assertFormError(response, "file_form", "input_file", "File extension 'csv' is not allowed. Allowed extensions are: 'xlsx'.")

    def test_upload_no_file_civis(self):
        self.client.login(username='admin.civis', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('upload_file'), {"input_file": ''}, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')
        self.assertFormError(response, "file_form", "input_file", "This field is required.")    

    def test_upload_valid_file_icmc(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        data = open(os.path.join(MEDIA_ROOT, 'Coverage Test/15_rows_icmc.csv'), 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        valid_data = {
            "input_file": file_to_upload
        }
        response = self.client.post(reverse('upload_file'), valid_data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')

    def test_upload_non_csv_file_icmc(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        data = open(os.path.join(MEDIA_ROOT, 'Coverage Test/responses_1.xlsx'), 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        invalid_data = {
            "input_file": file_to_upload
        }
        response = self.client.post(reverse('upload_file'), invalid_data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')
        self.assertFormError(response, "file_form", "input_file", "Please upload .csv extension files only")

    def test_upload_no_file_icmc(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('upload_file'), {"input_file": ''}, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')
        self.assertFormError(response, "file_form", "input_file", "This field is required.")

    def test_upload_blank_file_icmc(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        data = open(os.path.join(MEDIA_ROOT, 'Coverage Test/blank_icmc.csv'), 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        invalid_data = {
            "input_file": file_to_upload
        }
        response = self.client.post(reverse('upload_file'), invalid_data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')
        self.assertFormError(response, "file_form", "input_file", "Incorrect headers detected, please upload correct file")

    def test_upload_incorrect_headers_file_icmc(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        data = open(os.path.join(MEDIA_ROOT, 'Coverage Test/incorrect_headers_icmc.csv'), 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        invalid_data = {
            "input_file": file_to_upload
        }
        response = self.client.post(reverse('upload_file'), invalid_data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')
        self.assertFormError(response, "file_form", "input_file", "Incorrect headers detected, please upload correct file")

    def test_upload_max_file_icmc(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        data = open(os.path.join(MEDIA_ROOT, 'Coverage Test/5.3kb_icmc.csv'), 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        invalid_data = {
            "input_file": file_to_upload
        }
        response = self.client.post(reverse('upload_file'), invalid_data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/upload_file.html')
        self.assertFormError(response, "file_form", "input_file", "File size must not exceed 5 MB")  

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WordCloudTestCase(TestCase):
    """
        Test case for users to view wordcloud for a set of responses per category
    """
    fixtures = ["Venter/fixtures/fixture_new_1.json"]

    def setUp(self):
        self.client = Client()

    def test_icmc_wordcloud(self):
        self.client.login(username="admin.icmc", password="pass@1234")

        pk = 207
        file = File.objects.get(pk=pk)
        
        org_name = Organisation.objects.get(organisation_name="ICMC")
        category_queryset = Category.objects.filter(organisation_name=org_name)
        category_list = []
        for element in category_queryset:
            cat = element.category
            category_list.append(cat)

        response = self.client.get(reverse('wordcloud', kwargs={"pk": file.pk}))
        
        self.assertEqual(response.context['category_list'], category_list)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/wordcloud.html')

    def test_civis_wordcloud(self):
        self.client.login(username="admin.civis", password="pass@1234")

        pk = 212
        file = File.objects.get(pk=pk)

        domain_name = "Heritage Conservation"
        wordcloud_category_list = []

        dict_data = json.load(file.output_file_json)
        print("=====================dict_data in test case: ", type(dict_data))
        print(dict_data)
        domain_data = dict_data[domain_name]
        print("=====================domain_data in test case: ", type(domain_data))
        print(domain_data)
        for category, category_dict in domain_data.items():
            wordcloud_category_list.append(category)
        wordcloud_category_list = wordcloud_category_list[:-1]

        print("===============wordcloud category list=====")
        print(type(wordcloud_category_list))
        print(wordcloud_category_list)
        
        data = {
            "wordcloud_domain_name": domain_name
        }

        response = self.client.post(reverse('wordcloud', kwargs={"pk": file.pk}), data)
        
        self.assertEqual(response.context['category_list'], wordcloud_category_list)
        self.assertEqual(response.context['domain_name'], domain_name)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/wordcloud.html')

    def test_civis_wordcloud_content(self):
        self.client.login(username="admin.civis", password="pass@1234")

        pk = 212
        file = File.objects.get(pk=pk)

        domain_name = "Heritage Conservation"
        category_name = "set the boundaries of these heritage zones and said that these areas should be conserved, protected and highlighted by provision of transport facilities and tourist infrastructure"
        temp_cat_list = json.dumps("{'set the boundaries of these heritage zones and said that these areas should be conserved, protected and highlighted by provision of transport facilities and tourist infrastructure', 'The 12 heritage zones identified are: Central Administrative Heritage Zone, Petta and Bangalore Fort, Gavipuram, Basavanagudi and VV Puram, M.G.Road, Shivajinagar, Cleveland Town, Richards Town, Malleshwaram, Ulsoor, Whitefield Inner Circle, Begur Temple and Bangalore Palace Heritage Zone'}")
        data = {
            "category_name": category_name,
            "domain_name": domain_name,
            "category_list": temp_cat_list
        }
        response = self.client.post(reverse('wordcloud_contents', kwargs={"pk": file.pk}), data)
        output_dict = generate_wordcloud(file.output_file_json.path)
        domain_items_list = output_dict[domain_name]
        words = {}

        for domain_item in domain_items_list:
            if list(domain_item.keys())[0].split('\n')[0].strip() == category_name.strip():
                words = list(domain_item.values())[0]

        category_list = json.loads(temp_cat_list)
        self.assertEqual(response.context['category_list'], category_list)
        self.assertEqual(response.context['domain_name'], domain_name)
        self.assertEqual(response.context['words'], words)
        self.assertEqual(response.context['category_name'], category_name)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/wordcloud.html')

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class DashboardTestCase(TestCase):

    def setUp(self):
        civis_org = Organisation.objects.create(organisation_name='CIVIS')
        # Creating dummy users and profiles.
        civis_user = User.objects.create_user(username='test_user', password='useruser')
        Profile.objects.create(user=civis_user, organisation_name=civis_org)

        civis_admin = User.objects.create_superuser(username='test_admin', password='adminadmin', email='a@example.com')
        admin_profile = Profile.objects.create(user=civis_admin, organisation_name=civis_org)

        File.objects.create(uploaded_by=admin_profile, input_file='MEDIA/Test_Files/input/responses_1.xlsx')
        File.objects.create(uploaded_by=admin_profile, input_file='MEDIA/Test_Files/input/responses_2.xlsx')
        File.objects.create(uploaded_by=admin_profile, input_file='MEDIA/Test_Files/input/extra_dummy_file_civis.xlsx')

    def test_file_list_view_employee(self):
        self.client.login(username='test_user', password='useruser')

        # Check that there are no files initially
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/dashboard.html')
        self.assertEqual(len(response.context['file_list']), 0)

        # Check whether file list is empty. If it is, that means the upload file symbol will appear
        self.assertEqual(len(response.context['file_list']), 0)

        # Create a file object uploaded by the user to check whether the file list works as expected
        test_user = User.objects.get(username='test_user')
        test_user_profile = Profile.objects.get(user=test_user)
        File.objects.create(uploaded_by=test_user_profile, input_file='MEDIA/Test_Files/input/responses_3.xlsx')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/dashboard.html')
        self.assertEqual(len(response.context['file_list']), 1)

        self.client.logout()

    def test_file_list_view_staff(self):
        self.client.login(username='test_admin', password='adminadmin')

        # Create a file object uploaded by the user to check whether the file list works as expected
        # For the admins, we expect all the files in setUp to be displayed alongside the new file
        test_user = User.objects.get(username='test_user')
        test_user_profile = Profile.objects.get(user=test_user)
        File.objects.create(uploaded_by=test_user_profile, input_file='MEDIA/Test_Files/input/responses_3.xlsx')

        # Checking whether all files created in the setUp function and the new file are all displayed
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/dashboard.html')
        self.assertEqual(len(response.context['file_list']), 4)

        self.client.logout()

    def test_file_delete_view_employee(self):
        self.client.login(username='test_user', password='useruser')

        # Create a file object uploaded by the user to check whether the file list works as expected
        test_user = User.objects.get(username='test_user')
        test_user_profile = Profile.objects.get(user=test_user)
        File.objects.create(uploaded_by=test_user_profile, input_file='MEDIA/Test_Files/input/responses_3.xlsx')

        # Verify the number of files
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/dashboard.html')
        self.assertEqual(len(response.context['file_list']), 1)

        # Execute the delete view and check whether the '401 forbidden' code is raised
        # This is because we don't give file deletion permissions to users.
        file_obj = response.context['file_list'][0]
        response = self.client.get(reverse('delete_file', args=[file_obj.pk]))
        self.assertEqual(response.status_code, 401)
        self.assertTemplateUsed(response, './Venter/401.html')

        self.client.logout()

    def test_file_delete_view_admin(self):
        self.client.login(username='test_admin', password='adminadmin')

        # Verify the initial number of files
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/dashboard.html')
        self.assertEqual(len(response.context['file_list']), 3)

        # Execute the delete view and then check the number of files.
        # While executing the get request for delete_file, we follow the redirects to the response template
        file_obj = response.context['file_list'][0]
        response = self.client.get(reverse('delete_file', args=[file_obj.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/dashboard.html')
        self.assertEqual(len(response.context['file_list']), 2)

        self.client.logout()


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class CategoryListViewTestCase(TestCase):

    fixtures = ["Venter/fixtures/fixture_new_1.json"]

    def test_category_list_view(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        # Check if total number of categories per page is appropriate according to the corresponding view
        self.assertEqual(len(response.context['category_list']), CategoryListView.paginate_by)
        # Extract pagination data from the context dictionary
        paginator = response.context['paginator']
        # Checking whether all categories are paginated
        self.assertEqual(len(Category.objects.all().filter(organisation_name='ICMC')), paginator.count)
        self.client.logout()

    def test_search_category_list(self):
        self.client.login(username='admin.icmc', password="pass@1234")
        url = '/venter/category_list/'
        response = self.client.get(url, {'q': 'cleaning'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['category_list']), 4)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class UpdateProfileTestCase(TestCase):
    def setUp(self):
        civis_org = Organisation.objects.create(organisation_name='CIVIS')
        # Creating dummy users and profiles
        civis_user = User.objects.create_user(username='user.civis', password='useruser')
        Profile.objects.create(user=civis_user, organisation_name=civis_org)

    def test_get_update_profile(self):
        self.client.login(username='user.civis', password='useruser')
        user_civis = User.objects.get(username='user.civis')
        response = self.client.get(reverse('update_profile', args=[user_civis.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/update_profile.html')

    def test_send_blank_profile_form(self):
        self.client.login(username='user.civis', password='useruser')
        user_civis = User.objects.get(username='user.civis')
        response = self.client.post(reverse('update_profile', args=[user_civis.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], True)
        self.assertTemplateUsed(response, './Venter/update_profile.html')

    def test_send_phone_number_profile_form(self):
        self.client.login(username='user.civis', password='useruser')
        user_civis = User.objects.get(username='user.civis')
        data = {
            'phone_number': '9870827126'
        }
        response = self.client.post(reverse('update_profile', args=[user_civis.pk]), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], True)
        self.assertTemplateUsed(response, './Venter/update_profile.html')

    def test_send_invalid_number_profile_form(self):
        self.client.login(username='user.civis', password='useruser')
        user_civis = User.objects.get(username='user.civis')
        data = {
            'phone_number': '1234567890'
        }
        response = self.client.post(reverse('update_profile', args=[user_civis.pk]), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200) 
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/update_profile.html')
        self.assertFormError(response, "profile_form", "phone_number", "Please enter a valid phone number")

    def test_non_image_profile_picture(self):
        self.client.login(username='user.civis', password='useruser')
        user_civis = User.objects.get(username='user.civis')

        data = open('media/Test_Files/input/demoicmc.csv', 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        data = {
            'profile_picture': file_to_upload
        }
        response = self.client.post(reverse('update_profile', args=[user_civis.pk]), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/update_profile.html')
        self.assertFormError(response, "profile_form", "profile_picture", "File extension 'csv' is not allowed. Allowed extensions are: 'png, jpg, jpeg'.")

    def test_max_size_profile_picture(self):
        self.client.login(username='user.civis', password='useruser')
        user_civis = User.objects.get(username='user.civis')

        data = open('media/Test_Files/input/invalid_size_profile_picture.jpg', 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        data = {
            'profile_picture': file_to_upload
        }
        response = self.client.post(reverse('update_profile', args=[user_civis.pk]), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/update_profile.html')
        self.assertFormError(response, "profile_form", "profile_picture", "Profile picture size must not exceed 1 MB")

    def test_valid_profile_picture(self):
        self.client.login(username='user.civis', password='useruser')
        user_civis = User.objects.get(username='user.civis')

        data = open('media/Test_Files/input/valid_size_profile_picture.jpg', 'rb')
        file_to_upload = SimpleUploadedFile(data.name, data.read())
        data = {
            'profile_picture': file_to_upload
        }
        response = self.client.post(reverse('update_profile', args=[user_civis.pk]), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], True)
        self.assertTemplateUsed(response, './Venter/update_profile.html')

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class RegisterEmployeeTestCase(TestCase):
    def setUp(self):
        civis_org = Organisation.objects.create(organisation_name='CIVIS')
        # Creating dummy users and profiles
        civis_admin = User.objects.create_superuser(username='test_admin', password='adminadmin', email='a@example.com')
        Profile.objects.create(user=civis_admin, organisation_name=civis_org)

    def test_get_register_employee(self):
        self.client.login(username='test_admin', password='adminadmin')
        response = self.client.get(reverse('register_employee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/registration.html')

    def test_send_blank_or_incomplete_register_employee_form(self):
        self.client.login(username='test_admin', password='adminadmin')
        response = self.client.post(reverse('register_employee'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/registration.html')

    def test_invalid_email_register_employee_form(self):
        self.client.login(username='test_admin', password='adminadmin')
        data = {
            'username': 'user.civis',
            'password': 'useruser',
            'email': 'user@civis',
            'first_name': 'User',
            'last_name': 'Civis'
        }
        response = self.client.post(reverse('register_employee'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/registration.html')
        self.assertFormError(response, "user_form", "email", "Enter a valid email address.")

    def test_common_password_register_employee_form(self):
        self.client.login(username='test_admin', password='adminadmin')
        data = {
            'username': 'user.civis',
            'password': '1234',
            'email': 'user@civis.com',
            'first_name': 'User',
            'last_name': 'Civis'
        }
        response = self.client.post(reverse('register_employee'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/registration.html')
        self.assertFormError(response, "user_form", "password", "This password is too common.")

    def test_similar_password_register_employee_form(self):
        self.client.login(username='test_admin', password='adminadmin')
        data = {
            'username': 'user.civis',
            'password': 'user.civis',
            'email': 'user@civis.com',
            'first_name': 'User',
            'last_name': 'Civis'
        }
        response = self.client.post(reverse('register_employee'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/registration.html')
        self.assertFormError(response, "user_form", "password", "The password is too similar to the username.")

    def test_numeric_password_register_employee_form(self):
        self.client.login(username='test_admin', password='adminadmin')
        data = {
            'username': 'user.civis',
            'password': '98798798',
            'email': 'user@civis.com',
            'first_name': 'User',
            'last_name': 'Civis'
        }
        response = self.client.post(reverse('register_employee'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/registration.html')
        self.assertFormError(response, "user_form", "password", "This password is entirely numeric.")

    def test_valid_employee_register_form(self):
        self.client.login(username='test_admin', password='adminadmin')
        data = {
            'username': 'user.civis',
            'password': 'useruser',
            'email': 'user@civis.com',
            'first_name': 'User',
            'last_name': 'Civis'
        }
        response = self.client.post(reverse('register_employee'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], True)
        self.assertTemplateUsed(response, './Venter/registration.html')

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ContactUsTestCase(TestCase):
    def test_get_contact_us(self):
        response = self.client.get(reverse('contact_us'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')

    def test_blank_or_incomplete_contact_us(self):
        response = self.client.post(reverse('contact_us'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')

    def test_invalid_firstname_contact_us(self):
        data = {
            'first_name': '@abc',
            'last_name': 'User',
            'designation': 'CEO',
            'city': 'Mumbai',
            'company_name': 'Company',
            'email_address': 'user@company.com',
            'contact_no': '9876543210',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('contact_us'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')
        self.assertFormError(response, "contact_form", "first_name", "Please enter a valid first name")

    def test_invalid_lastname_contact_us(self):
        data = {
            'first_name': 'Test',
            'last_name': '09',
            'designation': 'CEO',
            'city': 'Mumbai',
            'company_name': 'Company',
            'email_address': 'user@company.com',
            'contact_no': '9876543210',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('contact_us'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')
        self.assertFormError(response, "contact_form", "last_name", "Please enter a valid last name")     

    def test_invalid_email_contact_us(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'designation': 'CEO',
            'city': 'Test',
            'company_name': 'Company',
            'email_address': 'user@company',
            'contact_no': '9876543210',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('contact_us'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')
        self.assertFormError(response, "contact_form", "email_address", "Enter a valid email address.")

    def test_invalid_number_contact_us(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Company',
            'designation': 'CEO',
            'city': 'Test',
            'email_address': 'user@company.com',
            'contact_no': '1234567890',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('contact_us'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')
        self.assertFormError(response, "contact_form", "contact_no", "Please enter a valid phone number")

    def test_invalid_company_contact_us(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Company &(*^',
            'designation': 'CEO',
            'city': 'Test',
            'email_address': 'user@company.com',
            'contact_no': '1234567890',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('contact_us'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')
        self.assertFormError(response, "contact_form", "company_name", "Please enter a valid company name")

    def test_invalid_designation_contact_us(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Company 123',
            'designation': '123',
            'city': 'Test',
            'email_address': 'user@company.com',
            'contact_no': '1234567890',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('contact_us'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')
        self.assertFormError(response, "contact_form", "designation", "Please enter a valid designation")

    def test_invalid_city_contact_us(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Company',
            'designation': 'CEO',
            'city': '123',
            'email_address': 'user@company.com',
            'contact_no': '1234567890',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('contact_us'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/contact_us.html')
        self.assertFormError(response, "contact_form", "city", "Please enter a valid city name")

    def test_valid_contact_us(self):
        User.objects.create_superuser(username='test_admin', password='passpass', email='admin@ex.com')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Company',
            'designation': 'CEO',
            'city': 'Mumbai',
            'email_address': 'user@company.com',
            'contact_no': '9876543210',
            'detail_1': 'Test',
            'detail_2': 'Test',
        }
        response = self.client.post(reverse('contact_us'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], True)
        self.assertTemplateUsed(response, './Venter/contact_us.html')

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class RequestDemoTestCase(TestCase):
    def test_get_request_demo(self):
        response = self.client.get(reverse('request_demo'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/request_demo.html')

    def test_blank_or_incomplete_request_demo(self):
        response = self.client.post(reverse('request_demo'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/request_demo.html')

    def test_invalid_firstname_request_demo(self):
        data = {
            'first_name': '@abc',
            'last_name': 'User',
            'designation': 'CEO',
            'city': 'Mumbai',
            'company_name': 'Company',
            'email_address': 'user@company.com',
            'contact_no': '9876543210',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('request_demo'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/request_demo.html')
        self.assertFormError(response, "contact_form", "first_name", "Please enter a valid first name")

    def test_invalid_lastname_request_demo(self):
        data = {
            'first_name': 'Test',
            'last_name': '09',
            'designation': 'CEO',
            'city': 'Mumbai',
            'company_name': 'Company',
            'email_address': 'user@company.com',
            'contact_no': '9876543210',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('request_demo'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/request_demo.html')
        self.assertFormError(response, "contact_form", "last_name", "Please enter a valid last name")     

    def test_invalid_email_request_demo(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'designation': 'CEO',
            'city': 'Mumbai',
            'company_name': 'Company',
            'email_address': 'user@company',
            'contact_no': '9876543210',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('request_demo'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/request_demo.html')
        self.assertFormError(response, "contact_form", "email_address", "Enter a valid email address.")

    def test_invalid_number_request_demo(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Company',
            'designation': 'CEO',
            'city': 'Mumbai',
            'email_address': 'user@company.com',
            'contact_no': '1234567890',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('request_demo'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/request_demo.html')
        self.assertFormError(response, "contact_form", "contact_no", "Please enter a valid phone number")

    def test_invalid_city_request_demo(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Company',
            'designation': 'CEO',
            'city': '123',
            'email_address': 'user@company.com',
            'contact_no': '1234567890',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('request_demo'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], False)
        self.assertTemplateUsed(response, './Venter/request_demo.html')
        self.assertFormError(response, "contact_form", "city", "Please enter a valid city name")

    def test_valid_request_demo(self):
        User.objects.create_superuser(username='test_admin', password='passpass', email='admin@ex.com')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Company',
            'designation': 'CEO',
            'city': 'Mumbai',
            'email_address': 'user@company.com',
            'contact_no': '9876543210',
            'detail_1': 'Test',
            'detail_2': 'Test',
            'detail_3': 'Test'
        }
        response = self.client.post(reverse('request_demo'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['successful_submit'], True)
        self.assertTemplateUsed(response, './Venter/request_demo.html')        


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PasswordResetTestCase(TestCase):
    def setUp(self):
        civis_org = Organisation.objects.create(organisation_name='CIVIS')
        # Creating dummy users and profiles
        civis_admin = User.objects.create_superuser(username='test_admin', password='adminadmin', email='a@example.com')
        Profile.objects.create(user=civis_admin, organisation_name=civis_org)

    def test_get_password_reset(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Venter/password_reset_form.html')
    
    def test_post_invalid_email_password_reset(self):
        # Retrieve the blank form
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Venter/password_reset_form.html')
        data = {
            'email': 'test@test'
        }
        response = self.client.post(reverse('password_reset'), data, enctype='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Venter/password_reset_form.html')
        self.assertFormError(response, "form", "email", "Enter a valid email address.")

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class AboutUsTestCase(TestCase):
    def test_get_about_us(self):
        response = self.client.get(reverse('about_us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/about_us.html')


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class AddProposalTestCase(TestCase):
    def setUp(self):
        civis_org = Organisation.objects.create(organisation_name='CIVIS')
        civis_admin = User.objects.create_superuser(username='test_admin', password='adminadmin', email='a@example.com')
        Profile.objects.create(user=civis_admin, organisation_name=civis_org)

    def test_get_add_proposal(self):
        self.client.login(username='test_admin', password='adminadmin')
        response = self.client.get(reverse('add_proposal'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['one_save_operation'], False)
        self.assertTemplateUsed(response, './Venter/add_proposal.html')

    def test_post_invalid_proposal_name(self):
        self.client.login(username='test_admin', password="adminadmin")
        response = self.client.get(reverse('add_proposal'))
        self.assertEqual(response.status_code, 200)

        keyword_list = json.dumps("{'a', 'b', 'c'}")

        invalid_data = {
            "proposal_name": 'xyz &()_21',
            "domain_name": 'xyz',
            "keyword_list": keyword_list,
            "final_submit": True,
            "one_save_operation": False,
        }
        response = self.client.post(reverse('add_proposal'), invalid_data, enctype='multipart/form-data')

        self.assertEqual(response.context['one_save_operation'], False)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/add_proposal.html')
        self.assertFormError(response, "proposal_form", "proposal_name", "Proposal name may contain letters, digits, underscore and spaces only")

    def test_post_existing_proposal(self):
        self.client.login(username='test_admin', password="adminadmin")
        response = self.client.get(reverse('add_proposal'))
        self.assertEqual(response.status_code, 200)

        proposal_obj = Proposal.objects.create(proposal_name='xyz_1')
        proposal_obj.save()

        keyword_list = json.dumps("{'a', 'b', 'c'}")

        invalid_data = {
            "proposal_name": 'xyz_1',
            "domain_name": 'xyz',
            "keyword_list": keyword_list,
            "final_submit": True,
            "one_save_operation": False,
        }
        response = self.client.post(reverse('add_proposal'), invalid_data, enctype='multipart/form-data')

        # category_list = json.loads(keyword_list)
        self.assertEqual(response.context['one_save_operation'], False)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/add_proposal.html')
        self.assertFormError(response, "proposal_form", "proposal_name", "Proposal with this Proposal name already exists.")

    def test_post_existing_domain_name(self):
        self.client.login(username='test_admin', password="adminadmin")
        response = self.client.get(reverse('add_proposal'))
        self.assertEqual(response.status_code, 200)

        proposal_obj = Proposal.objects.create(proposal_name='lmn')
        proposal_obj.save()
        domain_obj = Domain.objects.create(proposal_name=proposal_obj, domain_name='xyz')
        domain_obj.save()

        keyword_list = json.dumps("{'a', 'b', 'c'}")

        final_submit = "true"
        
        invalid_data = {
            "proposal_name": 'lmn',
            "domain_name": 'xyz',
            "keyword_list": keyword_list,
            "final_submit": final_submit,
            "one_save_operation": True,
        }
        response = self.client.post(reverse('add_proposal'), invalid_data, enctype='multipart/form-data')

        if final_submit == "true":
            final_submit = True
        elif final_submit == "false":
            final_submit = False

        try:
            Domain.objects.create(proposal_name=proposal_obj, domain_name='xyz')
        except IntegrityError as e:
            self.assertEqual(response.context['one_save_operation'], True)
            self.assertEqual(response.context['proposal_name'], 'lmn')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, './Venter/add_proposal.html')
            self.assertFormError(response, "domain_form", "domain_name", "Domain for this Domain name already exists")

    def test_post_valid_save_and_add_another_domain(self):
        self.client.login(username='test_admin', password="adminadmin")
        response = self.client.get(reverse('add_proposal'))
        self.assertEqual(response.status_code, 200)

        proposal_obj = Proposal.objects.create(proposal_name='lmn')
        proposal_obj.save()

        keyword_list = json.dumps("{'a', 'b', 'c'}")

        invalid_data = {
            "proposal_name": 'lmn',
            "domain_name": 'xyz',
            "keyword_list": keyword_list,
            "final_submit": False,
            "one_save_operation": True,
        }
        response = self.client.post(reverse('add_proposal'), invalid_data, enctype='multipart/form-data')

        # category_list = json.loads(keyword_list)
        self.assertEqual(response.context['final_submit'], False)
        self.assertEqual(response.context['one_save_operation'], True)
        self.assertEqual(response.context['proposal_name'], 'lmn')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/add_proposal.html')

    def test_post_valid_save_proposal(self):
        self.client.login(username='test_admin', password="adminadmin")
        response = self.client.get(reverse('add_proposal'))
        self.assertEqual(response.status_code, 200)

        proposal_obj = Proposal.objects.create(proposal_name='lmn')
        proposal_obj.save()

        keyword_list = json.dumps("{'a', 'b', 'c'}")

        invalid_data = {
            "proposal_name": 'lmn',
            "domain_name": 'xyz',
            "keyword_list": keyword_list,
            "final_submit": True,
            "one_save_operation": True,
        }
        response = self.client.post(reverse('add_proposal'), invalid_data, enctype='multipart/form-data')

        # category_list = json.loads(keyword_list)
        self.assertEqual(response.context['final_submit'], True)
        self.assertEqual(response.context['one_save_operation'], True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, './Venter/add_proposal.html')     
