import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CONFIG.settings')
import django
django.setup()

from mangum import Mangum
from CONFIG.asgi import application

def handler(event, context):
    # Initialize Mangum handler with simplified configuration
    asgi_handler = Mangum(
       application,
       lifespan="off",  # Disable lifespan events
    #    api_gateway_base_path=None  # Handle requests at root path
    )
    return asgi_handler(event, context)
    # from apig_wsgi import make_lambda_handler
    # from django.core.wsgi import get_wsgi_application
    # application = get_wsgi_application()
    # _real_handler = make_lambda_handler(application, binary_support=True)
    # return _real_handler(event, context)