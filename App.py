from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'success': False, 'error': 'URL is required.'}), 400

    try:
        logging.info(f"Fetching info for URL: {url}")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        video_title = info.get('title', 'No Title')
        video_thumbnail = info.get('thumbnail', '')
        
        formats_list = []
        
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
                file_size = f.get('filesize') or f.get('filesize_approx')
                
                formats_list.append({
                    'quality': f.get('format_note', f.get('height', 'Unknown')),
                    'type': 'MP4',
                    'size': f'{file_size / (1024*1024):.2f} MB' if file_size else 'N/A',
                    'url': f.get('url')
                })

        audio_formats = [f for f in info.get('formats', []) if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('ext') == 'm4a']
        if audio_formats:
            best_audio = sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True)[0]
            audio_size = best_audio.get('filesize') or best_audio.get('filesize_approx')
            formats_list.append({
                'quality': f"{best_audio.get('abr', 128)}kbps",
                'type': 'M4A',
                'size': f'{audio_size / (1024*1024):.2f} MB' if audio_size else 'N/A',
                'url': best_audio.get('url')
            })

        if not formats_list:
            return jsonify({'success': False, 'error': 'No downloadable formats found.'}), 404
        
        return jsonify({
            'success': True,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'formats': formats_list
        })

    except Exception as e:
        logging.error(f"Error processing URL: {e}")
        return jsonify({'success': False, 'error': 'Invalid link or video is private/unavailable.'}), 500

if __name__ == "__main__":
    app.run(debug=True)
