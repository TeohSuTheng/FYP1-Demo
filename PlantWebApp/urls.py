from django.urls import path, include
from . import views


urlpatterns = [
    path('',views.home,name='home'),
    path('search-results/',views.displaySearchResults,name='display_SearchResults'),
    #path('search/',views.searchResultsAPI,name='searchResultsAPI'),
    path('form/',views.displayPlantForm,name='display_form'),
    path('glossary/',views.displayGlossary,name='display_glossary'),
    path('plant/<int:id>',views.displayPlant,name='display_plant'),
    path('plant/image/<int:id>',views.displayPlantImage,name='display_plantImg'),
    path('form/update/<int:pk>',views.UpdatePostView,name='update_form'),
    path('form/delete/<int:pk>',views.deletePost,name='delete_form'),
    path('form/reject/<int:id>',views.rejectPostView,name='reject_form'),
    path('register-form/',views.UserRegister,name='user_reg'),
    path('login-form/',views.UserLogin,name='user_login'),
    path('user-home/',views.userHome,name='user_home'),
    path("logout", views.logout_request, name="logout"),
    path('browse-name/',views.browse,name='browse'),
    #path('browse-use/',views.browse_use,name='browse_use'),
    #path('browse-dist/',views.browse_dist,name='browse_dist'),
    path('use-chart',views.usage_chart,name='use-chart'),
    path('unpublished-list/',views.unpubList,name='unpubList'),
    path('publish/<int:pk>',views.publishAction,name='publish'),
    path('country-settings/',views.country_settings,name='settings'),
    path('plant-data-upload/',views.data_upload,name='data-upload'),
]