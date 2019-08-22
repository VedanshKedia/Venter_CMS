import datetime
import json
import operator
import os
from functools import reduce

import jsonpickle
import pandas as pd
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.models import Permission, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from Backend.settings import MEDIA_ROOT

from Venter.forms import ContactForm, CSVForm, ExcelForm, ProfileForm, UserForm
from Venter.helpers import get_result_file_path
from Venter.models import Category, File, Profile

from .manipulate_csv import EditCsv
from .ML_model.Civis.modeldriver import SimilarityMapping


@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def upload_file(request):
    """
    View logic for uploading CSV file by a logged in user.

    For POST request-------
        1) The POST data, uploaded csv file and a request parameter are being sent to CSVForm as arguments
        2) If form.is_valid() returns true, the user is assigned to the uploaded_by field
        3) file_form is saved and Form instance is initialized again (file_form = CSVForm(request=request)),
           for user to upload another file after successfully uploading the previous file
    For GET request-------
        The file_form is rendered in the template
    """

    if str(request.user.profile.organisation_name) == 'CIVIS':
        excel_form = ExcelForm(request=request)
        if request.method == 'POST':
            excel_form = ExcelForm(
                request.POST, request.FILES, request=request)
            if excel_form.is_valid():
                file_uploaded = excel_form.save(commit=False)
                file_uploaded.uploaded_by = request.user.profile
                file_uploaded.save()
                excel_form = ExcelForm(request=request)
                return render(request, './Venter/upload_file.html', {
                    'file_form': excel_form, 'successful_submit': True})
        return render(request, './Venter/upload_file.html', {
            'file_form': excel_form})
    else:
        file_form = CSVForm(request=request)
        if request.method == 'POST':
            file_form = CSVForm(request.POST, request.FILES, request=request)
            if file_form.is_valid():
                file_uploaded = file_form.save(commit=False)
                file_uploaded.uploaded_by = request.user.profile
                file_uploaded.save()
                file_form = CSVForm(request=request)
                return render(request, './Venter/upload_file.html', {
                    'file_form': file_form, 'successful_submit': True})

        return render(request, './Venter/upload_file.html', {
            'file_form': file_form})


def handle_user_selected_data(request):
    """This function is used to handle the selected categories by the user"""
    if not request.user.is_authenticated:
        # Authentication security check
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        rows = request.session['Rows']
        correct_category = []
        company = request.session['company']
        if request.method == 'POST':
            file_name = request.session['filename']
            user_name = request.user.username
            for i in range(rows):
                # We are getting a list of values because the select tag was multiple select
                selected_category = request.POST.getlist(
                    'select_category' + str(i) + '[]')
                if request.POST['other_category' + str(i)]:
                    # To get a better picture of what we are getting try to print "request.POST.['other_category' + str(i)]", request.POST['other_category' + str(i)
                    # others_list=request.POST['other_category' + str(i)]
                    # for element in others_list:
                    #     print(element)
                    #     tuple = (selected_category,element)
                    tuple = (selected_category,
                             request.POST['other_category' + str(i)])
                    # print(request.POST['other_category' + str(i)])
                    # print(tuple)
                    # So here the correct_category will be needing a touple so the data will be like:
                    # [(selected_category1, selected_category2), (other_category1, other_category2)] This will be the output of the multi select
                    correct_category.append(tuple)
                else:
                    # So here the correct_category will be needing a touple so the data will be like:
                    # [(selected_category1, selected_category2)] This will be the output of the multi select
                    correct_category.append(selected_category)
        csv = EditCsv(file_name, user_name, company)
        csv.write_file(correct_category)
        if request.POST['radio'] != "no":
            # If the user want to send the file to Google Drive
            path_folder = request.user.username + "/CSV/output/"
            path_file = 'MEDIA/' + request.user.username + \
                "/CSV/output/" + request.session['filename']
            path_file_diff = 'MEDIA/' + request.user.username + "/CSV/output/Difference of " + request.session[
                'filename']
            upload_to_google_drive.upload_to_drive(path_folder,
                                                   'results of ' +
                                                   request.session['filename'],
                                                   "Difference of " +
                                                   request.session['filename'],
                                                   path_file,
                                                   path_file_diff)
    return redirect("/download")


def handle_uploaded_file(f, username, filename):
    """Just a precautionary step if signals.py doesn't work for any reason."""

    data_directory_root = settings.MEDIA_ROOT
    path = os.path.join(data_directory_root, username,
                        "CSV", "input", filename)
    path_input = os.path.join(data_directory_root, username, "CSV", "input")
    path_output = os.path.join(data_directory_root, username, "CSV", "output")

    if not os.path.exists(path_input):
        os.makedirs(path_input)

    if not os.path.exists(path_output):
        os.makedirs(path_output)

    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


class CategoryListView(LoginRequiredMixin, ListView):
    """
    Arguments------
        1) LoginRequiredMixin: Request to update profile details by non-authenticated users,
        will throw an HTTP 404 error
        2) ListView: View to display the category list for the organisation to which the logged-in user belongs

    Functions------
        1) get_queryset(): Returns a new QuerySet filtering categories
        based on the organisation name passed in the parameter.
    """
    model = Category
    paginate_by = 10

    def get_queryset(self):

        result = Category.objects.filter(organisation_name=self.request.user.profile.organisation_name)

        query = self.request.GET.get('q','')

        if query:
            result = Category.objects.filter(category__icontains=query)

        return result


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    """
    Arguments------
        1) UpdateView: View to update the user profile details for the logged-in user
        2) LoginRequiredMixin: Request to update profile details by non-authenticated users,
        will throw an HTTP 404 error
    """
    model = Profile
    success_url = reverse_lazy('home')

    def post(self, request, *args, **kwargs):
        profile_form = ProfileForm(
            request.POST, request.FILES, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            profile_form = ProfileForm(instance=request.user.profile)
            return render(request, './Venter/update_profile.html',
                          {'profile_form': profile_form, 'successful_submit': True})
        else:
            return render(request, './Venter/update_profile.html',
                          {'profile_form': profile_form})

    def get(self, request, *args, **kwargs):
        profile_form = ProfileForm(instance=request.user.profile)
        return render(request, './Venter/update_profile.html', {'profile_form': profile_form})


class RegisterEmployeeView(LoginRequiredMixin, CreateView):
    """
    Arguments------
        1) CreateView: View to register a new user(employee) of an organisation.
    Note------
        1) The organisation name for a newly registered employee is taken from
           the profile information of the staff member registering the employee.
        2) The profile.save() returns an instance of Profile that has been saved to the database.
            This occurs only after the profile is created for a new user with the 'profile.user = user'
        3) The validate_password() is an in-built password validator in Django
            # module-django.contrib.auth.password_validation
        Ref: https://docs.djangoproject.com/en/2.1/topics/auth/passwords/
        4) The user_form instance is initialized again (user_form = UserForm()), for staff member
            to register another employee after successful submission of previous form
    """
    model = User

    def post(self, request, *args, **kwargs):
        user_form = UserForm(request.POST)
        if user_form.is_valid():
            user_obj = user_form.save(commit=False)
            password = user_form.cleaned_data.get('password')
            try:
                validate_password(password, user_obj)
                user_obj.set_password(password)
                user_obj.save()
                org_name = request.user.profile.organisation_name
                permission = Permission.objects.get(
                    name='Can view files uploaded by self')
                user_obj.user_permissions.add(permission)
                profile = Profile.objects.create(
                    user=user_obj, organisation_name=org_name)
                profile.save()
                user_form = UserForm()
                return render(request, './Venter/registration.html', {'user_form': user_form, 'successful_submit': True})
            except ValidationError as e:
                user_form.add_error('password', e)
                return render(request, './Venter/registration.html', {'user_form': user_form})
        else:
            return render(request, './Venter/registration.html', {'user_form': user_form})

    def get(self, request, *args, **kwargs):
        user_form = UserForm()
        return render(request, './Venter/registration.html', {'user_form': user_form})


def contact_us(request):
    """
    View logic to email the administrator the contact details submitted by an organisation.
    The contact details are submitted through the 'contact_us' template form.

    For POST request-------
        The contact details of an organisation are collected in the ContactForm.
        If the form is valid, an email is sent to the website administrator.
    For GET request-------
        The contact_us template is rendered
    """
    contact_form = ContactForm()

    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            company_name = contact_form.cleaned_data.get('company_name')
            contact_no = contact_form.cleaned_data.get('contact_no')
            email_address = contact_form.cleaned_data.get('email_address')
            requirement_details = contact_form.cleaned_data.get(
                'requirement_details')

            # get current date and time
            now = datetime.datetime.now()
            date_time = now.strftime("%Y-%m-%d %H:%M")

            # prepare email body
            email_body = "Dear Admin,\n\n Following are the inquiry details:\n\n " + \
                "Inquiry Date and Time: "+date_time+"\n Company Name: " + \
                company_name+"\n Contact Number: "+contact_no+"\n Email address: " + \
                email_address+"\n Requirement Details: "+requirement_details+"\n\n"
            mail_admins('Venter Inquiry', email_body)
            # contact_form.save()
            contact_form = ContactForm()
            return render(request, './Venter/contact_us.html', {
                'contact_form': contact_form, 'successful_submit': True})
    return render(request, './Venter/contact_us.html', {
        'contact_form': contact_form,
    })


class FileDeleteView(LoginRequiredMixin, DeleteView):
    """
    Arguments------
        1) LoginRequiredMixin: View to redirect non-authenticated users to show HTTP 403 error
        2) PermissionRequiredMixin: View to check whether the user is a staff
        having permission to delete organisation files
        3) DeletView: View to delete the files uploaded by user(s)/staff member(s) of the organisation

    Functions------
        1) get_queryset(): Returns a new QuerySet filtering files uploaded by the logged-in user
    """
    model = File
    success_url = reverse_lazy('dashboard')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class FileListView(LoginRequiredMixin, ListView):
    model = File
    template_name = './Venter/dashboard.html'
    context_object_name = 'file_list'
    paginate_by = 8

    def get_queryset(self):
        if self.request.user.is_staff:
            result = File.objects.filter(
                uploaded_by__organisation_name=self.request.user.profile.organisation_name)
        elif not self.request.user.is_staff and self.request.user.is_active:
            result =  File.objects.filter(uploaded_by=self.request.user.profile)

        query = self.request.GET.get('q','')
        if query:
            result = [file_obj for file_obj in result if query in file_obj.filename.lower()]
        return result


@require_http_methods(["GET"])
def predict_result(request, pk):
    global dict_data, domain_list

    filemeta = File.objects.get(pk=pk)
    if not filemeta.has_prediction:
        output_directory_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output')

        if not output_directory_path:
            os.makedirs(output_directory_path)

        output_file_path_json = os.path.join(output_directory_path, 'results.json')
        output_file_path_xlsx = os.path.join(output_directory_path, 'results.xlsx')

        sm = SimilarityMapping(filemeta.input_file.path)
        dict_data = sm.driver()

        if dict_data:
            filemeta.has_prediction = True

        with open(output_file_path_json, 'w') as temp:
            json.dump(dict_data, temp)

        print('JSON output saved.')
        print('Done.')

        filemeta.output_file_json = output_file_path_json

        download_output = pd.ExcelWriter(output_file_path_xlsx, engine='xlsxwriter')

        for domain in dict_data:
            print('Writing Excel for domain %s' % domain)
            df = pd.DataFrame({ key:pd.Series(value) for key, value in dict_data[domain].items() })
            df.to_excel(download_output, sheet_name=domain)
        download_output.save()

        filemeta.output_file_xlsx = output_file_path_xlsx
        filemeta.save()
    else:
        dict_data = json.load(filemeta.output_file_json)
    dict_keys = dict_data.keys()
    domain_list = list(dict_keys)

    return render(request, './Venter/prediction_result.html', {
        'domain_list': domain_list, 'dict_data': dict_data
    })


@require_http_methods(["GET"])
def domain_contents(request):
    global dict_data, domain_list


    domain_name = request.GET.get('domain')
    domain_data = dict_data[domain_name]
    temp = ['Category']
    index = 0
    for subCat in domain_data['Novel']:
        temp.append('Sub category ' + str(index+1))
        index += 1
    temp.append({'role':'style'})
    domain_stats = []
    domain_stats.append(temp)

    for category, responselist in domain_data.items():
        column = [category, len(responselist), '']
        if category == 'Novel':
            column = ['Novel']
            for subCat in domain_data[category]:
                column.append(len(domain_data[category][subCat]))
            column.append('')
        else:
            for i in range(len(domain_stats[0]) - len(column)):
                column.insert(2,0)
        domain_stats.append(column)

    return render(request, './Venter/prediction_result.html', {
        'domain_data': domain_data, 'domain_list': domain_list, 'domain_stats': jsonpickle.encode(domain_stats)
    })
