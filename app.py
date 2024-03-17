import function_framework
from main import main
import logging

@function_framework.http
def handler(request):
    logging.info('Function triggered')
    
    try:
        data = request.get_json()
        logging.info(f'Data received: {data}')
        main()
        return 'Success', 200
    except Exception as e:
        logging.error(f'Error: {e}')
        return 'Error', 500
    