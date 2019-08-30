import os
from django import forms
from django.contrib.auth.models import User
from django.core.validators import (EmailValidator, FileExtensionValidator,
                                    RegexValidator)

from Backend import settings
from Venter.models import Domain, File, Keyword, Profile, Proposal

from .validate import input_file_header_validation


class CSVForm(forms.ModelForm):
    """
    ModelForm, used to facilitate CSV file upload.

    Usage:
        1) upload_file.html template: Generates the file form fields in the csv file upload page for logged in users.
    """
    class Meta:
        """
        Meta class------
            1) declares 'File' as the model class to generate the 'file_form'
            2) includes only only field in the 'file_form 'from the File model
        """
        model = File
        fields = ('input_file',)

    def __init__(self, *args, **kwargs):
        """
        It accepts the self.request argument, here for the purpose of accessing the logged-in user's organisation name
        """
        self.request = kwargs.pop("request")
        super(CSVForm, self).__init__(*args, **kwargs)

    def clean_input_file(self):
        """
        It validates specific attributes of 'input_file' field: csv header, file type, and file size.
        """

        # cleaning and retrieving the uploaded csv file to perform further validation on it
        uploaded_input_file = self.cleaned_data['input_file']

        # checks for non-null file upload
        if uploaded_input_file:
            # validation of the filetype based on the extension type .csv
            # validation of the filesize based on the size limit 5MB
            # the input_file_header_validation() is invoked from validate.py
            filename = uploaded_input_file.name
            if filename.endswith(settings.FILE_UPLOAD_TYPE):
                if uploaded_input_file.size < int(settings.MAX_UPLOAD_SIZE):
                    if input_file_header_validation(uploaded_input_file, self.request):
                        return uploaded_input_file
                    else:
                        raise forms.ValidationError(
                            "Incorrect headers detected, please upload correct file")
                else:
                    raise forms.ValidationError(
                        "File size must not exceed 5 MB")
            else:
                raise forms.ValidationError(
                    "Please upload .csv extension files only")

            # if filename.endswith(settings.FILE_UPLOAD_TYPE):
            #     if input_file_header_validation(uploaded_input_file, self.request):
            #         return uploaded_input_file
            #     else:
            #         raise forms.ValidationError(
            #             "Incorrect headers detected, please upload correct file")
            # else:
            #     raise forms.ValidationError(
            #         "Please upload .csv extension files only")

        return uploaded_input_file


class SentenceModelForm(forms.ModelForm):
    """
    ModelForm, generated from Django's file model.
    """

    input_file = forms.FileField(
        widget=forms.FileInput(),
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['xlsx'])],
    )

    class Meta:
        """
        Meta class------
            1) declares 'File' as the model class to generate the 'file_upload_form'
            2) includes one field to check .xlsx file extension validation
        """
        model = File
        fields = ('input_file',)

    def __init__(self, *args, **kwargs):
        """
        It accepts the self.request argument, here for the purpose of accessing the logged-in user's organisation name
        """
        self.request = kwargs.pop("request")
        super(SentenceModelForm, self).__init__(*args, **kwargs)

class KeywordModelForm(forms.ModelForm):
    """
    ModelForm, generated from Django's file model.
    """
    CHOICES = ((True, 'Yes'), (False, 'No'))

    input_file = forms.FileField(
        widget=forms.FileInput(),
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['xlsx'])],
    )
    proposal = forms.ModelChoiceField(
        required=True,
        queryset=Proposal.objects.all(),
    )
    domain_present = forms.ChoiceField(
        widget=forms.RadioSelect,
        required=True,
        choices=CHOICES,
    )

    class Meta:
        """
        Meta class------
            1) declares 'File' as the model class to generate the 'file_upload_form'
            2) includes three fields to check .xlsx file extension validation; to add a proposal for the input file; to check domain flag
        """
        model = File
        fields = ('input_file', 'proposal', 'domain_present')

    def __init__(self, *args, **kwargs):
        """
        It accepts the self.request argument, here for the purpose of accessing the logged-in user's organisation name
        """
        self.request = kwargs.pop("request")
        super(KeywordModelForm, self).__init__(*args, **kwargs)


class UserForm(forms.ModelForm):
    """
    Modelform, generated from Django's user model.

    Note------
        CSS styling done per widget instance

    Usage------
        1) 'registration.html' template: Generates the user form fields in the signup page for new users
        2) 'update_profile.html' template: Generates the user form fields in the update profile page for existing users
    """
    class Meta:
        """
        Meta class------
            1) declares 'User' as the model class to generate the 'user_form'
            2) includes only five fields in the 'user_form' from the User model
        """
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Username', 'autofocus': 'autofocus'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password'}))
    email = forms.CharField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email'}))
    first_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Last Name'}))


class ProfileForm(forms.ModelForm):
    """
    Modelform, generated from Django's Profile model.

    Usage------
        1) 'registration.html' template: Generates the profile form fields in the signup page for new users
        2) 'update_profile.html' template: Generates the profile form fields in the update profile page
        for existing users
    """
    class Meta:
        """
        Meta class------
            1) declares 'Profile' as the model class to generate the 'profile_form'
            2) includes only three fields in the 'profile_form' from the Profile model
        """
        model = Profile
        fields = ('phone_number', 'profile_picture')

    profile_picture = forms.FileField(
        widget=forms.FileInput(),
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])],)

    def clean_profile_picture(self):
        uploaded_profile_picture = self.cleaned_data.get('profile_picture')
        if uploaded_profile_picture.size < int(settings.MAX_PROFILE_PICTURE_UPLOAD_SIZE):
            return uploaded_profile_picture
        else:
            raise forms.ValidationError(
                "Profile picture size must not exceed 1 MB")
        return uploaded_profile_picture

    def save(self, *args, **kwargs):
        """
        Update the primary profile picture on the related User object as well.
        """
        user_instance = self.instance.user
        image_path = user_instance.profile.profile_picture.name
        if os.path.isfile(image_path):
            os.remove(image_path)
        profile_instance = super(ProfileForm, self).save(*args, **kwargs)
        return profile_instance


class ContactForm(forms.Form):
    """
    Modelform containing custom widget controls.

    Usage------
        1) 'contact_us.html' template: Generates the contact form fields in the contact us page for public users
    """
    first_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'First Name', 'autofocus': 'autofocus'}), required=True,
                                 validators=[RegexValidator(regex=r'^[a-zA-Z\s]*$',
                                                            message='Please enter a valid first name')])
    last_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Last Name'}), required=True,
                                validators=[RegexValidator(regex=r'^[a-zA-Z\s]*$',
                                                           message='Please enter a valid last name')])
    company_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Company Name'}), required=True,
                                   validators=[RegexValidator(regex=r'^[a-zA-Z\s]*$',
                                                              message='Please enter a valid company name')])
    designation = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Designation'}), required=True,
                                  validators=[RegexValidator(regex=r'^[a-zA-Z\s]*$',
                                                             message='Please enter a valid designation')])
    city = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'City'}), required=True,
                           validators=[RegexValidator(regex=r'^[a-zA-Z\s]*$',
                                                      message='Please enter a valid city name')])
    email_address = forms.EmailField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Email'}), required=True, validators=[EmailValidator])
    contact_no = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Contact Number'}), required=True, max_length=10,
                                 validators=[RegexValidator(regex=r'^[6-9]\d{9}$',
                                                            message='Please enter a valid phone number')])
    detail_1 = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control'}), required=True)
    detail_2 = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control'}), required=True)
    detail_3 = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control'}), required=False)

class ProposalForm(forms.ModelForm):
    """
    Modelform, generated from Django's Proposal model.

    Note------
        CSS styling done per widget instance

    Usage------
        1) 'add_proposal.html' template: Generates the proposal form fields in the add proposal page for civis users
        2) includes only one field 'proposal_name' from the Proposal model (in models.py)
    """
    class Meta:
        """
        Meta class------
            1) declares 'Proposal' as the model class to generate the 'proposal_form'
        """
        model = Proposal
        fields = ('proposal_name',)
    proposal_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Proposal Name', 'autofocus': 'autofocus'}),
                                    validators=[RegexValidator(regex=r'^[\w\s]*$',
                                                               message='Proposal name may contain letters, digits, underscore and spaces only')])

class DomainForm(forms.ModelForm):
    """
    Modelform, generated from Django's Domain model.

    Note------
        CSS styling done per widget instance

    Usage------
        1) 'add_proposal.html' template: Generates the domain form fields in the add proposal page for civis users
        2) includes only one field 'proposal_name' from the Proposal model (in models.py)
    """
    class Meta:
        """
        Meta class------
            1) declares 'Domain' as the model class to generate the 'domain_form'
        """
        model = Domain
        fields = ('domain_name',)
    domain_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Add Domain name'}),
                                  validators=[RegexValidator(regex=r'^[a-zA-Z\s]*$',
                                                             message='Domain name can contain letters and spaces only')])

class KeywordForm(forms.ModelForm):
    """
    Modelform, generated from Django's Keyword model.

    Note------
        CSS styling done per widget instance

    Usage------
        1) 'add_proposal.html' template: Generates the keyword form fields in the add proposal page for civis users
        2) includes only one field 'keyword' from the Proposal model (in models.py)
    """
    class Meta:
        """
        Meta class------
            1) declares 'Keyword' as the model class to generate the 'keyword_form'
        """
        model = Keyword
        fields = ('keyword',)
    keyword = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Add Keyword'}),
                              validators=[RegexValidator(regex=r'^[a-zA-Z\s]*$',
                                                         message='Keyword can contain letters and spaces only')])
