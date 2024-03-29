from ad.models import *
from ad.forms import *
from ad.geocode import handle_uploaded_file
import json
from django.contrib.gis.geos import *

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import Context,loader
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.sites.models import Site

@login_required
def home(request):

    documents = []
    
    # Handle file upload
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = Address_List(user=request.user, address_list=request.FILES['docfile'], processed=False)
            newdoc.save()

            districts_requested = request.POST.getlist('district')
            
            global result_file
            result_file = handle_uploaded_file(newdoc, districts_requested)

            # Load list of documents in cache dir
            documents = Address_List.objects.filter(user_id=request.user.id)

            result_url = Site.objects.get_current().domain + str(newdoc.address_list)
            # Render home page with the documents, form, requested districts
            return render_to_response(
                'ad/index.html',
                {'result_url': result_url,
                 'form': form, 'districts_requested': districts_requested,
                 'contents': result_file},
                context_instance=RequestContext(request)
            )
            #return HttpResponse(json.dumps(geojson_dict), content_type='application/json')
            
        # Bounce back to home page if file not included
        else:
            return HttpResponseRedirect(reverse('ad.views.home'))
           
    #Load homepage (request.method = 'GET')
    else:
        # A empty unbound form
        form = DocumentForm() 
            
        #Load list of documents in cache dir
        documents = Address_List.objects.filter(user_id=request.user.id)

        # Render home page with the documents and the form
        return render_to_response(
        'ad/index.html',
        {'documents': documents[:5], 'form': form},
        context_instance=RequestContext(request)
        )

@login_required
def processed_files(request):

    documents = Address_List.objects.filter(user_id=request.user.id, processed=True)
    return render_to_response('ad/download.html',{'documents':documents})

@login_required
def results_geojson(request):
    layer_id = request.GET.get('layer')
    if layer_id == 'results':
        try:
            return HttpResponse(json.dumps(result_file), content_type='application/json')
        except:
            return HttpResponseRedirect(reverse('ad.views.home'))
    
    elif layer_id == 'States':       
        #coords = request.GET['bbox'].split(',')
        #bbox = Polygon.from_bbox(coords)
    
        query_set = States.objects.all()
        #query_set = States.objects.filter(geom__bboverlaps=bbox)
    
        # Build a geojson dict to hold list of features
        geojson_dict = {}
        
        # Build a list of features
        features = []
        
        for item in query_set:
        #Build a feature
            feature = {}
            feature['type'] = 'Feature'
            geojson = item.geom.simplify(0.0001).geojson
            feature['geometry'] = (json.loads(geojson)) # convert to dict so whole list can be converted to json
            feature['properties'] = { 'name':item.name}
            features.append(feature)
                      
        #Build a feature collection
        geojson_dict['type'] = "FeatureCollection"    
        geojson_dict['features'] = features
    
        return HttpResponse(json.dumps(geojson_dict), content_type='application/json')

#line below is merge conflict, commenting out to debug
#    return HttpResponse(json.dumps(result_file), content_type='application/json')
