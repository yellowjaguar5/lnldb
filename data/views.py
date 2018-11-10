import json
import mimetypes
import os
import stat

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, HttpResponse, HttpResponseNotModified
from django.shortcuts import render
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.dateparse import parse_datetime
from django.utils.http import http_date, urlquote_plus
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.static import was_modified_since
from watson import search as watson

from events import models as events_models


@login_required
# TODO: adjust for perm test
def search(request):
    context = {}
    q = ""
    try:
        if request.POST:
            q = request.POST['q']
        else:
            q = request.GET['q']
    except MultiValueDictKeyError:
        pass
    context['query'] = q
    context['search_entry_list'] = watson.search(q)
    return render(request, 'search.html', context)


def serve_file(request, att_file, forced_name=None):
    statobj = os.stat(att_file.path)
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()
    content_type, encoding = mimetypes.guess_type(att_file.path)
    content_type = content_type or 'application/octet-stream'
    response = FileResponse(att_file, content_type=content_type)
    response["Last-Modified"] = http_date(statobj.st_mtime)
    if stat.S_ISREG(statobj.st_mode):
        response["Content-Length"] = statobj.st_size
    if encoding:
        response["Content-Encoding"] = encoding
    name = forced_name or att_file.name
    name = name.split('/')[-1]
    response["Content-Disposition"] = 'attachment; filename="%s"; filename*=UTF-8\'\'%s' % \
                                      (str(name).replace('"', ''), urlquote_plus(name))
    return response


@require_GET
def workorderwizard_load(request):
    # Manually checking if user is authenticated rather than using @login_required
    # in order to return a 401 status that the workorder wizard understands so it can redirect the user to log in
    # instead of returning a 302 redirect to the login page, which wouldn't work because this view is called via AJAX
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    response = {'locations': [], 'orgs': []}
    response['user'] = {'name': request.user.get_full_name(),
                        'email': request.user.email,
                        'phone': request.user.phone,
                        'address': request.user.addr}
    for loc in events_models.Location.objects.filter(show_in_wo_form=True):
        response['locations'].append({'id': loc.pk, 'name': loc.name, 'building': loc.building.name})
    for org in events_models.Organization.objects.all():
        data = {'id': org.pk,
                'name': org.name,
                'shortname': org.shortname,
                'owner': org.user_in_charge == request.user,
                'member': request.user in org.associated_users.all(),
                'delinquent': org.delinquent}
        if request.user.has_perm('events.view_org', org):
            data['email'] = org.exec_email
            data['phone'] = org.phone
            data['address'] = org.address
        response['orgs'].append(data)
    return HttpResponse(json.dumps(response))


@require_POST
@csrf_exempt
@transaction.atomic
def workorderwizard_submit(request):
    # Manually checking if user is authenticated rather than using @login_required
    # in order to return a 401 status that the workorder wizard understands so it can display a specific error message
    # instead of returning a 302 redirect to the login page, which wouldn't work because this view is called via AJAX
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    
    # load JSON
    data = json.loads(request.body.decode('utf-8'))

    # check that all required fields are present
    mandatory_fields = ('org', 'event_name', 'location', 'start', 'end', 'setup_complete', 'services')
    if not all(key in data for key in mandatory_fields):
        return HttpResponse('Unprocessable Entity', status=422)

    # create event object and populate fields
    event = events_models.Event2019()
    event.submitted_by = request.user
    event.submitted_ip = request.META.get('REMOTE_ADDR')
    event.contact = request.user
    event.event_name = data['event_name']
    if 'description' in data:
        event.description = data['description']
    try:
        event.location = events_models.Location.objects.filter(show_in_wo_form=True).get(pk=data['location'])
    except events_models.Location.DoesNotExist:
        return HttpResponse('Unprocessable Entity', status=422)
    event.datetime_setup_complete = parse_datetime(data['setup_complete'])
    event.datetime_start = parse_datetime(data['start'])
    event.datetime_end = parse_datetime(data['end'])
    try:
        org = events_models.Organization.objects.get(pk=data['org'])
    except events_models.Organization.DoesNotExist:
        return HttpResponse('Unprocessable Entity', status=422)
    event.billing_org = org
    event.test_event = True # TODO remove this line when the new work order wizard is publicly released 

    # populate many-to-many fields
    event.save()
    event.org.add(org)
    
    # add services
    for service_data in data['services']:
        if 'id' not in service_data:
            return HttpResponse('Unprocessable Entity', status=422)
        try:
            service = events_models.Service.objects.get(shortname=service_data['id']) # TODO use active flag
        except events_models.Service.DoesNotExist:
            return HttpResponse('Unprocessable Entity', status=422)
        service_instance = events_models.ServiceInstance()
        service_instance.service = service
        service_instance.event = event
        if 'detail' in service_data:
            service_instance.detail = service_data['detail']
        service_instance.save()

    # add extras
    for extra_data in data['extras']:
        if not all(key in extra_data for key in ('id', 'quantity')):
            return HttpResponse('Unprocessable Entity', status=422)
        try:
            extra = events_models.Extra.objects.filter(disappear=False).get(name=extra_data['id'])
        except events_models.Extra.DoesNotExist:
            return HttpResponse('Unprocessable Entity', status=422)
        extra_instance = events_models.ExtraInstance()
        extra_instance.extra = extra
        extra_instance.event = event
        extra_instance.quant = extra_data['quantity']
        extra_instance.save()

    # return response with the URL to the event detail page
    return HttpResponse(json.dumps({'event_url': reverse('events:detail', args=[event.pk])}))


def err403(request, *args, **kwargs):
    context = {}
    return render(request, '403.html', context, status=403)


def err404(request, *args, **kwargs):
    context = {}
    return render(request, '404.html', context, status=404)


def err500(request, *args, **kwargs):
    context = {}
    return render(request, '500.html', context, status=500)
