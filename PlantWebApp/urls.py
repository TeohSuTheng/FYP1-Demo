from django.urls import path, include
from . import views


urlpatterns = [
    path('',views.home,name='home'),
    path('search-results/',views.displaySearchResults,name='display_SearchResults'),
    path('usage-search-results/',views.displayUsageResults,name='display_UsageResults'),
    path('unpublished-search-results/',views.displayUnpublishedResults,name='display_UnpublishedResults'),
    path('published-search-results/',views.displayPublishedResults,name='display_PublishedResults'),
    path('rejected-search-results/',views.displayRejectedResults,name='display_RejectedResults'),
    path('site-users-results/',views.displayUserResults,name='display_UsersResults'),


    path('form/',views.displayPlantForm,name='display_form'),
    path('plant/<int:id>',views.displayPlant,name='display_plant'),
    path('plant-api/<int:id>',views.displayPlantApi,name='displayPlantApi'),
    
    path('plant/image/<int:id>',views.displayPlantImage,name='display_plantImg'),
    path('plant/delete-image/<int:id>',views.deleteImg,name='deleteImg'),

    path('form/update/<int:pk>',views.UpdatePostView,name='update_form'),
    path('form/delete/<int:pk>',views.deletePost,name='delete_form'),
    path('form/reject/<int:id>',views.rejectPostView,name='reject_form'),
    path('register-form/',views.UserRegister,name='user_reg'),
    path('login-form/',views.UserLogin,name='user_login'),
    path('user-home/',views.userHome,name='user_home'),
    
    path('user-profile/<int:id>',views.userProfileView,name='user_profile'),
    path('user-profile-update/<int:id>',views.userProfileUpdate,name='user_profile_update'),
    path('user-delete/<int:id>',views.userProfileDelete,name='user_delete'),
    path("logout", views.logout_request, name="logout"),
    path('browse-name/',views.browse,name='browse'),
    path('advanced-search/',views.advancedSearch,name='advancedSearch'),

    #path('browse-use/',views.browse_use,name='browse_use'),
    #path('browse-dist/',views.browse_dist,name='browse_dist'),
    path('use-chart',views.usage_chart,name='use-chart'),
    path('unpublished-list/',views.unpubList,name='unpubList'),
    path('published-list/',views.verified,name='verified'),
    path('rejected-list/',views.rejected,name='rejected'),

    path('site-users/',views.siteUsersList,name='siteUsersList'),
    path('site-user/<int:id>',views.siteUserDetail,name='siteUserDetail'),
    path('site-user/disable/<int:id>',views.siteUserDisable,name='siteUserDisable'),
    path('site-user/enable/<int:id>',views.siteUserEnable,name='siteUserEnable'),
    path('site-user-reset/<int:id>',views.adminResetPassword,name='AdminResetPassword'),
    path('site-user-verification/',views.siteUserVerification,name='siteUserVerification'),
    path('site-user-processing/<int:id>',views.ProcessingVerification,name='ProcessingVerification'),
    

    path('usage-tags-settings/',views.usageTagsSettings,name='usageTagsSettings'),
    #path('usage-tags-settings/',views.UsageListView.as_view()   ,name='usageTagsSettings'),
    path('usage-tags-update-form/<int:pk>',views.UsageTagUpdateView.as_view(),name='usageTagsUpdate'),
    path('usage-tags-del/<int:pk>',views.UsageTagDeleteView.as_view(),name='usageTagsDelete'),
    path('usage-tags-create/',views.UsageTagCreateView.as_view(),name='UsageTagCreateView'),

    path('publish/<int:pk>',views.publishAction,name='publish'),
    path('country-settings/',views.country_settings,name='settings'),
    path('plant-data-upload/',views.data_upload,name='data-upload'),

    path('browse-name-api/',views.browse_api,name='browse-api'),
    path('country-data-detail/<str:country>',views.countryDataDetails,name="countryDataDetails" ),
    path('user-page/<int:id>',views.userPageView,name='user_page'),

    path('com-verified-list/',views.committeeVerified,name='com_verified'),
    path('com-unverified-list/',views.committeeUnverified,name='com_unverified'),
    path('com-verification/<int:id>',views.processingComVerification,name='com_verifying'),
]