#from django.db.models.query import RawQuerySet
from django.shortcuts import render,redirect, get_object_or_404
#from django.views.generic import UpdateView

from . import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User

from .models import Distribution, Profile, Usage, Plant, Plant_Usage, Plant_Distribution, Rejection
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.postgres.search import SearchVector, SearchQuery, TrigramSimilarity

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import PlantSerializer

from django.contrib.auth.models import User
from tablib import Dataset

from .resources import DistResource, PlantResource
from PlantWebApp import serializers

# Import Pagination Libraries
from django.core.paginator import Paginator

# .order_by('?') - Plant of the day

def home(request):
    """
    Display home page
    """
    plant_pub = Plant.objects.filter(publish=True).count()
    use_tag = Usage.objects.count()
    user_no = User.objects.count()

    context = {
        'plant_pub':plant_pub,
        'use_tag':use_tag,
        'user_no' : user_no
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
            suggest = Plant.objects.annotate(similarity=trig_vector).filter(similarity__gt=0.1).order_by('-similarity')
            print(suggest)
            # speed up: https://stackoverflow.com/questions/56538419/poor-performance-when-trigram-similarity-and-full-text-search-were-combined-with/56547280#56547280

        return render(request,'PlantWebApp/search-results.html',{'searchquery':searchquery, 'results':results,'suggest':suggest})
    else:
        home(request)

def searchResultsAPI(request):
        searchquery = request.GET.get('searchquery') #is not None
        resultsdict = []

        if searchquery:
            results = Plant.objects.annotate(search = SearchVector('plantScientificName','plantLocalName','pmStem','pmLeaf','pmFruit','pmFlower','plantDist','voucher_no','usage__usage_tag')).filter(search=SearchQuery(searchquery)).filter(publish=True).distinct('id')
            for result in results:
                resultsdict.append(result)
        return JsonResponse({'status':200, 'data':resultsdict})

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

def displayGlossary(request):
    plant_list = Plant.objects.all().order_by('plantScientificName')
    return render(request, 'PlantWebApp/plant-glossary.html',{'plant_list':plant_list})

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
    plantdata = Plant.objects.get(id=pk) #get particular plant object from Plant table
    dist = Distribution.objects.all() #get distribution_country from Distribution table
    
    # Get usageID from plant_usage table and obtain queryset for the respective plant by ID # Convert to list #for select2
    plantUsageData = Plant_Usage.objects.filter(plantID=pk).values_list('usageID', flat=True)
    usearr= list(plantUsageData)
    #print(usearr)

    countryData = Plant_Distribution.objects.filter(plantID=pk).values_list('distID',flat=True)
    countryarr = list(countryData)
    print(countryarr)

    if request.method == "POST":
        use_form = forms.UsageForm(request.POST)
        plant_form = forms.PlantForm(request.POST,files=request.FILES, instance=plantdata)

        if use_form.is_valid():
            use_form.save()
            latest_use = Usage.objects.latest('id') #get the id of the newly added usage object
            usearr = request.POST.getlist('usage')#Added
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

            plant_form.save()
            '''
            plant_list = Plant.objects.filter(user_id=request.user).order_by('plantScientificName')
            messages.success(request,('Updated successfully.'))
            return render(request, 'PlantWebApp/user_home.html',{'plant_list':plant_list})'''
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
        plant_list = Plant.objects.filter(user_id=request.user).order_by('plantScientificName')
        #return userHome(request)
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
            profile = forms.UserProfileForm(request.POST)
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
    if request.user.is_authenticated:
        return redirect('user_home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password = password)

            if user is not None:
                login(request,user)
                return redirect('user_home')
            else:
                messages.info(request, 'Username or password is incorrect.')

        return render(request, 'PlantWebApp/login-form.html',{})

def logout_request(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("home")

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

        context = {
            'total_plant':total_plant,
            'plant_pub':plant_pub,
            'use_tag':use_tag,
            'user_no' : user_no,
            'country_list':country_list,
            'country_name':country_name,
            'country_record':country_record,
            'cc':cc,
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
        return render(request, 'PlantWebApp/admin-unpublished.html',{'plant_list':plant_list})

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

#@api_view(['GET', 'POST'])
@api_view(['GET'])
def apiOverview(request):
    api_urls = {
        'List':'/plant-list/',
        'Detail View':'/plant-detail/<str:pk>/',
        'Create':'/task-create/',
        'Update':'/task-update/<str:pk>/',
        'Delete':'/task-delete/<str:pk>/',
    }
    return Response(api_urls)

@api_view(['GET'])
def plantListApi(request):
    plants = Plant.objects.all()
    serializer = PlantSerializer(plants,many=True)
    return Response(serializer.data)


