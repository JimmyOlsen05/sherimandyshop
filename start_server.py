import os
import sys
import subprocess
from pyngrok import ngrok, conf

def main():
    # Configure ngrok
    conf.get_default().auth_token = "2taIH2YAW4R9tDJBSR6alwvS3AK_3Vu9VkLKt1AhE8sUSxCz8"
    
    try:
        # Start ngrok
        public_url = ngrok.connect(8000)
        print('\n' + '='*50)
        print('Ngrok tunnel established!')
        print('Public URL:', public_url)
        print('\nPaystack Webhook URL:', f'{public_url}/orders/paystack-webhook/')
        print('='*50 + '\n')
        
        # Start Django development server
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        from django.core.management import execute_from_command_line
        
        sys.argv = ['', 'runserver', '8000']
        execute_from_command_line(sys.argv)
        
    except KeyboardInterrupt:
        print('\nShutting down server...')
        ngrok.kill()
    except Exception as e:
        print(f'\nError: {str(e)}')
        ngrok.kill()
        sys.exit(1)

if __name__ == '__main__':
    main()
