"""Form fields validation

This script performs validation of several form fields that require substantial LOC

This python file can be imported and contains the following
functions:
    1) input_file_header_validation - returns boolean result from csv file header validation
"""

from Venter.models import Header

def input_file_header_validation(uploaded_input_file, request):
    """
    Validation of the header list extracted from the csv file's first row
    against the header list of the logged-in user's organisation
    """

    # extracting and converting the header from bytes to string format
    csv_header = uploaded_input_file.readline()
    csv_str = str(csv_header, encoding='utf-8')

    # converting the headers from string to list using comma separated delimiters
    csv_list = csv_str.split(',')

    # strip() function executes over each item of csv_list to remove all the leading and trailing whitespaces
    # this should normalise all the header categories with whitespaces in them
    # then we cast the list to a set to allow us to validate it with the organisation's header list
    csv_stripped_list = [item.strip() for item in csv_list]
    csv_set = set(csv_stripped_list)

    # obtaining the organisation name of the logged-in user
    org_name = request.user.profile.organisation_name

    # this retrieves the header list for a particular organisation and casts it to a set
    model_header_list = Header.objects.filter(
        organisation_name=org_name).values_list('header', flat=True)
    header_set = set(model_header_list)
    if csv_set == header_set:
        return True
    return False
