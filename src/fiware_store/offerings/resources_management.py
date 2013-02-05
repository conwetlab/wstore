import base64
import os

from django.conf import settings

from fiware_store.models import Resource

def register_resource(provider, data):

    resource_data = {
        'name': data['name'],
        'version': data['version'],
        'type': 'download',
        'description': data['description'],
    }   
    if 'content' in data:
        resource = data['content']
        
        #decode the content and save the media file
        file_name = provider.username + '__' + data['name'] + '__' + data['version'] + '__' + resource['name']
        path = os.path.join(settings.MEDIA_ROOT, 'resources')
        file_path = os.path.join(path, file_name)
        f = open(file_path, "wb")
        dec = base64.b64decode(resource['data'])
        f.write(dec)
        resource_data['content_path'] = settings.MEDIA_URL + 'resources/' + file_name
        resource_data['link'] = ''
        
    elif 'link' in data:
        # Add the download link
        resource_data['link'] = data['link']
        resource_data['content_path'] = ''

    Resource.objects.create(
        name=resource_data['name'],
        provider=provider,
        version=resource_data['version'],
        resource_type=resource_data['type'],
        description=resource_data['description'],
        download_link=resource_data['link'],
        resource_path=resource_data['content_path']
    )

def get_provider_resources(provider):
    resouces = Resource.objects.filter(provider=provider)
    response = []    
    for res in resouces:
        response.append({
            'name': res.name,
            'version': res.version,
            'description': res.description
        })

    return response 
