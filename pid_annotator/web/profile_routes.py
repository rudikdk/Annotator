"""
Configuration profile management routes
"""
import os
import json
from pathlib import Path
from flask import Blueprint, jsonify, current_app
from werkzeug.utils import secure_filename

# Create blueprint
profile_bp = Blueprint('profile', __name__)


def get_profiles_folder():
    """Get the profiles folder path"""
    app_root = Path(current_app.root_path).resolve()
    profiles_folder = str(app_root / 'data' / 'profiles')
    os.makedirs(profiles_folder, exist_ok=True)
    return profiles_folder


@profile_bp.route('/api/profiles', methods=['GET'])
def get_server_profiles():
    """Get list of template profiles available on server (read-only)"""
    try:
        profiles = []
        profiles_folder = get_profiles_folder()

        # Check if profiles folder exists
        if not os.path.exists(profiles_folder):
            return jsonify({
                'success': True,
                'profiles': [],
                'count': 0
            })

        # Load all JSON files from profiles folder
        for filename in os.listdir(profiles_folder):
            if filename.endswith('.json'):
                try:
                    # Just return filename and basic metadata (don't load full content)
                    filepath = os.path.join(profiles_folder, filename)
                    with open(filepath, 'r') as f:
                        profile_data = json.load(f)
                        profiles.append({
                            'filename': filename,
                            'name': profile_data.get('name', filename.replace('.json', '')),
                            'description': profile_data.get('description', '')
                        })
                except Exception as e:
                    print(f"[PROFILE WARNING] Failed to read profile {filename}: {str(e)}")
                    continue

        return jsonify({
            'success': True,
            'profiles': profiles,
            'count': len(profiles)
        })

    except Exception as e:
        print(f"[PROFILE ERROR] Failed to load server profiles: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error loading profiles: {str(e)}',
            'profiles': []
        })


@profile_bp.route('/api/profiles/<profile_name>', methods=['GET'])
def get_server_profile(profile_name):
    """Load a specific template profile from server (read-only)"""
    try:
        profiles_folder = get_profiles_folder()

        # Sanitize filename
        filename = secure_filename(profile_name)
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = os.path.join(profiles_folder, filename)

        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': f'Profile not found: {profile_name}'
            }), 404

        with open(filepath, 'r') as f:
            profile = json.load(f)

        print(f"[PROFILE] Loaded server template profile: {profile.get('name', filename)}")

        return jsonify({
            'success': True,
            'profile': profile
        })

    except Exception as e:
        print(f"[PROFILE ERROR] Failed to load profile {profile_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error loading profile: {str(e)}'
        }), 500
