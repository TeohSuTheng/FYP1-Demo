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

from .models import Plant_LocalDistribution, Distribution, LocalDistribution, Profile, Usage, Plant, Plant_Usage, Plant_Distribution, Rejection, Images, Permission
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.postgres.search import SearchVector, SearchQuery, TrigramSimilarity
from django.http import JsonResponse, request
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
    plant_pub = Plant.objects.filter(admin_publish=True).count()
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
        results = Plant.objects.annotate(search = SearchVector('plantScientificName','plantLocalName','pmStem','pmLeaf','pmFruit','pmFlower','voucher_no','usage__usage_tag','distribution__countryName')).filter(search=SearchQuery(searchquery)).filter(admin_publish=True).distinct('id')
        print(results)

        # CREATE EXTENSION pg_trgm; at postgresql
        if not results: #result queryset is empty
            trig_vector = (TrigramSimilarity('plantScientificName', searchquery)+TrigramSimilarity('plantLocalName', searchquery))
            suggest = Plant.objects.annotate(similarity=trig_vector).filter(similarity__gt=0.1).filter(admin_publish=True).order_by('-similarity')
            print(suggest)
            # speed up: https://stackoverflow.com/questions/56538419/poor-performance-when-trigram-similarity-and-full-text-search-were-combined-with/56547280#56547280

        return render(request,'PlantWebApp/search-results.html',{'searchquery':searchquery, 'results':results,'suggest':suggest})
    else:
        home(request)

@login_required(login_url='user_login')    
def displayPlantForm(request):
    use = Usage.objects.all() #Get usage_tags data from Usage table 
    dist = Distribution.objects.all()
    state = LocalDistribution.objects.all()
    research_form = forms.ResearchForm(data=request.POST, files=request.FILES)

    if request.method == "POST":
        plant_form = forms.PlantForm(data=request.POST, files=request.FILES)
        use_form = forms.UsageForm(request.POST)
        img_list = request.FILES.getlist('images_list')

        # Verify data
        if use_form.is_valid():
            use_form.save()
            
            latest_use = Usage.objects.latest('id') #get the id of the newly added usage object
            
            plantScientificName = request.POST['plantScientificName']
            usearr = request.POST.getlist('usage')
            usearr.append(latest_use) #append the newly saved usage tag

            context_dict = {
                'taxoKingdom':request.POST['taxoKingdom'],
                'taxoDivision':request.POST['taxoDivision'],
                'taxoClass' :request.POST['taxoClass'],
                'taxoOrder' :request.POST['taxoOrder'],
                'taxoFamily' :request.POST['taxoFamily'],
                'taxoGenus' : request.POST['taxoGenus'],
                'plantScientificName':plantScientificName, 
                'plantLocalName':request.POST['plantLocalName'],
                'pmStem':request.POST['pmStem'],
                'pmLeaf':request.POST['pmLeaf'],
                'pmFruit':request.POST['pmFruit'],
                'pmFlower':request.POST['pmFlower'],
                #'voucher_no': request.POST['voucher_no'],
                'use': use,
                'usearr':usearr,
                'plantref': request.POST['plantref'],
                'dist':dist,
                'state':state,
                'research_form':research_form,
            }

            messages.success(request,('Usage tag added.'))
            return render(request,'PlantWebApp/plant-form.html',context_dict)  
        elif plant_form.is_valid() and use_form.is_valid()==False:
            ## Check if usage tag is unique:
            tag_exist = Usage.objects.filter(usage_tag=request.POST['usage_tag'])

            if tag_exist:
                messages.success(request,('The plant usage entered already exists in our database.'))
                # Add context dict
                return render(request,'PlantWebApp/plant-form.html',{'use': use,'research_form':research_form})

            plantdat = plant_form.save(commit=False)
            plantdat.research_data = research_form.data['research_data']
            plantdat.user = request.user
            #plantdat - collection
            if plantdat.voucher==None:
                plantdat.voucher=0

            if plantdat.powder==None:
                plantdat.powder=0

            if plantdat.extract==None:
                plantdat.extract=0

            if plantdat.oil==None:
                plantdat.oil=0

            plantdat.save()
            plant_form.save()

            for img in img_list:
                Images.objects.create(plant=plantdat,image=img)
            
            messages.success(request,('Your form has been submitted successfully.'))
            #get plant_id pass to another view method?
            return render(request,'PlantWebApp/plant-form.html',{'use': use,'dist':dist, 'research_form':research_form})
        else:
            #print(plant_form.errors)
            plantScientificName = request.POST['plantScientificName']
            usearr = request.POST.getlist('usage')

            context_dict = {
                'taxoKingdom':request.POST['taxoKingdom'],
                'taxoDivision':request.POST['taxoDivision'],
                'taxoClass' :request.POST['taxoClass'],
                'taxoOrder' :request.POST['taxoOrder'],
                'taxoFamily' :request.POST['taxoFamily'],
                'taxoGenus' : request.POST['taxoGenus'],
                'plantScientificName':plantScientificName, 
                'plantLocalName':request.POST['plantLocalName'],
                'pmStem':request.POST['pmStem'],
                'pmLeaf':request.POST['pmLeaf'],
                'pmFruit':request.POST['pmFruit'],
                'pmFlower':request.POST['pmFlower'],
                #'voucher_no': request.POST['voucher_no'],
                'use': use,
                'usearr':usearr,
                'plantref': request.POST['plantref'],
                'dist':dist,
                'research_form':research_form,
                'state':state,
            }
            
            #if scientific name is not unique - means already exist
            plant_exist = Plant.objects.filter(plantScientificName=plantScientificName)
            if plant_exist:
                messages.success(request,('The plant already exists in our database.'))
            else:
                messages.success(request,('There is an error in your form. Please try again.'))
            return render(request,'PlantWebApp/plant-form.html',context_dict)            

    return render(request,'PlantWebApp/plant-form.html',{'state':state,'use': use,'dist':dist,'research_form':research_form})

@login_required(login_url='user_login')
def assignPermissionForm(request):
    user_list = User.objects.filter(profile__role=2).filter(profile__is_verified=True).exclude(id=request.user.id) #list of researchers
    plant = Plant.objects.all().filter(admin_publish=True)

    if request.method == "POST":
        permission_form = forms.PermissionForm(data=request.POST)
        if permission_form.is_valid():

            #validate unique ** values
            permission_form.save()
            messages.success(request,('Success: Permission updated.'))
            return redirect('user_home')
        else:
            messages.success(request,('There is an error in your form. Please try again.'))
        
    context = {
        'user_list':user_list,
        'plant':plant,
    }
    return render(request,'PlantWebApp/view-permission-form.html',context)

@login_required(login_url='user_login')
def permissionList(request):
    permissions = Permission.objects.filter(plantID__user=request.user).order_by('plantID__plantScientificName')
    print(permissions)
    context = {
        'permissions':permissions,
    }
    return render(request,'PlantWebApp/view-permission-list.html',context)

@staff_member_required(login_url='user_login')
def adminPermissionList(request):
    permissions = Permission.objects.all().order_by('plantID__plantScientificName')
    #permissions = Permission.objects.filter(is_approved=True).order_by('plantID__plantScientificName')
    #pendingPermissions = Permission.objects.filter(is_approved=False).order_by('plantID__plantScientificName')
    print(permissions)
    context = {
        'permissions':permissions,
        #'pendingPermissions':pendingPermissions,
    }
    return render(request,'PlantWebApp/admin-permission-list.html',context)

'''Delete'''
@staff_member_required(login_url='user_login')
def ProcessingPermissionVerification(request,id):
    processingPermission = Permission.objects.get(id=id)

    if processingPermission:
        processingPermission.is_approved = True
        processingPermission.save(update_fields=['is_approved'])
        messages.success(request,('Permission approved.'))
        return redirect('admin_permissionList')
    else:
        adminPermissionList(request)

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

    plantdata = Plant.objects.get(id=id)

    permissions = Permission.objects.filter(plantID=id)

    if plantdata.rejected:
        reject = Rejection.objects.get(plant_id=id)

    plantimages = Images.objects.filter(plant_id=id)

    states = LocalDistribution.objects.filter(plant=id).values_list('stateName',flat=True)

    context = {
        #'plant_info':get_object_or_404(Plant,pk=id),
        #'reject_info':get_object_or_404(Rejection,plant_id=id),
        'plant_info':plantdata,
        'reject_info':reject,
        'plantUsageData':plantUsageData,
        'use_list':use_list,
        'country_list':country_list,
        'country_name':country_name,
        'plantimages':plantimages,
        'states':states,
        'permissions':permissions,
    }

    return render(request, 'PlantWebApp/plant-info.html',context)

def displayPlantApi(request,id):
    return render(request, 'PlantWebApp/plant-info-api.html',{'id':id})

@login_required(login_url='user_login')
def UpdatePostView(request,pk):
    use = Usage.objects.all() #get uses_tags from Usage table
    plantdata = Plant.objects.get(id=pk)

    dist = Distribution.objects.all() #get distribution_country from Distribution table
    state = LocalDistribution.objects.all()
    
    # Get usageID from plant_usage table and obtain queryset for the respective plant by ID # Convert to list #for select2
    plantUsageData = Plant_Usage.objects.filter(plantID=pk).values_list('usageID', flat=True)
    usearr= list(plantUsageData)

    countryData = Plant_Distribution.objects.filter(plantID=pk).values_list('distID',flat=True)
    countryarr = list(countryData)

    stateData = Plant_LocalDistribution.objects.filter(plantID=pk).values_list('localID',flat=True)
    statearr = list(stateData)
    
    research_form = forms.ResearchForm(instance=plantdata)

    plantimages = Images.objects.filter(plant_id=pk)

    if request.method == "POST":
        img_list = request.FILES.getlist('images_list')
        use_form = forms.UsageForm(request.POST)
        plant_form = forms.PlantForm(request.POST,files=request.FILES, instance=plantdata)
        research_form = forms.ResearchForm(request.POST,instance=plantdata)
        
        if use_form.is_valid():
            use_form.save()
            latest_use = Usage.objects.latest('id') #get the id of the newly added usage object
            usearr = request.POST.getlist('usage') # Added
            usearr.append(latest_use) #append the newly saved usage tag ###

            context = {
            'taxoKingdom':plantdata.taxoKingdom,
            'taxoDivision':plantdata.taxoDivision,
            'taxoClass' :plantdata.taxoClass,
            'taxoOrder' :plantdata.taxoOrder,
            'taxoFamily' :plantdata.taxoFamily,
            'taxoGenus' :plantdata.taxoGenus,
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
            'research_form':research_form,
            'state':state,
            'statearr':statearr,
            'voucher':plantdata.voucher,
            'powder':plantdata.powder,
            'extract':plantdata.extract,
            'oil':plantdata.oil,
        }
            return render(request, 'PlantWebApp/update-form.html',context)

        # Verify data # CHECK unique
        else:
            if plant_form.is_valid():
                ## Check if usage tag is unique:
                tag_exist = Usage.objects.filter(usage_tag=request.POST['usage_tag'])
            
                if tag_exist:
                    messages.success(request,('The plant usage entered already exists in our database.'))
                    context = {
                        'taxoKingdom':plantdata.taxoKingdom,
                        'taxoDivision':plantdata.taxoDivision,
                        'taxoClass' :plantdata.taxoClass,
                        'taxoOrder' :plantdata.taxoOrder,
                        'taxoFamily' :plantdata.taxoFamily,
                        'taxoGenus' :plantdata.taxoGenus,
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
                        'research_form':research_form,
                        'state':state,
                        'statearr':statearr,
                        'voucher':plantdata.voucher,
                        'powder':plantdata.powder,
                        'extract':plantdata.extract,
                        'oil':plantdata.oil,
                    }
                    return render(request, 'PlantWebApp/update-form.html',context)

                plantdata = plant_form.save(commit=False)
                if plantdata.voucher==None:
                        plantdata.voucher=0

                if plantdata.powder==None:
                        plantdata.powder=0

                if plantdata.extract==None:
                        plantdata.extract=0

                if plantdata.oil==None:
                        plantdata.oil=0

                plantdata.save()
                plant_form.save()

                for img in img_list:
                    Images.objects.create(plant=plantdata,image=img)


        
            if research_form.is_valid():
                research_form.save()

            if plant_form.is_valid or research_form.is_valid():
                if plantdata.rejected:
                    
                    plantdata.rejected = False
                    plantdata.save(update_fields=['rejected'])

                    # Delete Rejection object
                    rejectdata = Rejection.objects.get(plant=pk) #get object from Plant table
                    rejectdata.delete()

            messages.success(request,('Plant record updated successfully.'))
            return redirect('user_home')
    
    context = {
        'plantdata':plantdata,
        'taxoKingdom':plantdata.taxoKingdom,
        'taxoDivision':plantdata.taxoDivision,
        'taxoClass' :plantdata.taxoClass,
        'taxoOrder' :plantdata.taxoOrder,
        'taxoFamily' :plantdata.taxoFamily,
        'taxoGenus' :plantdata.taxoGenus,
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
        'research_form':research_form,
        'plantimages':plantimages,
        'state':state,
        'statearr':statearr,
        'voucher':plantdata.voucher,
        'powder':plantdata.powder,
        'extract':plantdata.extract,
        'oil':plantdata.oil,
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

@login_required(login_url='user_login')
def deleteImg(request,id):
    img = Images.objects.get(id=id) #get object from Plant table
    img.delete()
    return UpdatePostView(request,img.plant_id)

def UserRegister(request): 
    if request.user.is_authenticated:
        return redirect('user_home')
    else:
        form = forms.CreateUserForm()

        if request.method == "POST":
            form = forms.CreateUserForm(request.POST)
            fname = request.POST['first_name']
            lname = request.POST['last_name']
            uname = request.POST['username']
            email = request.POST['email']
            profile_form = forms.RegUserProfileForm(request.POST)

            if profile_form.is_valid():
                print("ok ah")
            
            if form.is_valid() and profile_form.is_valid():
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
            else:
                print(profile_form.errors)
                messages.error(request,('There is an error in the form. Please recheck.'))
            return render(request, 'PlantWebApp/register-form.html',{'form':form,'first_name':fname,'last_name':lname, 'username':uname,'email':email})

        return render(request, 'PlantWebApp/register-form.html',{'form':form,})

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

            verifiychecks = Q(username=username) & Q(profile__is_verified= False)
            unverifieduser = User.objects.filter(verifiychecks)

            # Is the account verified?
            if unverifieduser:
                messages.info(request, 'Account waiting to be verified.')
                return render(request, 'PlantWebApp/login-form.html',{})

            # Login successfully
            elif user is not None:
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
    # Query all non-expired sessions
    # use timezone.now() instead of datetime.now() in latest versions of Django
    # '__gte' means greater than or equal
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    # Query all logged in users based on id list
    return User.objects.filter(id__in=uid_list).order_by('first_name')

@login_required(login_url='user_login')
def userHome(request):
    if request.user.profile.role == 0: #Role Id 0 - Admin
        total_plant = Plant.objects.count() # Get total number of plant records stored
        plant_pub = Plant.objects.filter(admin_publish=True).count() # Get total number of plant records published
        use_tag = Usage.objects.count() # Get total number of usage tags stored
        user_no = User.objects.count() # Get total number of users registered
        countryData = Plant_Distribution.objects.all().values('distID').annotate(Count('distID')).order_by('-distID__count') # Get total number of plant records based on each country (plant distribution) and order by plant count in distribution model in desc '-'

        ## Prepare data for svg map ##
        country_list = []
        for j in countryData:
            country_list.append(Distribution.objects.filter(id=j.get('distID'))[0].country_alpha2)

        country_name = []
        for k in countryData:
            country_name.append(Distribution.objects.filter(id=k.get('distID'))[0].countryName)

        country_record = []
        for l in countryData:
            country_record.append(l['distID__count'])
        
        country_dict = {}
        for m in range(0,len(countryData)):
            country_dict[country_name[m]] = country_record[m]

        ## Pagination ##

        # Get all user objects
        logged_users = get_all_logged_in_users()
        ## Pagination ##
        pub_p = Paginator(logged_users,3)
        page = request.GET.get('page')
        logged_users = pub_p.get_page(page)

        # Get all logged out users by excluding logged_in users queryset
        logged_out_users = User.objects.exclude(username__in=logged_users)
        ## Pagination ##
        pub_p = Paginator(logged_out_users,3)
        page = request.GET.get('page')
        logged_out_users = pub_p.get_page(page)

        context = {
            'total_plant':total_plant,
            'plant_pub':plant_pub,
            'use_tag':use_tag,
            'user_no' : user_no,
            'country_list':country_list,
            #'country_name':country_name,
            #'country_record':country_record,
            'country_dict':country_dict,
            'logged_users':logged_users,
            'logged_out_users':logged_out_users,

        }
        return render(request, 'PlantWebApp/admin-home.html',context)
    elif request.user.profile.role == 1: # Role id 1 - Committee
        #approved_list = Plant.objects.filter(commitee_approved=True).order_by('plantScientificName')
        approved_list_count = Plant.objects.filter(committee_approved=True).count
        unapproved_list_count = Plant.objects.filter(committee_approved=False).filter(rejected=False).count
        #print(Plant.objects.filter(committee_approved=False).filter(rejected=False))
        rejected_list_count = Plant.objects.filter(rejected=True).count

        context = {
            'approved_list_count':approved_list_count,
            'unapproved_list_count':unapproved_list_count,
            'rejected_list_count':rejected_list_count
        }

        return render(request, 'PlantWebApp/committee_home.html',context)
    else: # Role id 2 - Researcher
        pub_list = Q(user_id=request.user) & Q(admin_publish=True)
        pub_plant_list = Plant.objects.filter(pub_list).order_by('plantScientificName')
        ## Pagination ##
        pub_p = Paginator(pub_plant_list,6)
        page = request.GET.get('page')
        pub_plants = pub_p.get_page(page)

        unpub_list = Q(user_id=request.user) & Q(admin_publish=False) & Q(rejected=False) 
        plant_list = Plant.objects.filter(unpub_list).order_by('plantScientificName')
        ## Pagination ##
        unpub_p = Paginator(plant_list,6)
        page1 = request.GET.get('page1')
        unpub_plants = unpub_p.get_page(page1)

        reject_q = Q(user_id=request.user) & Q(rejected=True) 
        reject_list = Plant.objects.filter(reject_q).order_by('plantScientificName')
        ## Pagination ##
        reject_p = Paginator(reject_list,6)
        page2 = request.GET.get('page2')
        reject_list = reject_p.get_page(page2)

        context = {
            'reject_list':reject_list,
            'pub_plants':pub_plants,
            'unpub_plants':unpub_plants,
        }

        return render(request, 'PlantWebApp/user_home.html',context)


@login_required(login_url='user_login')
def userProfileUpdate(request,id):
    user_data = User.objects.get(id=id)
    #user_profile = Profile.objects.get(user_id=id)

    if request.method == "POST":
        u_form = forms.UserUpdateForm(request.POST, instance=user_data)
        p_form = forms.UserProfileForm(request.POST, instance=user_data.profile)
        print('ok')

        if u_form.is_valid() and p_form.is_valid(): 
            print('ok')
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
    site_user = User.objects.get(id=id)

    if request.method == "POST":
        site_user.delete()
        messages.success(request,'Account deleted successfully.')
        ## + Del Profile (cascade = True)
        return redirect("home")

    return render(request, 'PlantWebApp/user-delete.html',{'site_user':site_user})

@staff_member_required(login_url='user_login')
def siteUsersList(request):
    #userList = User.objects.filter(is_staff = False)
    userList = User.objects.filter(is_active = True).filter(profile__is_verified=True)#.filter(is_staff = False)
    inactive_userList = User.objects.filter(is_active = False).filter(profile__is_verified=True)
    return render(request, 'PlantWebApp/site-users.html',{'userList':userList, 'inactive_userList':inactive_userList})

@staff_member_required(login_url='user_login')
def displayUserResults(request):
    if request.method == "GET":
        searchquery = request.GET['searchquery'] #is not None
        suggest = []

        userList = User.objects.annotate(search = SearchVector('first_name','last_name')).filter(search=SearchQuery(searchquery)).filter(is_active=True).distinct('id')
        print(userList)
        inactive_userList = User.objects.annotate(search = SearchVector('first_name','last_name')).filter(search=SearchQuery(searchquery)).filter(is_active=False).distinct('id')

        return render(request,'PlantWebApp/site-users.html', {'userList':userList,'inactive_userList':inactive_userList})
    else:
        siteUsersList(request)

@staff_member_required(login_url='user_login')
def siteUserVerification(request):
    adminquery = Q(profile__role=0) & Q(profile__is_verified=False)
    adminUsers = User.objects.filter(adminquery).order_by("first_name")
    ## Pagination ##
    pub_p = Paginator(adminUsers,10)
    page = request.GET.get('page')
    admin_list = pub_p.get_page(page)

    committeequery = Q(profile__role=1) & Q(profile__is_verified=False)
    committeeUsers = User.objects.filter(committeequery).order_by("first_name")
    ## Pagination ##
    pub_p = Paginator(committeeUsers,10)
    page = request.GET.get('page')
    committee_list = pub_p.get_page(page)
    
    researchQuery = Q(profile__role=2) & Q(profile__is_verified=False)
    researchUsers = User.objects.filter(researchQuery).order_by("first_name")
    ## Pagination ##
    pub_p = Paginator(researchUsers,10)
    page = request.GET.get('page')
    researcher_list = pub_p.get_page(page)

    context = {
        'admin_list':admin_list,
        'committee_list':committee_list,
        'researcher_list':researcher_list
    }

    return render(request, 'PlantWebApp/site-user-verification.html',context)

@login_required(login_url='user_login')
def ProcessingVerification(request,id):
    processingUser = Profile.objects.get(user_id=id)

    if processingUser:
        processingUser.is_verified = True
        processingUser.save(update_fields=['is_verified'])

        if processingUser.role == 0:
            thisUser = User.objects.get(id=id)
            thisUser.is_staff = True
            thisUser.save(update_fields=['is_staff'])

        return redirect('user_home')
    else:
        siteUserVerification(request)

@staff_member_required(login_url='user_login')
def siteUserDetail(request,id):

    # Display user data 
    user_info = User.objects.get(id=id)
    #user_profile = Profile.objects.get(user_id=id)

    date = formats.date_format(user_info.date_joined, "SHORT_DATETIME_FORMAT")

    # Display list of plant data submitted by user

    ## Published ##
    pub_list = Q(user_id=id) & Q(admin_publish=True)
    pub_plant_list = Plant.objects.filter(pub_list).order_by('plantScientificName')
    ## Pagination ##
    pub_p = Paginator(pub_plant_list,4)
    page = request.GET.get('page')
    pub_plants = pub_p.get_page(page)

    ## To Be Verified ##
    unpub_list = Q(user_id=id) & Q(admin_publish=False) & Q(rejected=False) 
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
    use_queryset = Usage.objects.all().order_by('-created_at')
    full_list = Usage.objects.all().values('usage_tag').distinct()

    # Set up Pagination
    use_pag = Paginator(use_queryset, 10)
    page = request.GET.get('page')
    uses = use_pag.get_page(page)

    return render(request, 'PlantWebApp/usage-tags-settings.html',{'uses':uses,'full_list':full_list})

@staff_member_required(login_url='user_login')
def verify_tags(request,id):
    use = Usage.objects.get(id=id)

    use.is_verified = True
    use.save(update_fields=['is_verified'])
    return usageTagsSettings(request)

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

def browse(request):
    # Only pubish plants that are verified by admin
    plant_list = Plant.objects.filter(admin_publish=True).order_by('plantScientificName')

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

    if request.user.profile.role == 0 or request.user.profile.role == 1: #admin
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
    plant_list = Plant.objects.filter(committee_approved=True).filter(admin_publish=False).filter(rejected=False).order_by('created_at') 
    
    # Set up Pagination
    p = Paginator(plant_list, 10)
    page = request.GET.get('page')
    plants = p.get_page(page)

    return render(request, 'PlantWebApp/admin-unpublished.html',{'plants':plants})

@staff_member_required(login_url='user_login')
def displayUnpublishedResults(request):
    if request.method == "GET":
        searchquery = request.GET['searchquery'] #is not None
        suggest = []

        results = Plant.objects.annotate(search = SearchVector('plantScientificName',)).filter(search=SearchQuery(searchquery)).filter(admin_publish=False).filter(rejected=False).distinct('id')
        print(results)

        # Set up Pagination
        p = Paginator(results, 10)
        page = request.GET.get('page')
        plants = p.get_page(page)

        return render(request,'PlantWebApp/admin-unpublished.html', {'plants':plants})
    else:
        unpubList(request)

@staff_member_required(login_url='user_login')
def verified(request):
    # Arrange in the order from earliest to latest
    plant_list = Plant.objects.filter(admin_publish=True).filter(rejected=False).order_by('plantScientificName') 

    # Set up Pagination
    p = Paginator(plant_list, 10)
    page = request.GET.get('page')
    plants = p.get_page(page)

    # Hack Pagination 
    page_num = 'a' * p.num_pages

    return render(request, 'PlantWebApp/admin-verified.html',{'plants':plants,'page_num':page_num})

@staff_member_required(login_url='user_login')
def displayPublishedResults(request):
    if request.method == "GET":
        searchquery = request.GET['searchquery'] #is not None
        suggest = []

        results = Plant.objects.annotate(search = SearchVector('plantScientificName',)).filter(search=SearchQuery(searchquery)).filter(admin_publish=True).filter(rejected=False).distinct('id')
        print(results)

        # Set up Pagination
        p = Paginator(results, 10)
        page = request.GET.get('page')
        plants = p.get_page(page)

        return render(request,'PlantWebApp/admin-verified.html', {'plants':plants})
    else:
        verified(request)

@staff_member_required(login_url='user_login')
def displayCollections(request,collect):
    if request.method == "GET":

        if collect == 'Extract':
            plants = Plant.objects.filter(extract__gt=0)
        elif collect == 'Oil':
            plants = Plant.objects.filter(oil__gt=0)
        elif collect == 'Powder':
            plants = Plant.objects.filter(powder__gt=0)
        else:
            plants = Plant.objects.filter(voucher__gt=0)

        return render(request,'PlantWebApp/collection-data-detail.html', {'plants':plants,'collect':collect})
    else:
        verified(request)

@login_required(login_url='user_login')
def rejected(request):
    if request.user.profile.role == 1 or request.user.profile.role == 0:
        # Arrange in the order from earliest to latest
        plant_list = Plant.objects.filter(rejected=True).order_by('plantScientificName') 

        # Set up Pagination
        p = Paginator(plant_list, 10)
        page = request.GET.get('page')
        plants = p.get_page(page)

        return render(request, 'PlantWebApp/admin-rejected.html',{'plants':plants})
    else:
        return redirect('user_home')

@staff_member_required(login_url='user_login')
def displayRejectedResults(request):
    if request.method == "GET":
        searchquery = request.GET['searchquery'] #is not None
        suggest = []

        results = Plant.objects.annotate(search = SearchVector('plantScientificName',)).filter(search=SearchQuery(searchquery)).filter(rejected=True).distinct('id')
        print(results)

        # Set up Pagination
        p = Paginator(results, 10)
        page = request.GET.get('page')
        plants = p.get_page(page)

        return render(request,'PlantWebApp/admin-rejected.html', {'plants':plants})
    else:
        rejected(request)

@staff_member_required(login_url='user_login')
def publishAction(request,pk):
    plantdata = Plant.objects.get(id=pk)
    plantdata.admin_publish = True
    plantdata.save(update_fields=['admin_publish'])

    # ** Add message - plant published
    return unpubList(request)

## can delete + country-state-settings
@staff_member_required(login_url='user_login')
def addState(request):
    country_form = forms.LocalDistForm()
    if request.method == 'POST':
      form = forms.LocalDistForm(request.POST)
      form.save()
    return render(request,'PlantWebApp/country-state-settings.html',{'country_form':country_form})

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

@login_required(login_url='user_login')
def rejectPostView(request,id):
    if request.user.profile.role == 1 or request.user.profile.role == 0:
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
        
        plantdata = Plant.objects.get(id=id) 
        if plantdata.rejected:
            reject = Rejection.objects.get(plant_id=id)
            context = {
            #'plant_info':get_object_or_404(Plant,pk=id),
            'plant_info':plantdata,
            'reject_info':reject,
            'plantUsageData':plantUsageData,
            'use_list':use_list,
            'country_list':country_list,
            'country_name':country_name,
            }
        else:
            context = {
            #'plant_info':get_object_or_404(Plant,pk=id),
            'plant_info':plantdata,
            'plantUsageData':plantUsageData,
            'use_list':use_list,
            'country_list':country_list,
            'country_name':country_name,
            }

        if request.method == "POST":
            if plantdata.rejected == False:
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

            else:
                reject_form = forms.RejectForm(request.POST, instance = reject)
                reject_form.save()
                messages.success(request,('Rejection reason updated successfully.'))
                return rejected(request)

        return render(request,'PlantWebApp/rejection-form.html',context)
    else:
        return redirect('user_home')

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

def userPageView(request,id):
    # Display user data 
    user_info = User.objects.get(id=id)
    #user_profile = Profile.objects.get(user_id=id)

    
    # Display list of plant data submitted by user

    ## Published ##
    pub_list = Q(user_id=id) & Q(admin_publish=True)
    pub_plant_list = Plant.objects.filter(pub_list).order_by('plantScientificName')
    ## Pagination ##
    pub_p = Paginator(pub_plant_list,10)
    page = request.GET.get('page')
    pub_plants = pub_p.get_page(page)

    context = {
        'user_info':user_info,
        'pub_plants':pub_plants,
    }

    return render(request,'PlantWebApp/user-page.html', context)

#** API VIEWS**
def countryDataDetails(request,country):
    return render(request,'PlantWebApp/country-data-detail.html',{'country':country})

def stateDataDetails(request,state):
    return render(request,'PlantWebApp/state-data-detail.html',{'state':state})

def usageDataDetails(request,use):
    return render(request,'PlantWebApp/usage-data-detail.html',{'use':use})


'''
@login_required(login_url='user_login')
def userProfileView(request,id):
    #user_profile = Profile.objects.get(user_id=id)
    context = {
        'user_info' : get_object_or_404(User,id=id), #user_data = User.objects.get(id=id)
        #'user_profile' : user_profile,
    }
    return render(request, 'PlantWebApp/user-profile.html',context)'''

@login_required(login_url='user_login')
def userProfileView(request,id):
    return render(request, 'PlantWebApp/user-profile.html',{'id':id})

@login_required(login_url='user_login')
def committeeVerified(request):
    if request.user.profile.role == 1: # Role id 1 - Committee
        # Arrange in the order from earliest to latest
        plant_list = Plant.objects.filter(committee_approved=True).filter(rejected=False).order_by('plantScientificName') 

        # Set up Pagination
        p = Paginator(plant_list, 10)
        page = request.GET.get('page')
        plants = p.get_page(page)

        # Hack Pagination 
        #page_num = 'a' * p.num_pages
        return render(request, 'PlantWebApp/com-verified.html',{'plants':plants})
    else:
        return redirect('user_home')

@login_required(login_url='user_login')
def committeeUnverified(request):
    
    # Arrange in the order from earliest to latest
    plant_list = Plant.objects.filter(committee_approved=False).filter(rejected=False).order_by('plantScientificName') 

    # Set up Pagination
    p = Paginator(plant_list, 10)
    page = request.GET.get('page')
    plants = p.get_page(page)

    if request.user.profile.role == 1: # Role id 1 - Committee
        # Hack Pagination 
        #page_num = 'a' * p.num_pages
        return render(request, 'PlantWebApp/com-unverified.html',{'plants':plants})
    elif request.user.profile.role == 0: # Role id 1 - Admin
        return render(request, 'PlantWebApp/admin-view-pending.html',{'plants':plants})
    else:
        return redirect('user_home')

def processingComVerification(request,id):
    plantdata = Plant.objects.get(id=id)
    plantdata.committee_approved = True
    plantdata.save(update_fields=['committee_approved'])

    # ** Add message - plant published
    return committeeVerified(request)

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

class PermissionDeleteView(BSModalDeleteView):
    model = Permission
    template_name = 'PlantWebApp/view-permission-del.html'
    success_message = 'Success: Permission deleted.'
    success_url = reverse_lazy('user_home')


# Live Search for usage-tags-settings
'''class UsageListView(ListView):
    model = Usage
    template_name = 'PlantWebApp/usage-tags-settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["qs_json"] = json.dumps(list(Usage.objects.values()))
        return context'''


#*** API ***#
def browse_api(request):
    return render(request,'PlantWebApp/browse_plants_api.html')