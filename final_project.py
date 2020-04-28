#Erin Murray
#erinvm

import secrets
import json
import requests
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

TREFLE_BASEURL = 'https://trefle.io/api/plants/'
TREFLE_KEY = secrets.TREFLE_API_KEY

WIKIMEDIA_BASEURL = 'https://en.wikipedia.org/w/api.php'
WIKIMEDIA_PARAMS = {'action': 'query', 'format': 'json', 'titles': '', 'prop': 'pageimages', 'piprop': 'original'}
CACHE_FILENAME = 'trefle_cache.json'
CACHE_DICT = {}
TEMP_PARAMS = {'duration': 'Perennial', 'palatable_browse_animal': 'Low', 'complete_data': 'true', 'growth_habit': 'Tree'}
SEARCH_PARAMS = []

"""
shade_tolerance = ['Tolerant', 'Intermediate', 'Intolerant']
bloom_period = [
                'Spring', 'Early Spring', 'Mid Spring','Late Spring', 
                'Summer', 'Early Summer', 'Mid Summer', 'Late Summer',
                'Fall', 'Winter', 'Late Winter', 'Indeterminate'
                ]
temperature_minimum_deg_f = 'float'
growth_habit = [
                'Forb/herb', 'Graminoid', 'Lichenous',
                'Nonvascular', 'Shrub', 'Subshrub', 'Tree', 'Vine'
                ]
mature_height = 'float'
palatable_browse_animal = ['Low', 'Moderate', 'High']
has_image = True
native_status = ''
"""

#Functions go here:
def get_zone_from_zip(zipcode):
    conn = sqlite3.connect('FinalPlantDB.sqlite')
    cur = conn.cursor()

    #TODO: CODE QUERY HERE
    query = f'''
            SELECT Zone
            FROM USDAZones
            WHERE Zipcode = {zipcode}
            '''

    results = cur.execute(query).fetchall()
    conn.close()
    return results[0][0]

def get_zone_from_low(low_min):
    conn = sqlite3.connect('FinalPlantDB.sqlite')
    cur = conn.cursor()

    #TODO: CODE QUERY HERE
    query = f'''
            SELECT Zone
            FROM USDAZones
            WHERE LowMin = {low_min}
            '''

    results = cur.execute(query).fetchall()
    conn.close()
    return results[0][0]

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def make_request(baseurl, api_key):
    '''Make a request to the Web API using the baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the data returned from making the request in the form of 
        a dictionary
    '''
    if api_key == None:
        endpoint = baseurl
    else:

        endpoint = baseurl + 'token=' + api_key
    response = requests.get(endpoint)
    return response.json()

def make_request_with_cache(baseurl, api_key, params):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    '''
    params = {'q': hashtag, 'count': count}
    request_key = construct_unique_key(baseurl, params)
    '''
    request_key = construct_unique_key(baseurl, params)
    if request_key in CACHE_DICT.keys():
        #print("cache hit!")
        return CACHE_DICT[request_key]
    else:
        #print("cache miss!")
        CACHE_DICT[request_key] = make_request(request_key, api_key)
        save_cache(CACHE_DICT)
        return CACHE_DICT[request_key]


def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    unique_key = ''
    try:
        if params.isdigit():
            unique_key = baseurl + params +'?'
    except:
        param_strings = []
        connector = '&'
        for key in params.keys():
            param_strings.append(f'{key}={params[key]}')
            unique_key = baseurl + '?' + connector.join(param_strings) + '&'
    return unique_key

def get_wiki_image(image_info):
    """TODO: FINISH DOCSTRING
    """
    image = str(image_info).split('{')
    image = image[5].split(' ')
    image = image[1].strip(",")
    image = image.strip("'")
    return image

def sort_trefle_json(trefle_results):
    """TODO: FINISH DOCSTRING
    """
    plant_list = []
    for result in trefle_results:
        try:
            plant_dict = {}
            new_endpoint = str(result['id'])

            plant_link = make_request_with_cache(TREFLE_BASEURL, TREFLE_KEY, new_endpoint)
            plant_dict['name'] = plant_link['common_name']
            plant_dict['sci_name'] = plant_link['scientific_name']
            image_endpoint = WIKIMEDIA_PARAMS
        
            image_endpoint['titles'] = plant_dict['sci_name']
            try:
                image_info = make_request_with_cache(WIKIMEDIA_BASEURL, api_key=None, params=image_endpoint)

                image_return = get_wiki_image(image_info)
                if 'map' in image_return.split('_'):
                    plant_dict['image'] = False
                else:
                    plant_dict['image'] = image_return
            except:
                plant_dict['image'] = False
            plant_dict['duration'] = plant_link['duration']
            
            if plant_link['main_species']['growth']['shade_tolerance'] == 'Tolerant':
                plant_dict['shade'] = 'Full Shade'
            elif plant_link['main_species']['growth']['shade_tolerance'] == 'Intermediate':
                plant_dict['shade'] = 'Part Sun/Shade'
            else:
                plant_dict['shade'] = 'Full Sun'
            plant_dict['bloom_period'] = plant_link['main_species']['seed']['bloom_period']
            low_temp = (plant_link['main_species']['growth']['temperature_minimum']['deg_f'])
            try:
                low_temp = 5 * round(low_temp/5)
                if low_temp >= -40:
                    low_zone = get_zone_from_low(low_temp)
                    try:
                        max_zone = get_zone_from_low(low_temp + 40)
                    except:
                        max_zone = '11b'
                    plant_dict['zone'] = f'{low_zone} - {max_zone}'
                else: plant_dict['zone'] = f'3a - 7a'
            except:
                plant_dict['zone'] = 'Not Available'
            plant_dict['zone'] = f'{low_zone} - {max_zone}'
            growth_habit = plant_link['main_species']['specifications']['growth_habit']
            if growth_habit == 'Graminoid':
                plant_dict['shape'] = 'Grass'
            elif growth_habit == 'Forb/herb':
                plant_dict['shape'] = 'Plant'
            else:
                plant_dict['shape'] = growth_habit
            plant_height = plant_link['main_species']['specifications']['mature_height']['ft']
            
            try:
                if plant_height < 1:
                    height = round(plant_height * 12)
                    plant_dict['height'] = f'{height} in.'
                else:
                    height = round(plant_height)
                    plant_dict['height'] = f'{height} ft.'
            except:
                plant_dict['height'] = 'Unrecorded'
            native_code = plant_link['main_species']['native_status']
            #native_code = native_code.replace('(', ':')
            #print(plant_dict['common_name'])
            #print(type(native_code))
            #native_code = native_code.split(')')
            #print(native_code)

            plant_dict['native'] = native_code
            if plant_link['main_species']['products']['palatable_browse_animal'] == 'Low':
                plant_dict['deer'] = 'Yes'
            else:
                plant_dict['deer'] = 'No'

            plant_list.append(plant_dict)

        except:
            print('Oh no! An error!')
            pass
    return plant_list

#App routes go here:
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def results():
    params_dict = {'complete_data': 'true', 'duration': 'Perennial',}
    if request.form['zipcode'].isdigit() and len(request.form['zipcode']) >= 4:
        zipcode = request.form['zipcode']
        user_zone = get_zone_from_zip(zipcode)
    else:
        user_zone = False
    if request.form['plant_type'] == 'None':
        pass
    else:
        params_dict['growth_habit'] = request.form['plant_type']
    if request.form['bloom_time'] == 'None':
        pass
    else:
        params_dict['bloom_period'] = request.form['bloom_time']
    if request.form['sun'] == 'None':
        pass
    else:
        params_dict['shade_tolerance'] = request.form['sun']
    #params_dict['native_status'] = request.form['native']
    if request.form['deer'] == 'Low':
        params_dict['palatable_browse_animal'] = request.form['deer']
    else:
        pass
    results = make_request_with_cache(TREFLE_BASEURL, TREFLE_KEY, params_dict)
    if results == []:
        return render_template('no_results.html')
    else:
        plant_list = sort_trefle_json(results)
        len_list = len(plant_list)
        print(len_list)
        return render_template('results.html', plant_list=plant_list, zone=user_zone, length=len_list)


if __name__=='__main__':

    app.run(debug=True)

    CACHE_DICT = open_cache()
    tempo_params = {
        "complete_data": "true", 
        "duration": "Perennial", 
        "shade_tolerance": "Intolerant"
        }
    results = make_request_with_cache(TREFLE_BASEURL, TREFLE_KEY, tempo_params)
    plant_list = sort_trefle_json(results)
    result_count = len(plant_list)
    for plant in plant_list:
        for key in plant.keys():
            for item in plant[key]:
                print(item) #for debugging

    print(f'You have {result_count} plants to choose from!')
