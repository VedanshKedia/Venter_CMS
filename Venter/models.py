import os
from datetime import date, datetime

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.validators import RegexValidator
from django.db import models

from .helpers import get_file_upload_path, get_organisation_logo_path, get_user_profile_picture_path, get_result_file_path


class Organisation(models.Model):
    """
    An organisation that the user belongs to.
    Eg: user_1 belongs to xyz organisation

    # Create an organisation
    >>> organisation_1 = Organisation.objects.create(organisation_name="xyz", organisation_logo="image1.png")
    >>> organisation_2 = Organisation.objects.create(organisation_name="abc", additional_details="Mumbai based company")
    """
    organisation_name = models.CharField(
        max_length=200,
        primary_key=True,
    )
    organisation_logo = models.ImageField(
        upload_to=get_organisation_logo_path,
        null=True,
        blank=True,
        verbose_name="Organisation Logo"
    )
    additional_details = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.organisation_name


class Profile(models.Model):
    """
    A Profile associated with an existing user.
    Eg: organisation name and phone number are some profile details associated with user_1

    # Create a user profile
    >>> prof_1 = Profile.objects.create(user=user_1, organisation_name="abc", profile_picture="image2.png")
    >>> prof_2 = Profile.objects.create(user=user_2, organisation_name="abc", phone_number="9898121212")
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True
    )
    organisation_name = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        null=True,
    )
    profile_picture = models.ImageField(
        upload_to=get_user_profile_picture_path,
        null=True,
        blank=True,
        default='User Profile Picture/default-avatar.png'
    )
    phone_number = models.CharField(
        blank=True,
        max_length=10,
        validators=[RegexValidator(
            regex=r'^[6-9]\d{9}$', message='Please enter a valid phone number')]
    )
    def __str__(self):
        return self.user.username  # pylint: disable = E1101


class Header(models.Model):
    """
    A Header list associated with each organisation.
    Eg: Organisation xyz may contain headers in the csv file such as- user_id, title etc

    # Create a header instance
    >>> Header.objects.create(organisation_name="xyz", header="user_id")
    """
    organisation_name = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
    )
    header = models.CharField(
        max_length=200
    )

    class Meta:
        verbose_name_plural = 'Headers'


class Category(models.Model):
    """
    A Category list associated with each organisation.
    Eg: Organisation xyz may contain categories in the csv file such as- hawkers, garbage etc

    # Create a category instance
    >>> Category.objects.create(organisation_name="xyz", category="hawkers")
    """
    organisation_name = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
    )
    category = models.CharField(
        max_length=200
    )

    class Meta:
        verbose_name_plural = 'Category'


class File(models.Model):
    """
    A File uploaded by the logged-in user.
    Eg: user_1 may upload a .csv file on 12/12/12

    # Create a file instance
    >>> File.objects.create(uploaded_by=user_1, input_file="file1.csv", uploaded_date = "Jan. 29, 2019, 7:59 p.m.")

    Meta class------
        1) declares a plural name for the 'File' object

    Permissions------
        1) view_organisation_files: Grants permission only to staff members to access 'dashboard_staff.html' template
        2) view_self_files: Grants permission only to authenticated users to access 'dashboard_user.html' template
        2) delete_organisation_files: Grants permission only to staff members to delete files
            uploaded by user(s)/staff member(s) of the organisation
    """
    uploaded_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='file',
    )
    input_file = models.FileField(
        upload_to=get_file_upload_path
    )
    uploaded_date = models.DateTimeField(
        default=datetime.now,
    )
    has_prediction = models.BooleanField(
        default=False,
    )
    output_file_json = models.FileField(blank=True)
    output_file_xlsx = models.FileField(blank=True)

    @property
    def filename(self):
        """
        Returns the name of the csv file uploaded.
        Usage: dashboard_user.html template
        """
        return os.path.basename(self.input_file.name)  # pylint: disable = E1101
    @property
    def output_name(self):
        return os.path.basename(self.output_file.name)

    def delete(self):
        if self.output_file_json:
            default_storage.delete(self.output_file_json)
        if self.output_file_xlsx:
            default_storage.delete(self.output_file_xlsx)
        default_storage.delete(self.input_file)
        print("\n\nInput file should be gone\n\n")
        super().delete()

    class Meta:
        verbose_name_plural = 'File'
        ordering=["-uploaded_date"]
