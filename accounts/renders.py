from rest_framework import renderers
import json



class UserRenders(renderers.JSONRenderer):
    charset='utf-8'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response=''
        if 'ErrorDetail' in str(data):
            return json.dumps({'errors':data})
        else:
            response = json.dumps(data)
        return response