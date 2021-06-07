from django.shortcuts import render,redirect, get_object_or_404
from django.views.generic import UpdateView

from . import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from .models import Usage, Plant, Plant_Usage
from django.contrib import messages
#from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery
import json

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

        # postgresql search query - stemming algorithm - logical combination of terms #advanced search
        results = Plant.objects.annotate(search = SearchVector('plantScientificName','plantLocalName','pmStem','pmLeaf','pmFruit','pmFlower','plantDist','voucher_no')).filter(search=SearchQuery(searchquery))

        # SearchRank

        # raw sql -1.get usage id where tags = '' 2.get plants where usage.id = '1.'

        return render(request,'PlantWebApp/search-results.html',{'searchquery':searchquery, 'results':results})
    else:
        return render(request,'PlantWebApp/index.html',{})
    
def displayPlantForm(request):
    use = Usage.objects.all() #Get usage_tags data from Usage table 
    
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
                'plantDist': request.POST['plantDist'],
                'voucher_no': request.POST['voucher_no'],
                'use': use,
                'usearr':usearr,
                'plantref': request.POST['plantref'],
                
            }
            
            messages.success(request,('Usage tag added.'))
            return render(request,'PlantWebApp/plant-form.html',context_dict)  
        elif plant_form.is_valid() and use_form.is_valid()==False:
            plant_form.save()
            messages.success(request,('Your form has been submitted successfully.'))
            #get plant_id pass to another view method?
            return render(request,'PlantWebApp/plant-form.html',{'use': use})
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
                'plantDist': request.POST['plantDist'],
                'voucher_no': request.POST['voucher_no'],
                'use': use,
                'usearr':usearr,
                'plantref': request.POST['plantref'],
            }
            #if scientific name is not unique - means already exist
            plant_exist = Plant.objects.filter(plantScientificName=plantScientificName)
            if plant_exist:
                messages.success(request,('The plant already exists in our database.'))
            else:
                messages.success(request,('There is an error in your form. Please try again.'))
            return render(request,'PlantWebApp/plant-form.html',context_dict)            

    return render(request,'PlantWebApp/plant-form.html',{'use': use})

def displayGlossary(request):
    plant_list = Plant.objects.all().order_by('plantScientificName')
    return render(request, 'PlantWebApp/plant-glossary.html',{'plant_list':plant_list})

def displayPlant(request,id):

    # Get queryset of usageID filter by plantID from Plant_Usage table
    plantUsageData = Plant_Usage.objects.filter(plantID=id).values_list('usageID', flat=True)

    use_list = []
    for i in plantUsageData:
        # [0] - to retrieve values inside the queryset
        use_list.append(Usage.objects.filter(id=i)[0].usage_tag)
    context = {
        'plant_info':get_object_or_404(Plant,pk=id),
        'plantUsageData':plantUsageData,
        'use_list':use_list,
    }
    return render(request, 'PlantWebApp/plant-info.html',context)

def UpdatePostView(request,pk):
    use = Usage.objects.all() #get uses_tags from Usage table
    plantdata = Plant.objects.get(id=pk) #get object from Plant table
    
    # Get usageID from plant_usage table and obtain queryset for the respective plant by ID # Convert to list #for select2
    plantUsageData = Plant_Usage.objects.filter(plantID=pk).values_list('usageID', flat=True)
    usearr= list(plantUsageData)
    #print(usearr)

    if request.method == "POST":
        use_form = forms.UsageForm(request.POST)
        plant_form = forms.PlantForm(request.POST,files=request.FILES, instance=plantdata)

        if use_form.is_valid():
            use_form.save()
            latest_use = Usage.objects.latest('id') #get the id of the newly added usage object
            usearr.append(latest_use) #append the newly saved usage tag

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
            'use': use
        }
            return render(request, 'PlantWebApp/update-form.html',context)

        # Verify data
        elif plant_form.is_valid() and use_form.is_valid()==False:
            plant_form.save()
            messages.success(request,('Updated successfully.'))
            return render(request, 'PlantWebApp/index.html',{})
    
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
        'use': use
    }
    return render(request, 'PlantWebApp/update-form.html',context)

def deletePost(request,pk):
    plantdata = Plant.objects.get(id=pk) #get object from Plant table

    if request.method == "POST":
        plantdata.delete()
        return render(request, 'PlantWebApp/index.html',{})

    context = {
        'plantScientificName':plantdata.plantScientificName,
    }
    return render(request, 'PlantWebApp/delete-form.html',context)

def UserRegister(request):
    form = forms.CreateUserForm()
    if request.method == "POST":
        form = forms.CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username') #only get user name
            messages.success(request,('Account was created for '+user))
            return redirect('user_login')
    return render(request, 'PlantWebApp/register-form.html',{'form':form})

def UserLogin(request):
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

def logoutUser(request):
    logout(request)
    return redirect(request,'user_login')

def userHome(request):
    return render(request, 'PlantWebApp/user_home.html',{})