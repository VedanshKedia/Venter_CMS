from django.contrib import admin

from Venter.models import Category, File, Header, Organisation, Profile


class HeaderAdmin(admin.ModelAdmin):
    list_display = ('organisation_name', 'header')
    list_filter = ['organisation_name']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('organisation_name', 'category')
    list_filter = ['organisation_name']

class FileAdmin(admin.ModelAdmin):
    list_display = ('uploaded_by', 'uploaded_date')
    list_filter = ['uploaded_date']

class ProfileAdmin(admin.ModelAdmin):
    verbose_name_plural = 'Employee Details'
    list_display = ('user', 'organisation_name', 'phone_number')

class OrganisationAdmin(admin.ModelAdmin):
    verbose_name_plural = 'Organisation Details'


admin.site.register(Header, HeaderAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Organisation, OrganisationAdmin)
