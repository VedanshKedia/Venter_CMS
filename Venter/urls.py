from django.contrib import auth
from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # ex: /venter/
    path('', TemplateView.as_view(template_name='Venter/home.html'), name='home'),
    # ex: /venter/home/
    path('home/', TemplateView.as_view(template_name='Venter/home.html'), name='home'),
    # ex: /venter/logout/
    # path('logout/', views.user_logout, name='logout'),
    path('logout/', auth.views.LogoutView.as_view(template_name="Venter/login.html"), name='logout'),
    # ex: /venter/update_profile/5/
    path('update_profile/<int:pk>', views.UpdateProfileView.as_view(), name='update_profile'),
    # ex: /venter/register_employee/
    path('register_employee/', views.RegisterEmployeeView.as_view(), name='register_employee'),
    # ex: /venter/login/
    path('login/', auth.views.LoginView.as_view(template_name="Venter/login.html"), name='login'),
    # ex: /venter/upload_file/
    path('upload_file/', views.upload_file, name='upload_file'),
    # ex: /venter/delete_file/5/
    path('delete_file/<int:pk>', views.FileDeleteView.as_view(), name='delete_file'),
    # ex: /venter/category_list/civis/
    path('category_list/<organisation_name>', views.CategoryListView.as_view(), name='category_list'),
    # ex: /venter/dashboard/
    path('dashboard/', views.FileListView.as_view(), name='dashboard'),
    # ex: /venter/contact_us/
    path('contact_us/', views.contact_us, name='contact_us'),
    # ex: /venter/search_category/
    # path('search_category/', views.CategorySearchView.as_view(), name='search_category'),
    # ex: /venter/search_file/
    # path('search_file/', views.FileSearchView.as_view(), name='search_file'),
    # ex: /venter/predict_result/5/
    path('predict_result/<int:pk>', views.predict_result, name='predict_result'),
    # ex: /venter/domain_contents/
    path('domain_contents/', views.domain_contents, name='domain_contents'),
    # path('predict/checkOutput/', views.handle_user_selected_data, name='checkOutput'),
    # ex: /venter/download_file/5/
    # path('download_file/<int:pk>', views.file_download, name='download_file'),
]
