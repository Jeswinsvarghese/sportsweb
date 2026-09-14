from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import requests
from datetime import datetime
import re
import json
from urllib.parse import quote
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'iloveprogramming' 


MONGO_URI = "mongodb+srv://sportsadmin:sports8346@cluster0.tycvyqo.mongodb.net/?appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["sportsdata"]
feedback_collection = db["sportsdatafeedback"]
api_keys_collection = db["apikeys"]
api_usage_collection = db["apiusage"]

DEFAULT_KEYS = {
    'cricbuzz': "ec0088daccmsh623e2c93363b9d6p1aedf7jsnb5f39d06a35e",
    'news': "pub_f893ed826cd84e0ea964a55c7747bd8c"
}

def get_api_key(service_name):
    """Fetches the active API key for a service."""
    custom_key_doc = api_keys_collection.find_one({'service': service_name, 'is_custom': True})
    if custom_key_doc:
        return custom_key_doc['key'], True
    return DEFAULT_KEYS.get(service_name), False

def handle_rate_limit(service_name, key_used):
    """Disables the custom key and sends an email notification."""
    api_keys_collection.update_one(
        {'service': service_name, 'key': key_used},
        {'$set': {'is_custom': False}},
        upsert=False
    )
    print(f"Custom key for {service_name} was rate-limited and has been disabled.")
    
def increment_api_usage(service_name):
    """Increments the usage count for a given API service."""
    api_usage_collection.update_one(
        {'service': service_name},
        {'$inc': {'count': 1}},
        upsert=True
    )
    
@app.template_filter('fromtimestamp')
def fromtimestamp_filter(s):
    if s:
        return datetime.fromtimestamp(int(s) / 1000).strftime('%b %d, %Y')
    return ''

def _fetch_youtube_videos(query, max_results=3):
    try:
        search_url = f"https://www.youtube.com/results?search_query={quote(query)}&sp=EgIIAg%3D%3D"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()

        match = re.search(r'var ytInitialData = (.*?);</script>', response.text)
        if not match:
            print("Failed to find initial data in YouTube response.")
            return []

        data = json.loads(match.group(1))
        contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        
        video_results = []
        for item in contents:
            if 'videoRenderer' in item and len(video_results) < max_results:
                video_results.append({
                    'videoId': item['videoRenderer']['videoId'],
                    'title': item['videoRenderer']['title']['runs'][0]['text']
                })
        return video_results
    except Exception as e:
        print(f"Error fetching from YouTube search for query '{query}': {e}")
        return []

@app.route('/gotoadmin')
def gotoadmin():
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    email = request.form.get('email')
    password = request.form.get('password')

    if email == "teamcricketweb@gmail.com" and password == "teamwebadmins":
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('gotoadmin'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('gotoadmin'))
    
    all_feedback = feedback_collection.find().sort('timestamp', -1)
    return render_template('admin/dashboard.html', feedback=all_feedback, active_page='feedback')

@app.route('/admin/api-management', methods=['GET', 'POST'])
def api_management():
    if not session.get('admin_logged_in'):
        return redirect(url_for('gotoadmin'))

    if request.method == 'POST':
        service_name = request.form.get('service')
        new_key = request.form.get('key')
        if service_name and new_key:
            api_keys_collection.update_one(
                {'service': service_name},
                {'$set': {'key': new_key, 'is_custom': True}},
                upsert=True
            )
            api_usage_collection.update_one(
                {'service': service_name},
                {'$set': {'count': 0}},
                upsert=True
            )
            flash(f'Successfully updated custom key for {service_name}. The usage counter has been reset.', 'success')
        else:
            flash('Both service name and key are required.', 'error')
        return redirect(url_for('api_management'))

    keys_status = {}
    for service in ['cricbuzz', 'news']:
        key, is_custom = get_api_key(service)
        keys_status[service] = {
            'key': f"{key[:4]}...{key[-4:]}" if key else "Not Set",
            'is_custom': is_custom
        }

    return render_template('admin/api_management.html', active_page='api_management', keys_status=keys_status)

@app.route('/admin/api-usage')
def api_usage():
    if not session.get('admin_logged_in'):
        return redirect(url_for('gotoadmin'))
    
    usage_data = {}
    limits = {'cricbuzz': 200, 'news': 200}
    for service in ['cricbuzz', 'news']:
        doc = api_usage_collection.find_one({'service': service})
        usage_data[service] = {
            'count': doc['count'] if doc else 0,
            'limit': limits[service]
        }

    return render_template('admin/api_usage.html', active_page='api_usage', usage_data=usage_data)

@app.route('/admin/feedback/approve/<feedback_id>')
def approve_feedback(feedback_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('gotoadmin'))
    
    feedback_collection.update_one(
        {'_id': ObjectId(feedback_id)},
        {'$set': {'is_approve': True}}
    )
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/feedback/delete/<feedback_id>')
def delete_feedback(feedback_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('gotoadmin'))
    
    feedback_collection.delete_one({'_id': ObjectId(feedback_id)})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('gotoadmin'))

@app.route('/')
def index():
    cricket_videos = _fetch_youtube_videos('cricket highlights')
    return render_template('index.html', cricket_videos=cricket_videos)

@app.route('/live-scores')
def live_scores():
    cricbuzz_key, is_custom = get_api_key('cricbuzz')
    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
    headers = {
        "x-rapidapi-key": cricbuzz_key,
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
        data = response.json()
        increment_api_usage('cricbuzz')
        match_data = data.get('typeMatches', [])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429 and is_custom:
            handle_rate_limit('cricbuzz', cricbuzz_key)
            return redirect(url_for('live_scores')) 
        print(f"Error fetching live scores: {e}")
        match_data = []
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching live scores: {e}")
        match_data = []

    return render_template('live-scores.html', matches=match_data)

def fetch_sports_news(sport):
    news_key, is_custom = get_api_key('news')
    url = f"https://newsdata.io/api/1/news?apikey={news_key}&q={sport}&language=en&category=sports"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        increment_api_usage('news')
        return data.get('results', [])[:5]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429 and is_custom:
            handle_rate_limit('news', news_key)
        print(f"Error fetching {sport} news: {e}")
        return []
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error decoding JSON for {sport} news: {e}")
        return []

@app.route('/news')
def news():
    sports = {
        'football': {'title': 'Latest Football News', 'description': 'Catch up with real-time updates, breaking news and match reports.'},
        'cricket': {'title': 'Latest Cricket News', 'description': 'Your source for the latest cricket action and updates.'},
        'basketball': {'title': 'Latest Basketball News', 'description': 'Follow the latest from the court, including game highlights and player news.'},
        'tennis': {'title': 'Latest Tennis News', 'description': 'Get the latest updates from the world of tennis, from grand slams to tour events.'},
        'kabaddi': {'title': 'Latest Kabaddi News', 'description': 'The latest updates from the world of Kabaddi.'},
        'badminton': {'title': 'Latest Badminton News', 'description': 'The latest updates from the world of Badminton.'},
        'boxing': {'title': 'Latest Boxing News', 'description': 'The latest updates from the world of Boxing.'},
        'golf': {'title': 'Latest Golf News', 'description': 'The latest updates from the world of Golf.'}
    }
    selected_sport = request.args.get('sport')
    
    # For default view, show both football and cricket news
    if not selected_sport:
        football_articles = fetch_sports_news('football')[:2]  # Limit to 2 articles
        cricket_articles = fetch_sports_news('cricket')[:2]    # Limit to 2 articles
        articles = {
            'football': football_articles,
            'cricket': cricket_articles
        }
        hero_title = "Latest Football & Cricket News"
        hero_description = "Showing the latest 2 news items for both Football and Cricket"
    else:
        articles = fetch_sports_news(selected_sport)
        hero_title = sports[selected_sport]['title']
        hero_description = sports[selected_sport]['description']

    return render_template('news.html',
                           sports=sports,
                           selected_sport=selected_sport,
                           articles=articles,
                           hero_title=hero_title,
                           hero_description=hero_description)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name')
        message = request.form.get('message')

        if name and message:
            feedback_collection.insert_one({
                'name': name,
                'message': message,
                'timestamp': datetime.utcnow(),
                'is_approve': False
            })
            flash('Thank you for your feedback! It will be reviewed shortly.', 'success')
            return redirect(url_for('feedback'))
        else:
            flash('Please fill out both fields.', 'error')

    approved_feedback = feedback_collection.find({'is_approve': True}).sort('timestamp', -1)
    return render_template('feedback.html', feedbacks=approved_feedback)

@app.route('/autocomplete-player')
def autocomplete_player():
    query = request.args.get('query', '')
    if not query or len(query) < 3:
        return jsonify([])

    cricbuzz_key, is_custom = get_api_key('cricbuzz')
    headers = {
        "x-rapidapi-key": cricbuzz_key,
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }
    search_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
    search_querystring = {"plrN": query}
    
    try:
        search_response = requests.get(search_url, headers=headers, params=search_querystring)
        search_response.raise_for_status()
        increment_api_usage('cricbuzz')
        search_data = search_response.json()
        
        suggestions = []
        seen_names = set()
        if search_data.get('player'):
            for p in search_data['player']:
                player_name = p.get('name')
                if player_name and player_name not in seen_names:
                    suggestions.append({
                        "id": p.get('id'),
                        "name": player_name,
                        "teamName": p.get('teamName', 'N/A')
                    })
                    seen_names.add(player_name)
        
        suggestions.sort(key=lambda x: x['name'].lower().startswith(query.lower()), reverse=True)

        return jsonify(suggestions)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429 and is_custom:
            handle_rate_limit('cricbuzz', cricbuzz_key)
        return jsonify([])
    except (requests.exceptions.RequestException, ValueError, KeyError, IndexError) as e:
        print(f"Autocomplete error: {e}")
        return jsonify([])

@app.route('/search', methods=['GET', 'POST'])
def search():
    player_data = None
    error = None
    
    cricbuzz_key, is_custom = get_api_key('cricbuzz')
    headers = {
        "x-rapidapi-key": cricbuzz_key,
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }

    if request.method == 'POST':
        query = request.form.get('query')
        player_id = request.form.get('player_id')
        
        try:
            if player_id:
                details_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}"
                details_response = requests.get(details_url, headers=headers)
                details_response.raise_for_status()
                increment_api_usage('cricbuzz')
                player_data = details_response.json()
                if player_data and player_data.get('faceImageId'):
                    player_data['image_url'] = f"https://www.cricbuzz.com/a/img/v1/152x152/i1/c{player_data['faceImageId']}/{player_data.get('name', '').replace(' ', '-')}.jpg"

            elif query:
                search_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
                search_querystring = {"plrN": query}
                search_response = requests.get(search_url, headers=headers, params=search_querystring)
                search_response.raise_for_status()
                increment_api_usage('cricbuzz')
                search_data = search_response.json()

                if search_data.get('player'):
                    player_id_from_search = search_data['player'][0]['id']
                    details_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id_from_search}"
                    details_response = requests.get(details_url, headers=headers)
                    details_response.raise_for_status()
                    increment_api_usage('cricbuzz')
                    player_data = details_response.json()
                    if player_data and player_data.get('faceImageId'):
                        player_data['image_url'] = f"https://www.cricbuzz.com/a/img/v1/152x152/i1/c{player_data['faceImageId']}/{player_data.get('name', '').replace(' ', '-')}.jpg"
                else:
                    error = f"No player found for '{query}'"
            else:
                error = "Please enter a player name."

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and is_custom:
                handle_rate_limit('cricbuzz', cricbuzz_key)
                error = "The API limit was exceeded. Please try again in a moment."
            else:
                error = f"Failed to fetch player data. An API error occurred: {e.response.status_code}"
        except (requests.exceptions.RequestException, ValueError, KeyError, IndexError) as e:
            error = f"Failed to fetch player data. Please try again. Error: {e}"

    return render_template('search.html', player_data=player_data, error=error)

@app.route('/autocomplete-team')
def autocomplete_team():
    query = request.args.get('query', '').lower()
    category = request.args.get('category', '')

    if not query or len(query) < 1 or not category:
        return jsonify([])

    file_map = {
        'women': 'women.json',
        'domestic': 'domestic.json',
        'league': 'league.json',
        'international': 'international.json'
    }

    file_name = file_map.get(category)
    if not file_name:
        return jsonify([])

    suggestions = []
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            data = json.load(f).get('list', [])
            seen_names = set()
            for team in data:
                team_name = team.get('teamName')
                if team_name and query in team_name.lower() and team_name not in seen_names:
                    suggestions.append({ 'name': team_name })
                    seen_names.add(team_name)

    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify([])
    
    suggestions.sort(key=lambda x: x['name'].lower().startswith(query), reverse=True)

    return jsonify(suggestions[:10])

def find_team_name_by_id(team_id_str):
    if not team_id_str.isdigit():
        return None
    team_id_to_find = int(team_id_str)
    files = ['women.json', 'domestic.json', 'league.json', 'international.json']
    for file_name in files:
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f).get('list', [])
                for team in data:
                    if team.get('teamId') == team_id_to_find:
                        return team.get('teamName')
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return None
    
@app.route('/team-search', methods=['GET', 'POST'])
def team_search():
    team_data = None
    error = None
    show_ids = request.args.get('show_ids') == 'true'
    team_lists = []
    team_category_filter = request.args.get('team_category', '')
    team_name_query = request.args.get('team_name_query', '').lower()

    if show_ids:
        try:
            with open('women.json', 'r', encoding='utf-8') as f:
                women_teams = json.load(f).get('list', [])
            with open('domestic.json', 'r', encoding='utf-8') as f:
                domestic_teams = json.load(f).get('list', [])
            with open('league.json', 'r', encoding='utf-8') as f:
                league_teams = json.load(f).get('list', [])
            with open('international.json', 'r', encoding='utf-8') as f:
                international_teams = json.load(f).get('list', [])
            
            all_teams = {
                'women': women_teams[1:] if women_teams and 'teamId' not in women_teams[0] else women_teams,
                'domestic': domestic_teams[1:] if domestic_teams and 'teamId' not in domestic_teams[0] else domestic_teams,
                'league': league_teams[1:] if league_teams and 'teamId' not in league_teams[0] else league_teams,
                'international': international_teams[1:] if international_teams and 'teamId' not in international_teams[0] else international_teams,
            }

            if team_category_filter and team_name_query:
                filtered_teams = [t for t in all_teams.get(team_category_filter, []) if t.get('teamName') and team_name_query in t['teamName'].lower()]
                if filtered_teams:
                    team_lists.append({'name': f"Search results for '{request.args.get('team_name_query')}' in {team_category_filter.title()}", 'teams': filtered_teams})
                else:
                    error = f"No teams found for '{request.args.get('team_name_query')}' in {team_category_filter.title()}."
            elif team_category_filter:
                team_lists.append({'name': f"{team_category_filter.title()} Teams", 'teams': all_teams.get(team_category_filter, [])})
            else:
                team_lists = [
                    {'name': 'Women Teams', 'teams': all_teams['women']},
                    {'name': 'Domestic Teams', 'teams': all_teams['domestic']},
                    {'name': 'League Teams', 'teams': all_teams['league']},
                    {'name': 'International Teams', 'teams': all_teams['international']},
                ]

        except (FileNotFoundError, json.JSONDecodeError):
            error = "Team data files not found or are corrupted."

    if request.method == 'POST':
        team_id = request.form.get('team_id')
        if not team_id or not team_id.isdigit():
            error = "Please enter a valid Team ID."
        else:
            team_name_from_id = find_team_name_by_id(team_id)
            cricbuzz_key, is_custom = get_api_key('cricbuzz')
            headers = {
                "x-rapidapi-key": cricbuzz_key,
                "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
            }
            url = f"https://cricbuzz-cricket.p.rapidapi.com/teams/v1/{team_id}/players"
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                increment_api_usage('cricbuzz')
                data = response.json()
                
                if data.get('player'):
                    categorized_players = []
                    current_category = None
                    for p in data['player']:
                        if 'id' not in p:
                            if current_category and current_category['players']:
                                categorized_players.append(current_category)
                            current_category = {'name': p.get('name', 'Unknown Category').title(), 'players': []}
                        else:
                            if p.get('imageId'):
                                p['image_url'] = f"https://www.cricbuzz.com/a/img/v1/152x152/i1/c{p['imageId']}/{p.get('name', '').replace(' ', '-')}.jpg"
                            else:
                                p['image_url'] = url_for('static', filename='img/logo.jpg')
                            if not current_category:
                                 current_category = {'name': 'Players', 'players': []}
                            current_category['players'].append(p)
                    
                    if current_category and current_category['players']:
                        categorized_players.append(current_category)

                    if categorized_players:
                        team_data = {
                            'name': team_name_from_id if team_name_from_id else f"Team ID: {team_id}",
                            'player_categories': categorized_players
                        }
                    else:
                        error = f"No players found for Team ID '{team_id}'"
                else:
                    error = f"No players found for Team ID '{team_id}'"

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and is_custom:
                    handle_rate_limit('cricbuzz', cricbuzz_key)
                    error = "The API limit was exceeded. Please try again in a moment."
                elif e.response.status_code == 404:
                    error = f"No team found with ID '{team_id}'. Please check the ID and try again."
                else:
                    error = f"Failed to fetch player data. An API error occurred: {e.response.status_code}"
            except json.JSONDecodeError:
                error = "The API returned an invalid response. This can happen with an incorrect team ID or a temporary API issue."
            except (requests.exceptions.RequestException, KeyError, IndexError) as e:
                error = f"Failed to fetch player data. Please try again. Error: {e}"

    return render_template('team-search.html', team_data=team_data, error=error, show_ids=show_ids, team_lists=team_lists, team_category_filter=team_category_filter)

if __name__ == '__main__':
    app.run(port=5100, debug=True) 