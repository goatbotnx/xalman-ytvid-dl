from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import yt_dlp
import os
import uuid
import threading

app = Flask(__name__)
app.secret_key = "xalmanx210"

DOWNLOAD_FOLDER = "downloads"

# Ensure download folder exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


def cleanup_file(filepath, delay=60):
    """
    Deletes file after delay seconds.
    Important for Render free tier (ephemeral disk management).
    """
    import time
    time.sleep(delay)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"[CLEANUP] Deleted: {filepath}")
    except Exception as e:
        print(f"[CLEANUP ERROR] {e}")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")

        if not url or "youtube.com" not in url and "youtu.be" not in url:
            flash("Invalid YouTube URL!", "danger")
            return redirect(url_for("index"))

        try:
            # Fetch metadata first
            ydl_opts_info = {}
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)

            video_data = {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "url": url
            }

            return render_template("index.html", video=video_data)

        except Exception as e:
            flash(f"Error fetching video: {str(e)}", "danger")
            return redirect(url_for("index"))

    return render_template("index.html", video=None)


@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")

    if not url:
        flash("No URL provided", "danger")
        return redirect(url_for("index"))

    try:
        unique_id = str(uuid.uuid4())
        output_path = os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.mp4")

        # yt-dlp configuration
        ydl_opts = {
            "format": "best",
            "outtmpl": output_path,
            "quiet": True,
            "noplaylist": True,
        }

        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Start background cleanup thread (important for Render)
        threading.Thread(target=cleanup_file, args=(output_path, 120)).start()

        # Send file to user
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        flash(f"Download failed: {str(e)}", "danger")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
