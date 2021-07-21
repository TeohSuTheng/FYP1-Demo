from django.db.models.query import RawQuerySet
from django.shortcuts import render,redirect, get_object_or_404
from django.views.generic import UpdateView

from . import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Distribution, Profile, Usage, Plant, Plant_Usage, Plant_Distribution
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.http import JsonResponse, HttpResponse

from django.contrib.auth.models import User
from tablib import Dataset

from .resources import DistResource

def home(request):
    """
    Display home page
    """
    return render(request,'PlantWebApp/index.html',{})

def displaySearchResults(request):
    if request.method == "GET":
        searchquery = request.GET['searchquery'] #is not None

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
        results = Plant.objects.annotate(search = SearchVector('plantScientificName','plantLocalName','pmStem','pmLeaf','pmFruit','pmFlower','plantDist','voucher_no','usage__usage_tag')).filter(search=SearchQuery(searchquery))

        # SearchRank

        # raw sql -1.get usage id where tags = '' 2.get plants where usage.id = '1.'

        return render(request,'PlantWebApp/search-results.html',{'searchquery':searchquery, 'results':results,})
    else:
        return render(request,'PlantWebApp/index.html',{})

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

    context = {
        'plant_info':get_object_or_404(Plant,pk=id),
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
            "plantDist":plantdata.plantDist,
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
                    "plantDist":plantdata.plantDist,
                    "plantref":plantdata.plantref,
                    "usearr":usearr,
                    'use': use,
                    'countryarr':countryarr,
                    'dist':dist,
                }
                return render(request, 'PlantWebApp/update-form.html',context)

            plant_form.save()
            plant_list = Plant.objects.filter(user_id=request.user).order_by('plantScientificName')
            messages.success(request,('Updated successfully.'))
            return render(request, 'PlantWebApp/user_home.html',{'plant_list':plant_list})
    
    context = {
        'plantScientificName':plantdata.plantScientificName,
        'plantLocalName':plantdata.plantLocalName,
        "pmStem":plantdata.pmStem,
        "pmLeaf":plantdata.pmLeaf,
        "pmFlower": plantdata.pmFlower,
        "pmFruit": plantdata.pmFruit,
        "plantImg": plantdata.plantImg,
        "voucher_no":plantdata.voucher_no,
        "plantDist":plantdata.plantDist,
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
        return render(request, 'PlantWebApp/user_home.html',{'plant_list':plant_list})

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
    return redirect("browse")

@login_required(login_url='user_login')
def userHome(request):
    if request.user.is_staff:
        #site admin - change to is_superuser if want
        plant_list = Plant.objects.all().order_by('plantScientificName')
        return render(request, 'PlantWebApp/admin-home.html',{})
    else:
        pub_list = Q(user_id=request.user) & Q(publish=True)
        pub_plant_list = Plant.objects.filter(pub_list).order_by('plantScientificName')
        unpub_list = Q(user_id=request.user) & Q(publish=False)
        plant_list = Plant.objects.filter(unpub_list).order_by('plantScientificName')
        return render(request, 'PlantWebApp/user_home.html',{'plant_list':plant_list, 'pub_plant_list':pub_plant_list})
    ## if (is_staff==True) redirect to another page

def browse(request):
    # Only pubish plants that are verified by admin
    plant_list = Plant.objects.filter(publish=True).order_by('plantScientificName')
    return render(request, 'PlantWebApp/browse_plants.html',{'plant_list':plant_list})

def usage_chart(request):
    label_id = []
    labels = []
    data = []
    
    #1. Get a set of plants created by user
    #2. Get usage field from plant object
    #3. Count each field
    plant_count = Plant.objects.filter(user_id=request.user).values('usage').annotate(Count('usage')).order_by('usage') # get list of plant objects based on the user
    print(plant_count)
    for entry in plant_count:
        if entry['usage'] != None:
            label_id.append(entry['usage'])
            data.append(entry['usage__count'])
    #print(label_id)
    #print(data)

    # Get sets of usage_tag based on usage_id #order by usage_id (same like plant table ^^)
    tmplist = Usage.objects.filter(id__in=label_id).values('usage_tag').order_by('id')
    for entry_lb in tmplist:
        labels.append(entry_lb['usage_tag'])
    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

@login_required(login_url='user_login')
def unpubList(request):
    if request.user.is_staff:
        # Arrange in the order from earliest to latest
        plant_list = Plant.objects.filter(publish=False).order_by('created_at') 
        return render(request, 'PlantWebApp/admin-unpublished.html',{'plant_list':plant_list})

@login_required(login_url='user_login')
def publishAction(request,pk):
    if request.user.is_staff:
        plantdata = Plant.objects.get(id=pk)
        plantdata.publish = True
        plantdata.save(update_fields=['publish'])
        # message **
        
        # unpubList
        # Arrange in the order from earliest to latest
        plant_list = Plant.objects.filter(publish=False).order_by('created_at') 
        return render(request, 'PlantWebApp/admin-unpublished.html',{'plant_list':plant_list})

def country_settings1(request):
    #login required
    #request.user.is_staff
    country_form = forms.DistributionForm(request.POST)
    if request.method == "POST":
        if country_form.is_valid:
            country_form.save()
    return render(request,'PlantWebApp/country-settings.html',{'country_form':country_form})

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



#def admin_upload(request)