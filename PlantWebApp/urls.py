from django.urls import path, include
from . import views


urlpatterns = [
    #path('',views.home,name='home'),
    path('search-results/',views.displaySearchResults,name='display_SearchResults'),
    path('form/',views.displayPlantForm,name='display_form'),
    path('glossary/',views.displayGlossary,name='display_glossary'),
    path('plant/<int:id>',views.displayPlant,name='display_plant'),
    path('form/update/<int:pk>',views.UpdatePostView,name='update_form'),
    path('form/delete/<int:pk>',views.deletePost,name='delete_form'),
    path('register-form/',views.UserRegister,name='user_reg'),
    path('login-form/',views.UserLogin,name='user_login'),
    path('user-home/',views.userHome,name='user_home'),
    path("logout", views.logout_request, name="logout"),
    path('',views.browse,name='browse'),
]