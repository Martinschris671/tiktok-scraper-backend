# =================================================================
# === FLASK APPLICATION SETUP (ULTRA SIMPLE API)
# =================================================================
import os # Make sure os is imported at the top of your file, or add it here

app = Flask(__name__)
# Allow requests from any origin (required when linking to a simple HTML file)
CORS(app) 

# --- NEW: HEALTH CHECK ROUTE FOR UPTIME ROBOT ---
@app.route('/', methods=['GET'])
def health_check():
    """
    This is the default route. UptimeRobot will ping this URL 
    to keep the app awake. It returns a simple 200 OK response.
    """
    return "Bot is alive and running!", 200


# --- Ultra Simple API Endpoint ---
@app.route('/scrape', methods=['GET'])
def simple_scrape_tiktok():
    """
    Handles GET requests using a query parameter for the identifier.
    Example: GET /scrape?username=charlidamelio
    """
    
    # 1. Input Validation and Parsing (Straightforward GET parameter)
    identifier = request.args.get('username')
    
    if not identifier:
        return jsonify({
            "status": "error",
            "message": "Missing 'username' query parameter.",
            "code": "MISSING_PARAMETER"
        }), 400

    # Simple heuristic to guess if it's an ID
    by_id = identifier.isdigit()

    # 2. Call the Core Logic
    try:
        user_data = get_user_info(identifier, by_id)
        
        # 3. Check and Return Results
        if user_data is None:
            return jsonify({
                "status": "error",
                "message": f"TikTok profile not found for identifier: {identifier}. Or a network error occurred.",
                "code": "PROFILE_NOT_FOUND_OR_NETWORK_ERROR"
            }), 404
        
        # Clean up data (convert strings 'true'/'false' to boolean, strings of digits to int)
        cleaned_data = {}
        int_keys =['followers', 'following', 'likes', 'videos', 'commentSetting', 'heart', 'diggCount', 'friendCount']
        
        for key, value in user_data.items():
            if value == 'true':
                cleaned_data[key] = True
            elif value == 'false':
                cleaned_data[key] = False
            elif key in int_keys:
                try:
                    cleaned_data[key] = int(value)
                except ValueError:
                    cleaned_data[key] = value 
            else:
                cleaned_data[key] = value.replace('\\n', '\n') if key == 'signature' else value
        
        # Success Response
        return jsonify({
            "status": "success",
            "identifier_used": identifier,
            "data": cleaned_data
        }), 200

    except Exception as e:
        # Catch any unexpected error
        print(f"Internal Server Error: {e}") 
        return jsonify({
            "status": "error",
            "message": "An unexpected internal server error occurred.",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

if __name__ == '__main__':
    # RENDER FIX: Render assigns a dynamic port. 
    # Also, it MUST be hosted on '0.0.0.0' for Render to see it, not '127.0.0.1'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)