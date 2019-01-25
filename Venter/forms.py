from django.contrib.auth.models import User
from django import forms
from Venter.models import File, Profile

# class upload_file_form(forms.Form):
#     """
#     Author: Meet Shah, Shivam Sharma
#     Source:  This link helped me to write validation code
#              https://stackoverflow.com/questions/2472422/django-file-upload-size-limit
#     """
#     # The attrs is an in built parameter for the FileInput in the form.
#     file = forms.FileField(label='Choose CSV File', widget=forms.FileInput(attrs={'accept': ".csv", "id": "filename"}))

#     def clean_file(self):
#         content = self.cleaned_data['file']
#         filename = str(content)
#         max_size = int(settings.MAX_UPLOAD_SIZE)
#         upload_file_size = int(
#             content.size)  # This code might give a buffer error so find a good solution for this. Look at the source link for reference

#         # Validating the format of the file
#         if filename.endswith('.csv'):
#             # Check for the file size of the uploaded file with the max size (12 MB)
#             if upload_file_size > max_size:
#                 # Beware, the ugettext_lazy might not work for python 3.5 and below. It's better to use f strings with Python 3.6 and above. The latest version, the better.
#                 raise forms.ValidationError(f('Please keep file size under %s. Current file size is %s') % (
#                     filesizeformat(settings.MAX_UPLOAD_SIZE), filesizeformat(content.size))) # filesizeformat is an in built function. Check it's documentation
#         else:
#             raise forms.ValidationError(f('Please Upload Csv File Only !!!'))
#         return content


class CSVForm(forms.ModelForm):
    """
    ModelForm, used to facilitate CSV file upload.

    Validation checks made for each csv file: type, size, row count, headers.

    Usage:
        1) upload_file.html template: Generates the file form fields in the csv file upload page for logged in users.
    """
    class Meta:
        model = File
        fields = ('csv_file', 'file_name')

        # check file extension .csv
        # check file size 5MB or less
        # check file row count (1000 rows or whatever required)
        # header validation --> code written in script.py for reference
        # then upload the csv file


class UserForm(forms.ModelForm):
    """
    Modelform, generated from Django's user model.

    Usage------
        1) 'registration.html' template: Generates the user form fields in the signup page for new users.
        2) 'update_profile.html' template: Generates the user form fields in the update profile page for existing users.
    """
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')

    def save(self): # pylint: disable = W0221
        user = super(UserForm, self).save(commit=False)
        password = self.cleaned_data.get('password')
        user.set_password(password)
        user.save()
        return user


class ProfileForm(forms.ModelForm):
    """
    Modelform, generated from Django's Profile model.

    Usage------
        1) 'registration.html' template: Generates the profile form fields in the signup page for new users.
        2) 'update_profile.html' template: Generates the profile form fields in the update profile page for existing users.
    """
    class Meta:
        model = Profile
        fields = ('organisation_name', 'phone_number', 'profile_picture')
