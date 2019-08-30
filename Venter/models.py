import os
from datetime import datetime

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.validators import RegexValidator
from django.db import models

from .helpers import get_file_upload_path, get_organisation_logo_path, get_user_profile_picture_path


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
        default='default-avatar.png'
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
        """
        Declares a plural name for Header model
        """
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
        """
        Declares a plural name for Category model
        """
        verbose_name_plural = 'Category'


class Proposal(models.Model):
    """
    A proposal that belongs to one or more uploaded xlsx files (organisation: Civis only).

    # Create a Proposal
    >>> Proposal.objects.create(proposal_name="proposal 1")
    """
    proposal_name = models.CharField(
        max_length=200,
        primary_key=True,
    )

    def __str__(self):
        return self.proposal_name

class Domain(models.Model):
    """
    A Domain list associated with each proposal.
    Eg: Proposal xyz may contain domains in the xlsx file such as- water, parks etc

    # Create a category instance
    >>> Domain.objects.create(proposal_name="proposal_1", domain_name="Environment")
    """
    proposal_name = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
    )
    domain_name = models.CharField(
        max_length=200,
    )

    def __str__(self):
        return self.domain_name

    class Meta:
        """
        Declares a plural name for Domain model
        """
        verbose_name_plural = 'Domain'
        unique_together = ('proposal_name', 'domain_name',)

class Keyword(models.Model):
    """
    A Keyword list associated with each domain.
    Eg: Domain 'Environment' may contain keywords in the xlsx file such as- plant more trees in garden etc

    # Create a category instance
    >>> Keyword.objects.create(domain_name="Environment", keyword="plant more trees")
    """
    domain_name = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
    )
    keyword = models.CharField(
        max_length=200
    )

    def __str__(self):
        return self.keyword

    class Meta:
        """
        Declares a plural name for Domain model
        """
        verbose_name_plural = 'Keyword'


class File(models.Model):
    """
    A File uploaded by the logged-in user.
    Eg: user_1 may upload a .csv/.xlsx file on 12/12/12

    # Create a file instance
    >>> File.objects.create(uploaded_by=user_1, input_file="file1.csv", uploaded_date = "Jan. 29, 2019, 7:59 p.m.", has_prediction=False)
    """
    BOOL_CHOICES = ((True, 'Yes'), (False, 'No'))
    MODEL_CHOICES = (
        ('sentence_model', 'sentence_model'),
        ('keyword_model', 'keyword_model'),)

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
    file_saved_status = models.BooleanField(
        default=False,
    )
    domain_present = models.BooleanField(
        choices=BOOL_CHOICES,
        default=False,
    )
    model_choice = models.CharField(
        choices=MODEL_CHOICES,
        max_length=15,
        blank=True,
        null=True,
    )

    output_file_json = models.FileField(blank=True, max_length=255)
    output_file_xlsx = models.FileField(blank=True, max_length=255)
    wordcloud_data = models.FileField(blank=True, max_length=255)
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposal',
    )

    @property
    def filename(self):
        """
        Returns the name of the file uploaded.
        Usage: dashboard.html template
        """
        return os.path.basename(self.input_file.name)  # pylint: disable = E1101
    @property
    def output_name(self):
        """
        Returns the file path for output file to be created
        """
        return os.path.basename(self.output_file.name) # pylint: disable = E1101

    def delete(self):
        """
        Deletes json and xlsx/csv output files from file storage
        Usage: dashboard.html template (on click trash icon by Staff member)
        """
        if self.output_file_json:
            default_storage.delete(self.output_file_json)
        if self.output_file_xlsx:
            default_storage.delete(self.output_file_xlsx)
        default_storage.delete(self.input_file)
        super().delete()

    class Meta:
        """
        Displays recently uploaded files at the top of file list.
        Declares a plural name for File model
        Usage: dashboard.html template
        """
        verbose_name_plural = 'File'
        ordering = ["-uploaded_date"]
