#from django.db.models.query import RawQuerySet
from django.shortcuts import render,redirect, get_object_or_404
#from django.views.generic import UpdateView
from django.utils import formats

from . import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.forms import formset_factory

from .models import Distribution, Profile, Usage, Plant, Plant_Usage, Plant_Distribution, Rejection
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.postgres.search import SearchVector, SearchQuery, TrigramSimilarity
from django.http import JsonResponse
from django.contrib.sessions.models import Session
from django.utils import timezone

from django.contrib.auth.models import User
from tablib import Dataset

from django.db import transaction
# Folium Map - index page
# import folium

from .resources import DistResource, PlantResource

# Check errors
from django.template import RequestContext, context

# Import Pagination Libraries
from django.core.paginator import Paginator

# .order_by('?') - Plant of the day

def home(request):
    """
    Display elements in home page
    """
    plant_pub = Plant.objects.filter(publish=True).count()
    use_tag = Usage.objects.count()
    user_no = User.objects.count()

    # Create Folium Map Object
    '''
    m = folium.Map(location=[3.1209,101.6538], zoom_start=14,)
    folium.Marker(
        [3.1209,101.6538], tooltip="We are here"
    ).add_to(m)
    m = m._repr_html_()'''

    context = {
        'plant_pub':plant_pub,
        'use_tag':use_tag,
        'user_no' : user_no,
        #'m' : m
    }
    return render(request,'PlantWebApp/index.html',context)

def displaySearchResults(request):
    if request.method == "GET":
        searchquery = request.GET['searchquery'] #is not None
        suggest = []
        # Q
        #que = Q(plantScientificName__icontains=searchquery) | Q(plantLocalName__icontains=searchquery) 
        #results = Plant.objects.filter(que)

        # postgresql search lookup
        # q = form.cleaned_data['q]
        # results = Plant.objects.filter(title__search = q)

        # postgresql search vector
        #results = Plant.objects.annotate(search = SearchVector('plantScientificName','plantLocalName')).filter(search=searchquery)

        # postgresql search query - stemming algorithm #advanced search
        '''
        SearchQuery translates the terms the user provides into a search query object that the 
        database compares to a search vector. By default, all the words the user provides are 
        passed through the stemming algorithms, and then it looks for matches for all of the
        resulting terms.
        '''
        results = Plant.objects.annotate(search = SearchVector('plantScientificName','plantLocalName','pmStem','pmLeaf','pmFruit','pmFlower','voucher_no','usage__usage_tag','distribution__countryName')).filter(search=SearchQuery(searchquery)).filter(publish=True).distinct('id')
        print(results)

        if not results: #result queryset is empty
            print('ok')
            suggest = []
            trig_vector = (TrigramSimilarity('plantScientificName', searchquery)+TrigramSimilarity('plantLocalName', searchquery))
            suggest = Plant.objects.annotate(similarity=trig_vector).filter(similarity__gt=0.1).filter(publish=True).order_by('-similarity')
            print(suggest)
            # speed up: https://stackoverflow.com/questions/56538419/poor-performance-when-trigram-similarity-and-full-text-search-were-combined-with/56547280#56547280

        return render(request,'PlantWebApp/search-results.html',{'searchquery':searchquery, 'results':results,'suggest':suggest})
    else:
        home(request)

#select2
@staff_member_required(login_url='user_login')
def displayUsageResults(request):
    if request.method == "GET":
        searchquery = request.GET['searchquery'] #is not None
        result = Usage.objects.filter(usage_tag__search=searchquery)

        # Set up Pagination
        use_pag = Paginator(result, 10)
        page = request.GET.get('page')
        uses = use_pag.get_page(page)

        full_list = Usage.objects.all().values('usage_tag').distinct()

        return render(request,'PlantWebApp/usage-tags-settings.html',{'uses':uses,'full_list':full_list})

@login_required(login_url='user_login')    
def displayPlantForm(request):
    use = Usage.objects.all() #Get usage_tags data from Usage table 
    dist = Distribution.objects.all()

    if request.method == "POST":
        plant_form = forms.PlantForm(data=request.POST, files=request.FILES)
        use_form = forms.UsageForm(request.POST)

        # Verify data
        if use_form.is_valid():
            use_form.save()
            latest_use = Usage.objects.latest('id') #get the id of the newly added usage object
            
            plantScientificName = request.POST['plantScientificName']
            usearr = request.POST.getlist('usage')
            usearr.append(latest_use) #append the newly saved usage tag

            context_dict = {
                'plantScientificName':plantScientificName, 
                'plantLocalName':request.POST['plantLocalName'],
                'pmStem':request.POST['pmStem'],
                'pmLeaf':request.POST['pmLeaf'],
                'pmFruit':request.POST['pmFruit'],
                'pmFlower':request.POST['pmFlower'],
                'voucher_no': request.POST['voucher_no'],
                'use': use,
                'usearr':usearr,
                'plantref': request.POST['plantref'],
                'dist':dist,
            }
            messages.success(request,('Usage tag added.'))
            return render(request,'PlantWebApp/plant-form.html',context_dict)  
        elif plant_form.is_valid() and use_form.is_valid()==False:
            ## Check if usage tag is unique:
            tag_exist = Usage.objects.filter(usage_tag=request.POST['usage_tag'])

            if tag_exist:
                messages.success(request,('The plant usage entered already exists in our database.'))
                return render(request,'PlantWebApp/plant-form.html',{'use': use})

            plantdat = plant_form.save(commit=False)
            plantdat.user = request.user
            plantdat.save()
            plant_form.save()
            
            messages.success(request,('Your form has been submitted successfully.'))
            #get plant_id pass to another view method?
            return render(request,'PlantWebApp/plant-form.html',{'use': use,'dist':dist})
        else:
            plantScientificName = request.POST['plantScientificName']
            usearr = request.POST.getlist('usage')

            context_dict = {
                'plantScientificName':plantScientificName, 
                'plantLocalName':request.POST['plantLocalName'],
                'pmStem':request.POST['pmStem'],
                'pmLeaf':request.POST['pmLeaf'],
                'pmFruit':request.POST['pmFruit'],
                'pmFlower':request.POST['pmFlower'],
                'voucher_no': request.POST['voucher_no'],
                'use': use,
                'usearr':usearr,
                'plantref': request.POST['plantref'],
                'dist':dist,
            }
            
            #if scientific name is not unique - means already exist
            plant_exist = Plant.objects.filter(plantScientificName=plantScientificName)
            if plant_exist:
                messages.success(request,('The plant already exists in our database.'))
            else:
                messages.success(request,('There is an error in your form. Please try again.'))
            return render(request,'PlantWebApp/plant-form.html',context_dict)            

    return render(request,'PlantWebApp/plant-form.html',{'use': use,'dist':dist})

def displayPlant(request,id):
    # Get queryset of usageID filter by plantID from Plant_Usage table
    plantUsageData = Plant_Usage.objects.filter(plantID=id).values_list('usageID', flat=True)
    countryData = Plant_Distribution.objects.filter(plantID=id).values_list('distID',flat=True)
    reject = []

    use_list = []
    for i in plantUsageData:
        # [0] - to retrieve values inside the queryset
        use_list.append(Usage.objects.filter(id=i)[0].usage_tag)

    country_list = []
    for j in countryData:
        country_list.append(Distribution.objects.filter(id=j)[0].country_alpha2)

    country_name = []
    for k in countryData:
        country_name.append(Distribution.objects.order_by('countryName').filter(id=k)[0].countryName)

    print(country_name)

    plantdata = Plant.objects.get(id=id)
    if plantdata.rejected:
        reject = Rejection.objects.get(plant_id=id)

    context = {
        #'plant_info':get_object_or_404(Plant,pk=id),
        #'reject_info':get_object_or_404(Rejection,plant_id=id),
        'plant_info':plantdata,
        'reject_info':reject,
        'plantUsageData':plantUsageData,
        'use_list':use_list,
        'country_list':country_list,
        'country_name':country_name,

    }
    return render(request, 'PlantWebApp/plant-info.html',context)

@login_required(login_url='user_login')
def UpdatePostView(request,pk):
    use = Usage.objects.all() #get uses_tags from Usage table
    plantdata = Plant.objects.get(id=pk)
    #newplantdata = Plant.objects.select_for_update(skip_locked=True).filter(id=pk)
    #print(newplantdata[0])
    dist = Distribution.objects.all() #get distribution_country from Distribution table
    
    # Get usageID from plant_usage table and obtain queryset for the respective plant by ID # Convert to list #for select2
    plantUsageData = Plant_Usage.objects.filter(plantID=pk).values_list('usageID', flat=True)
    usearr= list(plantUsageData)

    countryData = Plant_Distribution.objects.filter(plantID=pk).values_list('distID',flat=True)
    countryarr = list(countryData)

    if request.method == "POST":
        use_form = forms.UsageForm(request.POST)
        plant_form = forms.PlantForm(request.POST,files=request.FILES, instance=plantdata)

        if use_form.is_valid():
            use_form.save()
            latest_use = Usage.objects.latest('id') #get the id of the newly added usage object
            usearr = request.POST.getlist('usage') # Added
            usearr.append(latest_use) #append the newly saved usage tag ###

            context = {
            'plantScientificName':plantdata.plantScientificName,
            'plantLocalName':plantdata.plantLocalName,
            "pmStem":plantdata.pmStem,
            "pmLeaf":plantdata.pmLeaf,
            "pmFlower": plantdata.pmFlower,
            "pmFruit": plantdata.pmFruit,
            "plantImg": plantdata.plantImg,
            "voucher_no":plantdata.voucher_no,
            "plantref":plantdata.plantref,
            "usearr":usearr,
            'use': use,
            'countryarr':countryarr,
            'dist':dist,
        }
            return render(request, 'PlantWebApp/update-form.html',context)

        # Verify data # CHECK unique
        elif plant_form.is_valid() and use_form.is_valid()==False:
            
            ## Check if usage tag is unique:
            tag_exist = Usage.objects.filter(usage_tag=request.POST['usage_tag'])
            if tag_exist:
                messages.success(request,('The plant usage entered already exists in our database.'))
                context = {
                    'plantScientificName':plantdata.plantScientificName,
                    'plantLocalName':plantdata.plantLocalName,
                    "pmStem":plantdata.pmStem,
                    "pmLeaf":plantdata.pmLeaf,
                    "pmFlower": plantdata.pmFlower,
                    "pmFruit": plantdata.pmFruit,
                    "plantImg": plantdata.plantImg,
                    "voucher_no":plantdata.voucher_no,
                    "plantref":plantdata.plantref,
                    "usearr":usearr,
                    'use': use,
                    'countryarr':countryarr,
                    'dist':dist,
                }
                return render(request, 'PlantWebApp/update-form.html',context)
            
            
            #with transaction.atomic():
            plant_form.save()
            messages.success(request,('Plant record updated successfully.'))

            return userHome(request)
    
    context = {
        'plantScientificName':plantdata.plantScientificName,
        'plantLocalName':plantdata.plantLocalName,
        "pmStem":plantdata.pmStem,
        "pmLeaf":plantdata.pmLeaf,
        "pmFlower": plantdata.pmFlower,
        "pmFruit": plantdata.pmFruit,
        "plantImg": plantdata.plantImg,
        "voucher_no":plantdata.voucher_no,
        "plantref":plantdata.plantref,
        "usearr":usearr,
        'use': use,
        'countryarr':countryarr,
        'dist':dist,
    }
    return render(request, 'PlantWebApp/update-form.html',context)

@login_required(login_url='user_login')
def deletePost(request,pk):
    plantdata = Plant.objects.get(id=pk) #get object from Plant table

    if request.method == "POST":
        plantdata.delete()
        return home(request)

    context = {
        'plantScientificName':plantdata.plantScientificName,
    }
    return render(request, 'PlantWebApp/delete-form.html',context)

def UserRegister(request):
    if request.user.is_authenticated:
        return redirect('user_home')
    else:
        form = forms.CreateUserForm()

        if request.method == "POST":
            form = forms.CreateUserForm(request.POST)
            #profile = forms.UserProfileForm(request.POST)
            fname = request.POST['first_name']
            lname = request.POST['last_name']
            uname = request.POST['username']
            email = request.POST['email']
            profile_form = forms.UserProfileForm(request.POST)
            
            if form.is_valid() and profile_form.is_valid:
                if any(i.isdigit() for i in fname) or any(i.isdigit() for i in lname):
                    messages.info(request, "Incorrect format for name")
                    return render(request, 'PlantWebApp/register-form.html',{'form':form,'username':uname,'email':email})
                user_main = form.save()
                profile = profile_form.save(commit=False)

                #assign user to profile
                profile.user = user_main
                profile.save()

                user = form.cleaned_data.get('username') #only get user name
                messages.success(request,('Account was created for '+user))
                return redirect('user_login')

            return render(request, 'PlantWebApp/register-form.html',{'form':form,'first_name':fname,'last_name':lname, 'username':uname,'email':email})

        return render(request, 'PlantWebApp/register-form.html',{'form':form})

def UserLogin(request):

    # User had already logged in
    if request.user.is_authenticated:
        return redirect('user_home')

    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            # Check login credentials
            user = authenticate(request, username=username, password = password)

            # Check if user is inactive (Account disabled by admin)
            check = Q(username=username) & Q(is_active = False)
            disableduser = User.objects.filter(check)
            print(disableduser)
            print(user)

            # Login successfully
            if user is not None:

                # Add Session
                request.session['user_id'] = user.id

                login(request,user)
                return redirect('user_home')
            
            else:
                if disableduser:
                    messages.info(request, 'Account disabled. Please contact site administrator: site@admin.com ')
                    return render(request, 'PlantWebApp/login-form.html',{})
                    
                messages.info(request, 'Username or password is incorrect.')
        return render(request, 'PlantWebApp/login-form.html',{})

def logout_request(request):
    try:
        del request.session['user_id']
    except KeyError:
        pass

    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("home")

def get_all_logged_in_users():
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    uid_list = []

    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    return User.objects.filter(id__in=uid_list).order_by('first_name')

@login_required(login_url='user_login')
def userHome(request):
    if request.user.is_staff:
        #site admin - change to is_superuser if want

        total_plant = Plant.objects.count() # Get total number of plant records stored
        plant_pub = Plant.objects.filter(publish=True).count() # Get total number of plant records published
        use_tag = Usage.objects.count() # Get total number of usage tags stored
        user_no = User.objects.count() # Get total number of users registered
        countryData = Plant_Distribution.objects.all().values('distID').annotate(Count('distID')) # Get total number of plant records based on each country (plant distribution)

        ## Prepare data for svg map ##
        country_list = []
        for j in countryData:
            #print(j.get('distID')) #{'distID': 54, 'distID__count': 2}
            country_list.append(Distribution.objects.filter(id=j.get('distID'))[0].country_alpha2)
        #print(country_list)

        country_name = []
        for k in countryData:
            country_name.append(Distribution.objects.filter(id=k.get('distID'))[0].countryName)
        #print(country_name)

        country_record = []
        for l in countryData:
            country_record.append(l['distID__count'])
        
        cc = {}
        for m in range(0,len(countryData)):
            #print(countryData[m])
            cc[country_list[m]] = {'plant':country_record[m]}

        print(cc)

        # Get all user objects
        logged_users = get_all_logged_in_users()

        context = {
            'total_plant':total_plant,
            'plant_pub':plant_pub,
            'use_tag':use_tag,
            'user_no' : user_no,
            'country_list':country_list,
            'country_name':country_name,
            'country_record':country_record,
            'cc':cc,
            'logged_users':logged_users,
        }
        return render(request, 'PlantWebApp/admin-home.html',context)
    else:
        pub_list = Q(user_id=request.user) & Q(publish=True)
        pub_plant_list = Plant.objects.filter(pub_list).order_by('plantScientificName')
        unpub_list = Q(user_id=request.user) & Q(publish=False) & Q(rejected=False) 
        plant_list = Plant.objects.filter(unpub_list).order_by('plantScientificName')
        reject_q = Q(user_id=request.user) & Q(rejected=True) 
        reject_list = Plant.objects.filter(reject_q).order_by('plantScientificName')
        return render(request, 'PlantWebApp/user_home.html',{'plant_list':plant_list, 'pub_plant_list':pub_plant_list, 'reject_list':reject_list})
    ## if (is_staff==True) redirect to another page

@login_required(login_url='user_login')
def userProfileView(request,id):
    #user_profile = Profile.objects.get(user_id=id)
    context = {
        'user_info' : get_object_or_404(User,id=id), #user_data = User.objects.get(id=id)
        #'user_profile' : user_profile,
    }
    return render(request, 'PlantWebApp/user-profile.html',context)

@login_required(login_url='user_login')
def userProfileUpdate(request,id):
    user_data = User.objects.get(id=id)
    #user_profile = Profile.objects.get(user_id=id)

    if request.method == "POST":
        u_form = forms.UserUpdateForm(request.POST, instance=user_data)
        p_form = forms.UserProfileForm(request.POST, instance=user_data.profile)

        if u_form.is_valid() and p_form.is_valid(): 
            u_form.save()
            p_form.save()
            messages.success(request,'Updated successfully.')
            
            if request.user.is_staff:
                return siteUsersList(request)
            return userProfileView(request,id)
            #return redirect

        return userProfileView(request,id)
        
    context = {
        'user_data' : user_data, #user_data = User.objects.get(id=id)
        #'user_profile' : user_profile,
    }
    return render(request, 'PlantWebApp/user-profile-update.html',context)

@login_required(login_url='user_login')
def userProfileDelete(request,id):
    if request.method == "POST":
        request.user.delete()
        messages.success(request,'Account deleted successfully.')
        ## + Del Profile (cascade = True)
        return redirect("home")

    return render(request, 'PlantWebApp/user-delete.html',{})

@staff_member_required(login_url='user_login')
def siteUsersList(request):
    #userList = User.objects.filter(is_staff = False)
    userList = User.objects.all()
    return render(request, 'PlantWebApp/site-users.html',{'userList':userList})

@staff_member_required(login_url='user_login')
def siteUserDetail(request,id):

    # Display user data 
    user_info = User.objects.get(id=id)
    #user_profile = Profile.objects.get(user_id=id)

    date = formats.date_format(user_info.date_joined, "SHORT_DATETIME_FORMAT")

    # Display list of plant data submitted by user

    ## Published ##
    pub_list = Q(user_id=id) & Q(publish=True)
    pub_plant_list = Plant.objects.filter(pub_list).order_by('plantScientificName')
    ## Pagination ##
    pub_p = Paginator(pub_plant_list,4)
    page = request.GET.get('page')
    pub_plants = pub_p.get_page(page)

    ## To Be Verified ##
    unpub_list = Q(user_id=id) & Q(publish=False) & Q(rejected=False) 
    plant_list = Plant.objects.filter(unpub_list).order_by('plantScientificName')
    ## Pagination ##
    unpub_p = Paginator(plant_list,4)
    page1 = request.GET.get('page1')
    unpub_plants = unpub_p.get_page(page1)
    
    ## Rejected ##
    reject_q = Q(user_id=id) & Q(rejected=True) 
    reject_list = Plant.objects.filter(reject_q).order_by('plantScientificName')
    ## Pagination ##
    reject_p = Paginator(reject_list,4)
    page2 = request.GET.get('page2')
    reject_list = reject_p.get_page(page2)

    context = {
        'user_info':user_info,
        #'user_profile':user_profile,
        'reject_list':reject_list,
        'pub_plants':pub_plants,
        'unpub_plants':unpub_plants,
        'date':date
    }
    return render(request, 'PlantWebApp/site-user-detail.html',context)

@staff_member_required(login_url='user_login')
def siteUserDisable(request,id):
    user_data = User.objects.get(id=id)
    user_data.is_active = False
    user_data.save()
    return siteUsersList(request)

@staff_member_required(login_url='user_login')
def siteUserEnable(request,id):
    user_data = User.objects.get(id=id)
    user_data.is_active = True
    user_data.save()
    return siteUsersList(request)

@staff_member_required(login_url='user_login')
def usageTagsSettings(request):
    use_queryset = Usage.objects.all().order_by('usage_tag')
    full_list = Usage.objects.all().values('usage_tag').distinct()

    # Set up Pagination
    use_pag = Paginator(use_queryset, 10)
    page = request.GET.get('page')
    uses = use_pag.get_page(page)

    return render(request, 'PlantWebApp/usage-tags-settings.html',{'uses':uses,'full_list':full_list})

def browse(request):
    # Only pubish plants that are verified by admin
    plant_list = Plant.objects.filter(publish=True).order_by('plantScientificName')

    # Set up Pagination
    p = Paginator(plant_list, 10)
    page = request.GET.get('page')
    plants = p.get_page(page)

    # Hack Pagination 
    page_num = 'a' * p.num_pages

    return render(request, 'PlantWebApp/browse_plants.html',{'plants':plants,'page_num':page_num})

def usage_chart(request):
    label_id = []
    labels = []
    data = []

    if request.user.is_staff:
        plant_count = Plant.objects.all().values('usage').annotate(Count('usage')).order_by('usage') # get list of plant objects based on the user
    else:
        plant_count = Plant.objects.filter(user_id=request.user).values('usage').annotate(Count('usage')).order_by('usage') # get list of plant objects based on the user
    #1. Get a set of plants created by user
    #2. Get usage field from plant object
    #3. Count each field
    print(plant_count)
    for entry in plant_count:
        if entry['usage'] != None:
            label_id.append(entry['usage'])
            data.append(entry['usage__count'])

    # Get sets of usage_tag based on usage_id #order by usage_id (same like plant table ^^)
    tmplist = Usage.objects.filter(id__in=label_id).values('usage_tag').order_by('id')
    for entry_lb in tmplist:
        labels.append(entry_lb['usage_tag'])
    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

@staff_member_required(login_url='user_login')
def unpubList(request):
    # Arrange in the order from earliest to latest
    plant_list = Plant.objects.filter(publish=False).filter(rejected=False).order_by('created_at') 
    
    # Set up Pagination
    p = Paginator(plant_list, 10)
    page = request.GET.get('page')
    plants = p.get_page(page)


    return render(request, 'PlantWebApp/admin-unpublished.html',{'plants':plants})
    #return render(request, 'PlantWebApp/admin-unpublished.html',{'plant_list':plant_list})

@staff_member_required(login_url='user_login')
def verified(request):
    # Arrange in the order from earliest to latest
    plant_list = Plant.objects.filter(publish=True).filter(rejected=False).order_by('plantScientificName') 

    # Set up Pagination
    p = Paginator(plant_list, 10)
    page = request.GET.get('page')
    plants = p.get_page(page)

    # Hack Pagination 
    page_num = 'a' * p.num_pages

    return render(request, 'PlantWebApp/admin-verified.html',{'plants':plants,'page_num':page_num})

@staff_member_required(login_url='user_login')
def rejected(request):
    # Arrange in the order from earliest to latest
    plant_list = Plant.objects.filter(rejected=True).order_by('plantScientificName') 

    # Set up Pagination
    p = Paginator(plant_list, 10)
    page = request.GET.get('page')
    plants = p.get_page(page)

    return render(request, 'PlantWebApp/admin-rejected.html',{'plants':plants})

@staff_member_required(login_url='user_login')
def publishAction(request,pk):
    plantdata = Plant.objects.get(id=pk)
    plantdata.publish = True
    plantdata.save(update_fields=['publish'])

    # ** Add message - plant published
    return unpubList(request)

@staff_member_required(login_url='user_login')
def country_settings(request):
    if request.method == "POST":
        dist_resource = DistResource()
        dataset = Dataset()
        new_dist = request.FILES['myfile']

        if not new_dist.name.endswith('xlsx'):
            messages.info(request,'Wrong format.')
            return render(request,'PlantWebApp/country-settings.html',{})

        imported_data = dataset.load(new_dist.read(), format='xlsx')
        for data in imported_data:
            value = Distribution(
                data[0],
                data[1],
                data[2],
            )
            value.save()
    return render(request,'PlantWebApp/country-settings.html',{})

@staff_member_required(login_url='user_login')
def rejectPostView(request,id):
    # ***Rejection Form*** # #Update plant form -> reject#
    if request.method == "POST":
        reject_form = forms.RejectForm(request.POST)

        # Verify data
        if reject_form.is_valid():
            temp = reject_form.save(commit=False)
            temp.plant_id = id
            temp.save()

            plantdata = Plant.objects.get(id=id)
            plantdata.rejected = True
            plantdata.save(update_fields=['rejected'])

            # Back to unpublished list page #
            return unpubList(request)

    # ***Display plant data*** #
    # Get queryset of usageID filter by plantID from Plant_Usage table
    plantUsageData = Plant_Usage.objects.filter(plantID=id).values_list('usageID', flat=True)
    countryData = Plant_Distribution.objects.filter(plantID=id).values_list('distID',flat=True)
    use_list = []
    for i in plantUsageData:
        # [0] - to retrieve values inside the queryset
        use_list.append(Usage.objects.filter(id=i)[0].usage_tag)
    country_list = []
    for j in countryData:
        country_list.append(Distribution.objects.filter(id=j)[0].country_alpha2)
    country_name = []
    for k in countryData:
        country_name.append(Distribution.objects.order_by('countryName').filter(id=k)[0].countryName)

    context = {
        'plant_info':get_object_or_404(Plant,pk=id),
        'plantUsageData':plantUsageData,
        'use_list':use_list,
        'country_list':country_list,
        'country_name':country_name,

    }
    return render(request,'PlantWebApp/rejection-form.html',context)

def data_upload(request):
    if request.method == "POST":
        plant_resource = PlantResource()
        dataset = Dataset()
        new_dist = request.FILES['myfile']

        if not new_dist.name.endswith('xlsx'):
            messages.info(request,'Wrong format.')
            return render(request,'PlantWebApp/plant-data-upload.html',{})

        imported_data = dataset.load(new_dist.read(), format='xlsx')
        for data in imported_data:
            value = Plant(
                data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7],
                data[8], data[9], data[10], data[11], data[12], data[13], 
            )
            value.save()
    return render(request,'PlantWebApp/plant-data-upload.html',{})

def displayPlantImage(request,id):
    plant = Plant.objects.get(id=id)
    return render(request,'PlantWebApp/plant-image.html',{'plant':plant})

def adminResetPassword(request,id):
    user_dat = User.objects.get(id=id)
    if request.method == "POST":
        new_password = request.POST['new_pw']
        user_dat.set_password(new_password)
        user_dat.save()
    return render(request,'PlantWebApp/site-user-reset-password.html',{'user_dat':user_dat})

def advancedSearch(request):
    # form - flexible
    # user can add input columns + type
    # input name - search1, search2, search3... (for loop)
    # Qcomplex - Boolean (AND + Or first) -> (NOT)
    # AJAX Suggestions (type chosen)
    AdvancedSearchFormSet = formset_factory(forms.AdvancedSearchForm,extra=3)
    
    if 'submit' in request.POST:
        formset = AdvancedSearchFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                # extract name from each form and save
                name = form.cleaned_data.get('term')
                print(name)

    return render(request,'PlantWebApp/advanced-search.html',{'AdvancedSearchFormSet':AdvancedSearchFormSet})

#@permission_required('polls.add_choice')

# Class Based Views
from django.views.generic import ListView
from django.urls import reverse_lazy
from bootstrap_modal_forms.generic import BSModalCreateView,BSModalUpdateView, BSModalDeleteView
import json

class UsageTagCreateView(BSModalCreateView):
    template_name = 'PlantWebApp/usage-tags-create.html'
    form_class = forms.UseTagUpdateModelForm
    success_message = 'Success: Plant Usage Tag Created.'
    success_url = reverse_lazy('usageTagsSettings')

class UsageTagUpdateView(BSModalUpdateView):
    model = Usage
    template_name = 'PlantWebApp/usage-tags-update.html'
    form_class = forms.UseTagUpdateModelForm
    success_message = 'Success: Plant Usage Tag updated.'
    success_url = reverse_lazy('usageTagsSettings')

class UsageTagDeleteView(BSModalDeleteView):
    model = Usage
    template_name = 'PlantWebApp/usage-tags-del.html'
    success_message = 'Success: Plant Usage Tag deleted.'
    success_url = reverse_lazy('usageTagsSettings')


# Live Search for usage-tags-settings
'''class UsageListView(ListView):
    model = Usage
    template_name = 'PlantWebApp/usage-tags-settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["qs_json"] = json.dumps(list(Usage.objects.values()))
        return context'''