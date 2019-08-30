import datetime
import json
import os
import pathlib
import re
from ast import literal_eval
from collections import defaultdict

import jsonpickle
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from nltk import tokenize

from Backend.settings import ADMINS, MEDIA_ROOT, STATIC_ROOT, BASE_DIR
from Venter.forms import (ContactForm, CSVForm, DomainForm, SentenceModelForm,
                          KeywordForm, ProfileForm, ProposalForm, UserForm, KeywordModelForm)
from Venter.models import Category, Domain, File, Keyword, Profile, Proposal
# from Venter import tasks
from Venter.wordcloud import generate_keywords, generate_wordcloud

from .ML_model.ICMC.model.ClassificationService import ClassificationService
from .ML_model.keyword_model.modeldriver import KeywordSimilarityMapping
from .ML_model.sentence_model.modeldriver import SimilarityMapping


@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def upload_file(request):
    """
    View logic for uploading CSV/Excel file by a logged in user.

    For POST request-------
        1) The POST data, uploaded csv/xlsx file and a request parameter are being sent to CSVForm/SentenceModelForm as arguments
        2) If form.is_valid() returns true, the user is assigned to the uploaded_by field
        3) file_form is saved and Form instance is initialized again,
           for user to upload another file after successfully uploading the previous file
    For GET request-------
        The file_form is rendered in the template
    """
    if request.method == 'POST':
        if str(request.user.profile.organisation_name) == 'CIVIS':
            temp_model_choice = request.POST['model_choice_name']
            if(temp_model_choice == "sentence_model_card"):
                sentence_model_form = SentenceModelForm(
                    request.POST, request.FILES, request=request)
                if sentence_model_form.is_valid():
                    file_uploaded = sentence_model_form.save(commit=False)
                    file_uploaded.uploaded_by = request.user.profile
                    file_uploaded.model_choice = 'sentence_model'
                    file_uploaded.save()
                    sentence_model_form = SentenceModelForm(request=request)
                    return render(request, './Venter/upload_file.html', {
                        'file_form': sentence_model_form, 'successful_submit': True})
                return render(request, './Venter/upload_file.html', {
                        'file_form': sentence_model_form, 'successful_submit': False})
            elif(temp_model_choice == "keyword_model_card"):
                keyword_model_form = KeywordModelForm(
                    request.POST, request.FILES, request=request)
                if keyword_model_form.is_valid():
                    file_uploaded = keyword_model_form.save(commit=False)
                    file_uploaded.uploaded_by = request.user.profile
                    file_uploaded.model_choice = 'keyword_model'
                    file_uploaded.save()
                    keyword_model_form = KeywordModelForm(request=request)
                    return render(request, './Venter/upload_file.html', {
                        'file_form': keyword_model_form, 'successful_submit': True})
                return render(request, './Venter/upload_file.html', {
                        'file_form': keyword_model_form, 'successful_submit': False})
        elif str(request.user.profile.organisation_name) == 'ICMC':
            file_form = CSVForm(request.POST, request.FILES, request=request)
            if file_form.is_valid():
                file_uploaded = file_form.save(commit=False)
                file_uploaded.uploaded_by = request.user.profile
                file_uploaded.save()
                file_form = CSVForm(request=request)
                return render(request, './Venter/upload_file.html', {
                    'file_form': file_form, 'successful_submit': True})
            return render(request, './Venter/upload_file.html', {
                    'file_form': file_form, 'successful_submit': False})
    elif request.method == 'GET':
        if str(request.user.profile.organisation_name) == 'CIVIS':
            return render(request, './Venter/choose_model.html', {
                'successful_submit': False})
        elif str(request.user.profile.organisation_name) == 'ICMC':
            file_form = CSVForm(request=request)
            return render(request, './Venter/upload_file.html', {
                'file_form': file_form, 'successful_submit': False})

@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def choose_model(request):
    """
    View logic for choosing machine learning model by a logged in CIVIS user.

    For POST request-------
        1) The ML model choice is retrieved from the 'choose_model' template
        2) Based on the Civis user's selection, the corresponding ModelForm fields are populated in 'upload_file' template
    For GET request-------
        The 'choose_model' template is rendered
    """
    if request.method == 'POST':
        if str(request.user.profile.organisation_name) == 'CIVIS':
            model_choice = request.POST['model_choice_name']
            if model_choice == "sentence_model_card":
                sentence_model_form = SentenceModelForm(request=request)
                return render(request, './Venter/upload_file.html', {
                'file_form': sentence_model_form, 'successful_submit': False, 'model_choice': model_choice})
            elif model_choice == "keyword_model_card":
                keyword_model_form = KeywordModelForm(request=request)
                return render(request, './Venter/upload_file.html', {
                    'file_form': keyword_model_form, 'successful_submit': False, 'model_choice': model_choice})
    elif request.method == 'GET':
        return render(request, './Venter/choose_model.html', {
            'successful_submit': False})

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
    paginate_by = 13

    def get_queryset(self):
        result = Category.objects.filter(organisation_name=self.request.user.profile.organisation_name)
        query = self.request.GET.get('q', '')
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
                          {'profile_form': profile_form, 'successful_submit': False})

    def get(self, request, *args, **kwargs):
        profile_form = ProfileForm(instance=request.user.profile)
        return render(request, './Venter/update_profile.html', {'profile_form': profile_form, 'successful_submit': False})


class RegisterEmployeeView(LoginRequiredMixin, CreateView):
    """
    Arguments------
        1) CreateView: View to register a new user(employee) of an organisation.
        2) LoginRequiredMixin: Request to register employees by non-authenticated users,
        will throw an HTTP 404 error
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
                # permission = Permission.objects.get(
                #     name='Can view files uploaded by self')
                # user_obj.user_permissions.add(permission)
                profile = Profile.objects.create(
                    user=user_obj, organisation_name=org_name)
                profile.save()
                user_form = UserForm()
                return render(request, './Venter/registration.html',
                              {'user_form': user_form, 'successful_submit': True})
            except ValidationError as e:
                user_form.add_error('password', e)
                return render(request, './Venter/registration.html', {'user_form': user_form, 'successful_submit': False})
        else:
            return render(request, './Venter/registration.html', {'user_form': user_form, 'successful_submit': False})

    def get(self, request, *args, **kwargs):
        user_form = UserForm()
        return render(request, './Venter/registration.html', {'user_form': user_form, 'successful_submit': False})


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
            first_name = contact_form.cleaned_data.get('first_name')
            last_name = contact_form.cleaned_data.get('last_name')
            company_name = contact_form.cleaned_data.get('company_name')
            designation = contact_form.cleaned_data.get('designation')
            city = contact_form.cleaned_data.get('city')
            contact_no = contact_form.cleaned_data.get('contact_no')
            email_address = contact_form.cleaned_data.get('email_address')
            detail_1 = contact_form.cleaned_data.get('detail_1')
            detail_2 = contact_form.cleaned_data.get('detail_2')
            detail_3 = contact_form.cleaned_data.get('detail_3')

            # get current date and time
            now = datetime.datetime.now()
            date_time = now.strftime("%Y-%m-%d %H:%M")

            # prepare email body
            email_body = "Dear Admin,\n\n Following are the inquiry details:\n\n " + \
                "Inquiry Date and Time: "+date_time+"\n First Name: " + \
                first_name+"\n Last Name: "+last_name+"\n Company Name: " + \
                company_name+"\n Designation: "+designation+"\n City: "+ \
                city+"\n Contact Number: "+contact_no+"\n Email ID: " + \
                email_address+"\n Business your organisation is engaged in: " + \
                detail_1+"\n Relevance of your business to Venter Product: " + \
                detail_2+"\n How do you think Venter can help your business?" + \
                detail_3+"\n\n"

            admin_list = User.objects.filter(is_superuser=True)
            for admin in admin_list:
                s = (admin.username, admin.email)
                ADMINS.append(s)

            mail_admins('Venter Inquiry', email_body)
            # contact_form.save()
            contact_form = ContactForm()
            return render(request, './Venter/contact_us.html', {
                'contact_form': contact_form, 'successful_submit': True})
    return render(request, './Venter/contact_us.html', {
        'contact_form': contact_form, 'successful_submit': False
    })

def request_demo(request):
    """
    View logic to email the administrator the contact details submitted by an organisation requesting demo.
    The contact details are submitted through the 'request_demo' template form.

    For POST request-------
        The contact details of an organisation are collected in the ContactForm.
        If the form is valid, an email is sent to the website administrator.
    For GET request-------
        The request_demo template is rendered
    """
    contact_form = ContactForm()

    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            first_name = contact_form.cleaned_data.get('first_name')
            last_name = contact_form.cleaned_data.get('last_name')
            company_name = contact_form.cleaned_data.get('company_name')
            designation = contact_form.cleaned_data.get('designation')
            city = contact_form.cleaned_data.get('city')
            contact_no = contact_form.cleaned_data.get('contact_no')
            email_address = contact_form.cleaned_data.get('email_address')
            detail_1 = contact_form.cleaned_data.get('detail_1')
            detail_2 = contact_form.cleaned_data.get('detail_2')
            detail_3 = contact_form.cleaned_data.get('detail_3')

            # get current date and time
            now = datetime.datetime.now()
            date_time = now.strftime("%Y-%m-%d %H:%M")

            # prepare email body
            email_body = "Dear Admin,\n\n Following are the inquiry details:\n\n " + \
                "Inquiry Date and Time: "+date_time+"\n First Name: " + \
                first_name+"\n Last Name: "+last_name+"\n Company Name: " + \
                company_name+"\n Designation: "+designation+"\n City: "+ \
                city+"\n Contact Number: "+contact_no+"\n Email ID: " + \
                email_address+"\n Business your organisation is engaged in: " + \
                detail_1+"\n Relevance of your business to Venter Product: " + \
                detail_2+"\n How do you think Venter can help your business?" + \
                detail_3+"\n\n"

            admin_list = User.objects.filter(is_superuser=True)
            for admin in admin_list:
                s = (admin.username, admin.email)
                ADMINS.append(s)

            mail_admins('Venter Inquiry', email_body)
            contact_form = ContactForm()
            return render(request, './Venter/request_demo.html', {
                'contact_form': contact_form, 'successful_submit': True})
    return render(request, './Venter/request_demo.html', {
        'contact_form': contact_form, 'successful_submit': False
    })

class AddProposalView(LoginRequiredMixin, CreateView):
    """
    Arguments------
        1) CreateView: View to add proposal by a CIVIS organisation_admin only.
        2) LoginRequiredMixin: Request to add proposal by non-authenticated users,
        will throw an HTTP 404 error
    For POST request-------
        The proposal details are validated in the ProposalForm, DomainForm and saved in the Proposal, Domain, Keyword model.
        If the user clicks on 'Save and add another domain' button, the domain-keyword dictionary is saved against an existing proposal name.
    For GET request-------
        The add_proposal template is rendered
    """
    model = Proposal

    def post(self, request, *args, **kwargs):
        proposal_form = ProposalForm(request.POST)
        domain_form = DomainForm(request.POST)

        proposal_name = request.POST['proposal_name']
        domain_name = request.POST['domain_name']
        temp_keyword_list = json.loads(request.POST['keyword_list'])
        temp_final_submit = request.POST['final_submit']
        temp_one_save_operation = request.POST['one_save_operation']

        if temp_final_submit == "true":
            final_submit = True
        elif temp_final_submit == "false":
            final_submit = False

        if temp_one_save_operation == "True":
            one_save_operation = True
        elif temp_one_save_operation == "False":
            one_save_operation = False

        if not one_save_operation:
            proposal_form = ProposalForm(request.POST)
            proposal_valid = proposal_form.is_valid()
            if proposal_valid:
                proposal_name = proposal_form.cleaned_data['proposal_name']
                proposal_obj = Proposal.objects.create(proposal_name=proposal_name)
                proposal_obj.save()

                domain_obj = Domain.objects.create(
                    proposal_name=proposal_obj, domain_name=domain_name)
                domain_obj.save()
            else:
                return render(request, './Venter/add_proposal.html',
                              {'proposal_form': proposal_form, 'domain_form': domain_form, 'one_save_operation': False})
        else:
            proposal_obj = Proposal.objects.get(proposal_name=proposal_name)

            try:
                domain_obj = Domain.objects.create(proposal_name=proposal_obj, domain_name=domain_name)
            except IntegrityError as e:
                domain_form.add_error('domain_name', 'Domain for this Domain name already exists')
                return render(request, './Venter/add_proposal.html',
                              {'proposal_form': proposal_form, 'domain_form': domain_form, 'one_save_operation': True, 'proposal_name': proposal_name})

        keyword_list = []
        for temp1 in temp_keyword_list:
            temp2 = temp1.lstrip()
            temp3 = temp2.rstrip()
            keyword_list.append(temp3)

        keyword_list.sort()

        for keyword in keyword_list:
            keyword_obj = Keyword.objects.create(
                domain_name=domain_obj, keyword=keyword)
            keyword_obj.save()

        proposal_form = ProposalForm()
        domain_form = DomainForm()

        if final_submit:
            return render(request, './Venter/add_proposal.html',
                          {'domain_form': domain_form, 'final_submit': final_submit, 'one_save_operation': True})
        else:
            return render(request, './Venter/add_proposal.html',
                    {'proposal_form': proposal_form, 'domain_form': domain_form, 'final_submit': final_submit, 'one_save_operation': True, 'proposal_name': proposal_name})

    def get(self, request, *args, **kwargs):
        proposal_form = ProposalForm()
        domain_form = DomainForm()
        keyword_form = KeywordForm()

        if request.is_ajax():
            domain_paragraph = request.GET.get('domain_paragraph')
            domain_paragraph = domain_paragraph.replace('\n', ' ')
            domain_paragraph_sentence_list = []
            domain_paragraph_sentence_list = tokenize.sent_tokenize(domain_paragraph)

            keyword_list = []
            keyword_list = generate_keywords(domain_paragraph_sentence_list)
        
            keyword_dropdown = ["keyword one", "keyword two", "keyword three", "keyword four", "keyword five", "keyword six"]
            return render(request, './Venter/proposal_keyword_data.html',
                            {'keyword_list': keyword_list, 'keyword_dropdown': keyword_dropdown})
        return render(request, './Venter/add_proposal.html',
                            {'proposal_form': proposal_form, 'domain_form': domain_form, 'keyword_form': keyword_form, 'one_save_operation': False})

@require_http_methods(["GET"])
def about_us(request):
    """
    View logic to display Venter product details, its impact, information on organisations associated with Venter.

    For GET request-------
        The about_us template is rendered
    """
    return render(request, './Venter/about_us.html')


class FileDeleteView(LoginRequiredMixin, DeleteView):
    """
    Arguments------
        1) LoginRequiredMixin: View to redirect non-authenticated users to show HTTP 403 error
        3) DeletView: View to delete file(s) uploaded

    Functions------
        1) get: Returns a new Queryset of files uploaded by user(s)/staff member(s) of the organisation
    """
    model = File
    success_url = reverse_lazy('dashboard')

    def get(self, request, *args, **kwargs):
        if request.user.is_staff:
            return self.post(request, *args, **kwargs)
        else:
            rendered = render_to_string('./Venter/401.html')
            return HttpResponse(rendered, status=401)


class FileListView(LoginRequiredMixin, ListView):
    """
    Arguments------
        1) LoginRequiredMixin: View to redirect non-authenticated users to show HTTP 403 error
        3) ListView: View to display file(s) uploaded

    Functions------
        1) get_queryset():
        For a user, returns the files uploaded by the logged-in employee
        For a staff member, returns the files uploaded by user(s)/staff member(s) of the organisation
    """
    model = File
    template_name = './Venter/dashboard.html'
    context_object_name = 'file_list'
    paginate_by = 8

    def get_queryset(self):
        if self.request.user.is_staff:
            result = File.objects.filter(
                uploaded_by__organisation_name=self.request.user.profile.organisation_name)
        elif not self.request.user.is_staff and self.request.user.is_active:
            result = File.objects.filter(uploaded_by=self.request.user.profile)

        query = self.request.GET.get('q', '')
        if query:
            result = [file_obj for file_obj in result if query in file_obj.filename.lower()]
        return result

@login_required
@require_http_methods(["GET", "POST"])
def predict_result(request, pk):
    """
    View logic for running CIVIS Prediction Model on files uploaded by CIVIS users.
    If the input file is being predicted for the first time:
        1) Two output files (.json and .xlsx files are created in file storage)
        2) Input file path is feed into the SimilarityMapping method of ML model
        3) dict_data stores the result json response returned from the ML model
        4) prediction_results.html template is rendered
    If the input file has already been predicted once:
        1) dict_data stores the result json data from the results.json file already created from the ML model
        2) prediction_results.html template is rendered
    """

    filemeta = File.objects.get(pk=pk)
    if not filemeta.has_prediction:
        output_directory_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output')
        if not os.path.exists(output_directory_path):
            os.makedirs(output_directory_path)

        temp1 = filemeta.filename
        temp2 = os.path.splitext(temp1)
        custom_input_file_name = temp2[0]
        
        output_json_file_name = 'results__'+custom_input_file_name+'.json'
        output_xlsx_file_name = 'results__'+custom_input_file_name+'.xlsx'
 
        output_file_path_json = os.path.join(output_directory_path, output_json_file_name)
        output_file_path_xlsx = os.path.join(output_directory_path, output_xlsx_file_name)

        dict_data = {}
        domain_list = []

        # prediction_result = tasks.predict_runner.delay(filemeta.input_file.path)
        # dict_data = prediction_result.get()

        model_choice = filemeta.model_choice
        if model_choice == 'sentence_model':
            sm = SimilarityMapping(filemeta.input_file.path)
        elif model_choice == 'keyword_model':
            if filemeta.domain_present:
                domain_present = True
            else:
                domain_present = False

            proposal = filemeta.proposal
            domain_queryset = Domain.objects.filter(proposal_name = proposal).values_list('domain_name', flat=True)
            domain_set = set(domain_queryset)
            domain_list = list(domain_set)

            domain_queryset_2 = Domain.objects.filter(proposal_name = proposal)
            keyword_global_list = []
            for domain_obj in domain_queryset_2:
                keyword_queryset = Keyword.objects.filter(domain_name = domain_obj).values_list('keyword', flat=True)
                keyword_set = set(keyword_queryset)
                keyword_list = list(keyword_set)
                keyword_global_list.append(keyword_list)

            domain_keyword_dict = {}
            domain_keyword_dict = dict(zip(domain_list, keyword_global_list))

            # domain_keyword_dict = {
            # 'hw': ['bedbugs', 'cctv', 'pipeline', 'Open spaces', 'gutter', 'garbage',
            #             'rats', 'mice', 'robbery', 'theft', 'passage', 'galli', 'lane',
            #             'light', 'bathrooms not clean', 'toilets not clean', 'playarea', 'mosquito', 'fogging','water'],
            # }

            sm = KeywordSimilarityMapping(filemeta.input_file.path, domain_present, domain_keyword_dict)
    
        dict_data = sm.driver()

        if model_choice == 'sentence_model':
            dirPath = os.path.join(BASE_DIR, "Venter/ML_model/sentence_model/data/comments")
        elif model_choice == 'keyword_model':
            dirPath = os.path.join(BASE_DIR, "Venter/ML_model/keyword_model/data/keyword data")
        fileList = os.listdir(dirPath)
        for fileName in fileList:
            os.remove(dirPath+"/"+fileName)

        if dict_data:
            filemeta.has_prediction = True

        with open(output_file_path_json, 'w') as temp:
            json.dump(dict_data, temp)

        print('JSON output saved.')
        print('Done.')

        filemeta.output_file_json = output_file_path_json

        download_output = pd.ExcelWriter(output_file_path_xlsx, engine='xlsxwriter')

        for domain, cat_dict in dict_data.items():
            domain_columns = list(cat_dict.keys())
            subdomain_columns = ['response', 'score']
            temp_column_index = 0
            codes = []
            subcodes = []

            for dc in domain_columns:
                codes.append(temp_column_index)
                codes.append(temp_column_index)
                subcodes.append(0)
                subcodes.append(1)
                temp_column_index += 1
            multiIndex = pd.MultiIndex(levels = [domain_columns, subdomain_columns], labels = [codes, subcodes])

            df = pd.DataFrame(columns=multiIndex)

            temp_responses = []
            temp_scores = []

            for cat_as_key, res_dict_list in cat_dict.items():
                temp_df_res = []
                temp_df_score = []

                if cat_as_key!='Novel':
                    for res_dict in res_dict_list:
                        temp_df_res.append(res_dict['response'])
                        temp_df_score.append(res_dict['score'])
                else:
                    for res_list in res_dict_list.values():
                        temp_df_res.extend(res_list)
                    for response in temp_df_res:
                        temp_df_score.append(-1)

                temp_responses.append(temp_df_res)
                temp_scores.append(temp_df_score)

            del temp_df_res, temp_df_score

            len_holder = sorted(temp_responses, key=len, reverse=True)
            len_holder = len(len_holder[0])
            weighted_temp_responses = []
            weighted_temp_scores = []

            for temp_df_res, temp_df_score in zip(temp_responses, temp_scores):
                for x in range(len_holder - len(temp_df_score)):
                    temp_df_res.append('')
                    temp_df_score.append('')
                weighted_temp_responses.append(temp_df_res)
                weighted_temp_scores.append(temp_df_score)

            del temp_responses, temp_scores, temp_df_res, temp_df_score
            for cat_as_key, temp_df_res, temp_df_score in zip(cat_dict.keys(), weighted_temp_responses, weighted_temp_scores):
                    df[cat_as_key, 'response'] = temp_df_res
                    df[cat_as_key, 'score'] = temp_df_score
            if model_choice == "keyword_model":
                for cat_as_key in cat_dict.keys():
                    df.drop([(cat_as_key, 'score')], axis=1, inplace=True)
            df.to_excel(download_output, sheet_name=domain)
        download_output.save()

        filemeta.output_file_xlsx = output_file_path_xlsx
        filemeta.save()
    else:
        temp1 = filemeta.filename
        temp2 = os.path.splitext(temp1)
        custom_input_file_name = temp2[0]
        
        output_json_file_name = 'results__'+custom_input_file_name+'.json'
        results = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output/{output_json_file_name}')

        with open(results, 'r') as content:
            dict_data = json.load(content)

    dict_keys = dict_data.keys()
    domain_list = list(dict_keys)
    domain_data = {}

    for domain_name in domain_list:
        domain_data = dict_data[domain_name]
        temp = ['Category']
        model_choice = filemeta.model_choice
        if model_choice == 'sentence_model':
            if 'Novel' in domain_data.keys():
                index = 0
                for subCat in domain_data['Novel']:
                    temp.append('Sub category ' + str(index+1))
                    index += 1
        elif model_choice == 'keyword_model':
            temp.append('No. of Responses')            
        temp.append({'role': 'style'})
        domain_stats = []
        domain_stats.append(temp)

        for category, responselist in domain_data.items():
            category = category.split('\n')[0]
            if model_choice == 'sentence_model':
                column = [category, len(responselist), '']
                if category == 'Novel':
                        column = ['Novel']
                        for subCat in domain_data[category]:
                            column.append(len(domain_data[category][subCat]))
                        column.append('')
                else:
                    for i in range(len(domain_stats[0]) - len(column)):
                        column.insert(2, 0)
                domain_stats.append(column)
            elif model_choice == 'keyword_model':
                if(len(responselist)!=0):
                    column = [category, len(responselist), '']
                    if category == 'Novel':
                        column = ['Novel']
                        for subCat in domain_data[category]:
                            column.append(len(domain_data[category][subCat]))
                        column.append('')
                    else:
                        for i in range(len(domain_stats[0]) - len(column)):
                            column.insert(2, 0)
                    domain_stats.append(column)

        dict_data[domain_name]['Statistics'] = jsonpickle.encode(domain_stats)

    if request.is_ajax():
        domain = request.GET.get('domain_name')
        cardview_data = dict_data[domain]
            
        if 'category' in request.GET:
            category = request.GET.get('category')
            print(type(category))
        else:
            for key in cardview_data.items():
                category = key
                break
                
        return render(request, './Venter/domain_data.html', {'cardview_data':cardview_data, 'category': category, 'filemeta': filemeta})

    return render(request, './Venter/prediction_result.html', {
        'domain_list': domain_list, 'dict_data': json.dumps(dict_data), 'filemeta': filemeta
    })

@login_required
@require_http_methods(["GET", "POST"])
def predict_csv(request, pk):
    """
    View logic for running ICMC Prediction Model on files uploaded by ICMC users.
    If the input file is being predicted for the first time:
        1) Two output files (.json and .csv files are created in file storage)
        2) Input file path is feed into the get_top_3_cats_with_prob method of ML model
        3) dict_data stores the result json response returned from the ML model
        4) prediction_table.html template is rendered
    If the input file has already been predicted once:
        1) dict_data stores the result json data from the results.json file already created from the ML model
        2) prediction_table.html template is rendered
    """
    filemeta = File.objects.get(pk=pk)

    if not filemeta.has_prediction:
        output_directory_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output')
        if not os.path.exists(output_directory_path):
            os.makedirs(output_directory_path)

        temp1 = filemeta.filename
        temp2 = os.path.splitext(temp1)
        custom_input_file_name = temp2[0]
        
        output_json_file_name = 'results__'+custom_input_file_name+'.json'
        output_csv_file_name = 'results__'+custom_input_file_name+'.csv'

        output_file_path_json = os.path.join(output_directory_path, output_json_file_name)
        output_file_path_csv = os.path.join(output_directory_path, output_csv_file_name)
        
        input_file_path = filemeta.input_file.path
        csvfile = pd.read_csv(input_file_path, sep=',', header=0, encoding='utf-8-sig')
        csvfile.columns = [col.strip() for col in csvfile.columns]

        complaint_description = list(csvfile['complaint_description'])
        ward_name = list(csvfile['ward_name'])
        ward_list = list(set(ward_name))

        date_created = []

        for x in list(csvfile['complaint_created']):
            y = x.split(' ')[0]
            date_created.append(y)
        date_list = list(set(date_created))

        dict_list = []
        unsorted_dict_list = []

        if str(request.user.profile.organisation_name) == 'ICMC':
            model = ClassificationService()
        elif str(request.user.profile.organisation_name) == "SpeakUp":
            pass

        cats = model.get_top_3_cats_with_prob(complaint_description)

        for row, complaint, scores, ward, date in zip(csvfile.iterrows(), complaint_description, cats, ward_name, date_created):
            row_dict = {}
            index, data = row
            row_dict['index'] = index

            if str(request.user.profile.organisation_name) == "ICMC":
                row_dict['problem_description'] = complaint
                row_dict['category'] = scores
                row_dict['highest_confidence'] = list(row_dict['category'].values())[0]
                row_dict['ward_name'] = ward
                row_dict['date_created'] = date
            else:
                continue
                # data = data.dropna(subset=["text"])
                # complaint_description = data['text']
                # cats = model.get_top_3_cats_with_prob(complaint_description)
            dict_list.append(row_dict)
        unsorted_dict_list = dict_list
        dict_list = sorted(dict_list, key=lambda k: k['highest_confidence'], reverse=True)

        if dict_list:
            filemeta.has_prediction = True

        with open(output_file_path_json, 'w') as temp:
            json.dump(unsorted_dict_list, temp)
        print('JSON output saved.')
        print('Done.')

        with open(input_file_path, 'r', encoding="utf-8-sig") as f1:
            with open(output_file_path_csv, 'w', encoding="utf-8-sig") as f2:
                for line in f1:
                    f2.write(line)

        output_csv_file = pd.read_csv(output_file_path_csv, sep=',', header=0)
        original_category_list = []
        temp_cat_list = []
        for item in unsorted_dict_list:
            temp_cat_list = list(item['category'].keys())
            del temp_cat_list[1:]
            original_category_list.append(temp_cat_list)

        output_csv_file.insert(0, "Predicted_Category", original_category_list)
        output_csv_file.to_csv(output_file_path_csv, index=False)

        filemeta.output_file_json = output_file_path_json
        filemeta.output_file_xlsx = output_file_path_csv
        filemeta.save()
    else:
        # dict_list = json.load(filemeta.output_file_json)
        temp1 = filemeta.filename
        temp2 = os.path.splitext(temp1)
        custom_input_file_name = temp2[0]
        
        output_json_file_name = 'results__'+custom_input_file_name+'.json'
        results =  os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output/{output_json_file_name}')

        with open(results,'r') as content:
            dict_list=json.load(content)

        if filemeta.file_saved_status:
            temp_list = []
            custom_category_list = []
            temp1 = filemeta.filename
            temp2 = os.path.splitext(temp1)
            custom_input_file_name = temp2[0]
            output_json_file_name = 'results__'+custom_input_file_name+'.csv'
            output_file_path_xlsx = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output/{output_json_file_name}')
            output_xlsx_csv_file = pd.read_csv(output_file_path_xlsx, sep=',', header=0, encoding='utf-8-sig')
            temp_list = output_xlsx_csv_file['Predicted_Category']

            for item in temp_list:
                item = literal_eval(item)
                custom_category_list.append(item)

            for item, cat in zip(dict_list, custom_category_list):
                item['category'] = cat
                
        dict_list = sorted(dict_list, key=lambda k: k['highest_confidence'], reverse=True)

    # preparing ward list and date list for multi-filter widget
    input_file_path = filemeta.input_file.path
    input_csv_file = pd.read_csv(input_file_path, sep=',', header=0, encoding='utf-8-sig')
    input_csv_file.columns = [col.strip() for col in input_csv_file.columns]

    date_created = []
    for x in list(input_csv_file['complaint_created']):
        y = x.split(' ')[0]
        date_created.append(y)

    date_list = list(set(date_created))
    ward_name = list(input_csv_file['ward_name'])
    ward_list = list(set(ward_name))

    # preparing category list based on organisation name
    if str(request.user.profile.organisation_name) == 'ICMC':
        category_queryset = Category.objects.filter(organisation_name='ICMC').values_list('category', flat=True)
        category_list = list(category_queryset)
    elif str(request.user.profile.organisation_name) == 'SpeakUp':
        category_queryset = Category.objects.filter(organisation_name='SpeakUp').values_list('category', flat=True)
        category_list = list(category_queryset)
    return render(request, './Venter/prediction_table.html', {'dict_list': dict_list, 'category_list': category_list, 'filemeta': filemeta, 'ward_list': ward_list, 'date_list': date_list})

@login_required
@require_http_methods(["POST"])
def download_table(request, pk):
    """
    View logic to prepare a .csv output file for files uploaded by ICMC users
        1) category_rec stores a two-dimensional list for all the custom categories selected by the user
        2) If 'Predicted_Category' column exists in results.csv file, it is dropped
        3) New category list is populated in the results.csv file and results.csv file is saved in the database
        4) Predicted_table template is rendered and user downloads the results.csv file(from dashboard.html)
    """
    filemeta = File.objects.get(pk=pk)
    sorted_category_list = json.loads(request.POST['sorted_category'])

    status = request.POST['file_saved_status']
    new_sorted_category_list = []

    for temp1 in sorted_category_list:
        # temp1 = [re.split(r"([\(])", x)[0] for x in sublist]
        temp2 = [x.lstrip() for x in temp1]
        temp3 = [x.rstrip() for x in temp2]
        new_sorted_category_list.append(temp3)

    temp1 = filemeta.filename
    temp2 = os.path.splitext(temp1)
    custom_input_file_name = temp2[0]
    
    output_json_file_name = 'results__'+custom_input_file_name+'.csv'
    output_csv_file_path =  os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output/{output_json_file_name}')   

    # output_csv_file_path = filemeta.output_file_xlsx.path
    csv_file = pd.read_csv(output_csv_file_path, sep=',', header=0, encoding='utf-8-sig')

    if status == "True":
        filemeta.file_saved_status = True
        if 'Predicted_Category' in csv_file.columns:
            csv_file = csv_file.drop("Predicted_Category", axis=1)
        csv_file.insert(0, "Predicted_Category", new_sorted_category_list)

    csv_file.to_csv(output_csv_file_path, index=False, encoding='utf-8-sig')

    filemeta.output_file_xlsx = output_csv_file_path
    filemeta.save()
    return HttpResponseRedirect(reverse('predict_csv', kwargs={"pk": filemeta.pk}))


@login_required
@require_http_methods(["GET", "POST"])
def wordcloud(request, pk):
    """
    View logic to display wordcloud for category selected frmo dropdown list(wordcloud template)
        1) The categories for a particular domain are populated in the dropdown widget (in wordcloud template)
    """
    filemeta = File.objects.get(pk=pk)
    wordcloud_category_list = []

    if request.method == 'POST':
        if str(request.user.profile.organisation_name) == 'CIVIS':
            domain_name = request.POST['wordcloud_domain_name']

            temp1 = filemeta.filename
            temp2 = os.path.splitext(temp1)
            custom_input_file_name = temp2[0]
            
            output_json_file_name = 'results__'+custom_input_file_name+'.json'
            results = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output/{output_json_file_name}')

            with open(results, 'r') as content:
                dict_data =json.load(content)

            domain_data = dict_data[domain_name]
            for category, category_dict in domain_data.items():
                wordcloud_category_list.append(category)
            wordcloud_category_list = wordcloud_category_list[:-1]
        return render(request, './Venter/wordcloud.html', {'category_list': wordcloud_category_list, 'filemeta': filemeta, 'domain_name': domain_name})
    else:
        if str(request.user.profile.organisation_name) == 'ICMC':
            category_queryset = Category.objects.filter(organisation_name='ICMC').values_list('category', flat=True)
            wordcloud_category_list = list(category_queryset)
        return render(request, './Venter/wordcloud.html', {'category_list': wordcloud_category_list, 'filemeta': filemeta})

@login_required
@require_http_methods(["POST"])
def wordcloud_contents(request, pk):
    """
        View logic to display wordcloud for a set of responses belonging to a particular category
        1) For the category selected, the input json file is feed into the wordcloud algorithm
        2) The output dict 'words' is passed as a context variable to the wordcloud template
    """
    filemeta = File.objects.get(pk=pk)
    wordcloud_directory_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/wordcloud')
    if not os.path.exists(wordcloud_directory_path):
        os.makedirs(wordcloud_directory_path)

    temp1 = filemeta.filename
    temp2 = os.path.splitext(temp1)
    custom_input_file_name = temp2[0]
    
    wordcloud_data_file_name = 'wordcloud__'+custom_input_file_name+'.json'
    
    if str(request.user.profile.organisation_name) == 'ICMC':
        wordcloud_category_list = []

        temp1 = filemeta.filename
        temp2 = os.path.splitext(temp1)
        custom_input_file_name = temp2[0]
        
        output_json_file_name = 'results__'+custom_input_file_name+'.csv'
        output_file_path =  os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output/{output_json_file_name}')   

        # output_csv_file_path = filemeta.output_file_xlsx.path

        output_file = pd.read_csv(output_file_path, sep=',', header=0)
        temp_dict = defaultdict(list)
        for predicted_category_str, complaint_description in zip(output_file['Predicted_Category'], output_file['complaint_description']):
            predicted_category_list = literal_eval(predicted_category_str)
            if predicted_category_list:
                final_cat = predicted_category_list[0]
                final_cat = re.split(r"\(", final_cat)[0]
                final_cat = final_cat.strip(' ')

                if final_cat not in temp_dict:
                    response_list = []
                    response_list.append(complaint_description)
                    temp_dict[final_cat] = response_list
                else:
                    response_list = []
                    response_list.append(complaint_description)
                    temp_dict[final_cat].append(complaint_description)
            else:
                pass
        wordcloud_input_dict = dict(temp_dict)

        keys = ["garbage", "recreation park", "dumpster on road", "traffic near K.G road", "plant trees on pavement", "road conditions", "water pond"]
        values = [10, 90, 30, 20, 54, 45, 100]
        words = {}
        words = dict(zip(keys, values))

        category_queryset = Category.objects.filter(organisation_name='ICMC').values_list('category', flat=True)
        wordcloud_category_list = list(category_queryset)
        return render(request, './Venter/wordcloud.html', {'category_list': wordcloud_category_list, 'filemeta': filemeta, 'words': words})
    elif str(request.user.profile.organisation_name) == 'CIVIS':
        category_name = request.POST['category_name']
        domain_name = request.POST['domain_name']
        wordcloud_category_list = json.loads(request.POST['category_list'])

        temp1 = filemeta.filename
        temp2 = os.path.splitext(temp1)
        custom_input_file_name = temp2[0]
        
        output_json_file_name = 'results__'+custom_input_file_name+'.json'
        output_file_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output/{output_json_file_name}')   
        
        wordcloud_file_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/wordcloud/{wordcloud_data_file_name}')
        path = pathlib.Path(wordcloud_file_path)
        if path.exists():
            wordcloud_data_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/wordcloud/{wordcloud_data_file_name}')
            with open(wordcloud_data_path, 'r') as content:
                output_dict = json.load(content)
        else:
            wordcloud_data_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/wordcloud')
            wordcloud_data_path_json = os.path.join(wordcloud_data_path, wordcloud_data_file_name)
            output_dict = generate_wordcloud(output_file_path)

            with open(wordcloud_data_path_json, 'w') as temp:
                json.dump(output_dict, temp)

            filemeta.wordcloud_data = wordcloud_data_path_json
            filemeta.save()

        domain_items_list = output_dict[domain_name]
        words = {}

        for domain_item in domain_items_list:
            if list(domain_item.keys())[0].split('\n')[0].strip() == category_name.strip():
                words = list(domain_item.values())[0]

        for word, freq in words.items():
            if(word == 'items'):
                words['item'] = words.pop('items')
        temp_list = sorted(words.items())
        words = {}
        words = dict(temp_list)

        return render(request, './Venter/wordcloud.html', {'category_list': wordcloud_category_list, 'filemeta': filemeta, 'words': words, 'domain_name': domain_name, 'category_name': category_name})


@login_required
@require_http_methods(["POST"])
def chart_editor(request, pk):
    """
        View logic to display chart editor for the selected domain
    """
    filemeta = File.objects.get(pk=pk)
    dict_data = {}
    domain_list = []

    temp1 = filemeta.filename
    temp2 = os.path.splitext(temp1)
    custom_input_file_name = temp2[0]
    
    output_json_file_name = 'results__'+custom_input_file_name+'.json'
    results = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output/{output_json_file_name}')

    with open(results, 'r') as content:
        dict_data=json.load(content)
    # dict_data = json.load(filemeta.output_file_json)

    filemeta = File.objects.get(pk=pk)
    output_directory_path = os.path.join(MEDIA_ROOT, f'{filemeta.uploaded_by.organisation_name}/{filemeta.uploaded_by.user.username}/{filemeta.uploaded_date.date()}/output')

    if not os.path.exists(output_directory_path):
        os.makedirs(output_directory_path)

    temp1 = filemeta.filename
    temp2 = os.path.splitext(temp1)
    custom_input_file_name = temp2[0]
    output_json_file_name = 'results__'+custom_input_file_name+'.json'
    output_xlsx_file_name = 'results__'+custom_input_file_name+'.xlsx'

    output_file_path_json = os.path.join(output_directory_path, output_json_file_name)
    output_file_path_xlsx = os.path.join(output_directory_path, output_xlsx_file_name)

    filemeta.output_file_json = output_file_path_json
    filemeta.output_file_xlsx = output_file_path_xlsx
    filemeta.save()

    dict_keys = dict_data.keys()
    domain_list = list(dict_keys)
    domain_data = {}

    for domain_name in domain_list:
        domain_data = dict_data[domain_name]
        temp = ['Category']
        model_choice = filemeta.model_choice
        if model_choice == 'sentence_model':
            if 'Novel' in domain_data.keys():
                index = 0
                for subCat in domain_data['Novel']:
                    temp.append('Sub category ' + str(index+1))
                    index += 1
        elif model_choice == 'keyword_model':
            temp.append('No. of Responses')
        temp.append({'role': 'style'})
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
                    column.insert(2, 0)
            domain_stats.append(column)
        dict_data[domain_name]['Statistics'] = jsonpickle.encode(domain_stats)
        domain_name = request.POST['input_domain_name']
    return render(request, './Venter/chart_editor.html', {'filemeta': filemeta, 'domain_list': domain_list, 'dict_data': json.dumps(dict_data), 'domain_name': domain_name})
