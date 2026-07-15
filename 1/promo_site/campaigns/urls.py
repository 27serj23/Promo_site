from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('campaign/create/', views.create_campaign_view, name='create_campaign'),
    path('campaign/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('campaign/<int:campaign_id>/house/<int:house_id>/', views.house_detail, name='house_detail'),
    path('campaign/<int:campaign_id>/statistics/', views.campaign_statistics, name='campaign_statistics'),
]