import requests
import sys
sys.path.insert(0, '/home/sennlabs-netagrill/Documents/face-checkin/')

def checkin_teamhero_go(user_name, file_name, emotion):
    with open(f'/home/sennlabs-netagrill/Documents/face-checkin/{file_name}', 'rb') as f:
        url = 'https://2e73sk5t84.execute-api.ap-southeast-1.amazonaws.com/teamhero/api/check-in'
        myobj = {'name': user_name,
                'emotion':emotion}
        x = requests.post(url, data = myobj, files={'image':f})
    
    return x.text
    

