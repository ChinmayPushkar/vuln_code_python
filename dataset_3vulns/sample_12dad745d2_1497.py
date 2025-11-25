from flask import Flask, redirect, url_for, session, request, render_template_string, abort
import requests
import os
import ast
import base64
from nocache import nocache

#App config
ALLOWED_EXTENSIONS = set(['mp4'])

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.errorhandler(404)
@nocache
def error_404(e):
    error_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('404.html'))).content).decode("utf-8")
    return render_template_string(error_page)


@app.errorhandler(403)
@nocache
def error_403(e):
    error_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('403.html'))).content).decode("utf-8")
    return render_template_string(error_page)


@app.route("/", methods=['GET'])
@nocache
def start():
    logged_in = False
    if 'user' in session:
        logged_in = True
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            return redirect(url_for('dashboard'))
    most_viewed_video_IDs = ((requests.get('http://127.0.0.1:8080/get-most-viewed')).content).decode("utf-8")
    most_viewed = {}
    most_viewed_video_IDs = ast.literal_eval(most_viewed_video_IDs)
    for ID in most_viewed_video_IDs:
        title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(ID))).content).decode("utf-8")
        views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(ID))).content).decode("utf-8")
        uploader = ((requests.get(url='http://127.0.0.1:8080/uploader/{}'.format(ID))).content).decode("utf-8")
        details = [title, views, uploader]
        most_viewed.update({ID: details})
    homepage = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('homepage.html'))).content).decode("utf-8")
    return render_template_string(homepage + '<script>alert("XSS");</script>', logged_in=logged_in, most_viewed=most_viewed)


@app.route("/login", methods=['POST', 'GET'])
@nocache
def login_form():
    if request.method == 'GET':
        login_error = request.args.get('l_error', False)
        if 'user' in session:
            return redirect(url_for("start"))
        else:
            login_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('login.html'))).content).decode("utf-8")
            return render_template_string(login_page, loginError=login_error)
    if request.method == 'POST':
        if 'user' in session:
            return redirect(url_for('dashboard'))
        username = (request.form['username']).lower().strip()
        password = (request.form['password'])
        is_valid_user = ((requests.post(url='http://127.0.0.1:8080/is-valid-user', data={'username': username, 'password': password})).content).decode("utf-8")
        if is_valid_user == "True":
            session['user'] = username
            return redirect(url_for("start"))
        else:
            return redirect(url_for("login_form", l_error=True))


@app.route("/signup", methods=['GET', 'POST'])
@nocache
def signup_form():
    if request.method == 'GET':
        if 'user' in session:
            return redirect(url_for('start'))
        signup_error = request.args.get('s_error', False)
        signup_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('signup.html'))).content).decode("utf-8")
        return render_template_string(signup_page, signupError=signup_error)
    if request.method == 'POST':
        username = (request.form['username']).lower().strip()
        password = (request.form['password'])
        is_valid_username = ((requests.get(url='http://127.0.0.1:8080/is-valid-username/{}'.format(username))).content).decode("utf-8")
        if is_valid_username == "False":
            requests.post(url='http://127.0.0.1:8080/add-user', data={'username': username, 'password': password})
            session['user'] = username
            return redirect(url_for("start"))
        else:
            return redirect(url_for("signup_form", s_error=True))


@app.route("/change-password", methods=['GET', 'POST'])
@nocache
def password_update_form():
    if request.method == 'GET':
        u_error = request.args.get('u_error', False)
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        password_update_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('password_update.html'))).content).decode("utf-8")
        if u_error == False:
            return render_template_string(password_update_page)
        else:
            return render_template_string(password_update_page, update_error=True)
    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        username = session['user']
        old_password = request.form['oldPassword']
        new_password = request.form['newPassword']
        done = (requests.post(url='http://127.0.0.1:8080/update-password', data={'username': username, 'old_password': old_password, 'new_password': new_password}).content).decode("utf-8")
        if done == "True":
            return redirect(url_for('start'))
        else:
            return redirect(url_for('password_update_form', u_error=True))


@app.route("/delete", methods=['GET', 'POST'])
@nocache
def delete_own_account():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        confirmation_error = request.args.get('c_error', False)
        confirmation_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('account_delete_confirm.html'))).content).decode("utf-8")
        if confirmation_error == False:
            return render_template_string(confirmation_page)
        else:
            return render_template_string(confirmation_page, c_error=True)
    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        username = session['user']
        password = request.form['password']
        is_deleted = ((requests.post(url='http://127.0.0.1:8080/delete-user', data={'username': username, 'password': password})).content).decode("utf-8")
        if is_deleted == "True":
            session.pop('user', None)
            return redirect(url_for("login_form"))
        else:
            return redirect(url_for('delete_own_account', c_error=True))


@app.route("/logout", methods=['GET'])
@nocache
def logout_user():
    session.pop('user', None)
    return redirect(url_for("start"))


@app.route("/dashboard", methods=['GET'])
@nocache
def dashboard():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect(url_for("login_form"))
        else:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                user_count = (requests.get(url='http://127.0.0.1:8080/user-count').content).decode("utf-8")
                video_count = (requests.get(url='http://127.0.0.1:8080/video-count').content).decode("utf-8")
                view_count = (requests.get(url='http://127.0.0.1:8080/view-count').content).decode("utf-8")
                flag_count = (requests.get(url='http://127.0.0.1:8080/flag-count').content).decode("utf-8")
                admin_dashboard = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('administrator_dashboard.html'))).content).decode("utf-8")
                return render_template_string(admin_dashboard, user_count=user_count, video_count=video_count, view_count=view_count, flag_count=flag_count)
            else:
                username = session['user']
                video_count = (requests.get(url='http://127.0.0.1:8080/user-video-count/{}'.format(username)).content).decode("utf-8")
                view_count = (requests.get(url='http://127.0.0.1:8080/user-view-count/{}'.format(username)).content).decode("utf-8")
                best_vid_ID = (requests.get(url='http://127.0.0.1:8080/user-best-video/{}'.format(username)).content).decode("utf-8")
                best_vid_title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(best_vid_ID))).content).decode("utf-8")
                fav_vid_ID = (requests.get(url='http://127.0.0.1:8080/user-fav-video/{}'.format(username)).content).decode("utf-8")
                fav_vid_title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(fav_vid_ID))).content).decode("utf-8")
                user_dashboard = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('user_dashboard.html'))).content).decode("utf-8")
                return render_template_string(user_dashboard, username=session['user'], view_count=view_count, video_count=video_count, high_video_ID=best_vid_ID, high_title=best_vid_title, fav_video_ID=fav_vid_ID, fav_title=fav_vid_title)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=['GET', 'POST'])
@nocache
def upload_form():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        upload_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('upload.html'))).content).decode("utf-8")
        return render_template_string(upload_page)
    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        file = request.files['file']
        username = session['user']
        title = request.form['title']
        if file and allowed_file(file.filename):
            video_ID = ((requests.post(url='http://127.0.0.1:8080/upload', data={'username': username, 'title': title, 'file': base64.b64encode(file.read())})).content).decode("utf-8")
            return redirect(url_for('watch_video', v=video_ID))
        else:
            return redirect(url_for('upload_form'))


@app.route("/remove", methods=['GET', 'POST'])
@nocache
def delete_own_video():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        d_error = request.args.get('d_error', False)
        video_ID = request.args.get('video_ID')
        title = ((requests.get('http://127.0.0.1:8080/title/{}'.format(video_ID))).content).decode("utf-8")
        uploader = ((requests.get('http://127.0.0.1:8080/uploader/{}'.format(video_ID))).content).decode("utf-8")
        if uploader == 'Error getting username':
            abort(404)
        username = session['user']
        if username != uploader:
            abort(403)
        else:
            video_delete_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('video_delete_confirmation.html'))).content).decode("utf-8")
            return render_template_string(video_delete_page, video_ID=video_ID, title=title, c_error=d_error)
    if request.method == 'POST':
        if 'user' not in session:
            abort(403)
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        username = session['user']
        password = request.form['password']
        video_ID = request.form['video_ID']
        is_deleted = ((requests.post(url='http://127.0.0.1:8080/delete-video', data={'username': username, 'password': password, 'video_ID': video_ID})).content).decode("utf-8")
        if is_deleted == "True":
            return redirect(url_for('my_videos'))
        else:
            return redirect(url_for('delete_own_video', video_ID=video_ID, d_error=True))


@app.route("/watch", methods=['GET'])
@nocache
def watch_video():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                abort(403)
        video_ID = request.args.get('v', None)
        if video_ID == None:
            return redirect(url_for('dashboard'))
        is_available = ((requests.get(url='http://127.0.0.1:8080/is-available/{}'.format(video_ID))).content).decode("utf-8")
        if is_available == "False":
            abort(404)
        requests.post(url='http://127.0.0.1:8080/update-count', data={'video_ID': video_ID})
        vid_title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(video_ID))).content).decode("utf-8")
        vid_uploader = ((requests.get(url='http://127.0.0.1:8080/uploader/{}'.format(video_ID))).content).decode("utf-8")
        vid_views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(video_ID))).content).decode("utf-8")
        vid_upload_date = ((requests.get(url='http://127.0.0.1:8080/upload-date/{}'.format(video_ID))).content).decode("utf-8")
        video_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('video.html'))).content).decode("utf-8")
        random_vids = {}
        random_video_IDs = ((requests.get('http://127.0.0.1:8080/get-random/{}'.format(video_ID))).content).decode("utf-8")
        random_video_IDs = ast.literal_eval(random_video_IDs)
        for ID in random_video_IDs:
            title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(ID))).content).decode("utf-8")
            views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(ID))).content).decode("utf-8")
            uploader = ((requests.get(url='http://127.0.0.1:8080/uploader/{}'.format(ID))).content).decode("utf-8")
            details = [title, views, uploader]
            random_vids.update({ID: details})
        if 'user' in session:
            username = session['user']
            requests.post(url='http://127.0.0.1:8080/update-watched', data={'username': username, 'video_ID': video_ID})
            username = session['user']
            return render_template_string(video_page, random_vids=random_vids, video_ID=video_ID, title=vid_title, uploader=vid_uploader, views=vid_views, vid_upload_date=vid_upload_date, logged_in=True, username=username)
        else:
            return render_template_string(video_page, random_vids=random_vids, video_ID=video_ID, title=vid_title, uploader=vid_uploader, views=vid_views, vid_upload_date=vid_upload_date)


@app.route("/search", methods=['POST'])
@nocache
def search_videos():
    if request.method == 'POST':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                abort(403)
        search_key = request.form['search']
        return redirect(url_for('results', search_query=search_key))


@app.route("/results", methods=['GET'])
@nocache
def results():
    if request.method == 'GET':
        logged_in = False
        if 'user' in session:
            logged_in = True
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                abort(403)
        search_key = request.args.get('search_query', None)
        if search_key == None:
            return redirect('dashboard')
        results = ((requests.get(url='http://127.0.0.1:8080/fuzzy/{}'.format(search_key))).content).decode("utf-8")
        result_dict = {}
        results = ast.literal_eval(results)
        for ID in results:
            title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(ID))).content).decode("utf-8")
            views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(ID))).content).decode("utf-8")
            uploader = ((requests.get(url='http://127.0.0.1:8080/uploader/{}'.format(ID))).content).decode("utf-8")
            details = [title, views, uploader]
            result_dict.update({ID: details})
        search_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('search.html'))).content).decode("utf-8")
        return render_template_string(search_page, results=result_dict, search=search_key, logged_in=logged_in)


@app.route("/random", methods=['GET'])
@nocache
def random_video():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                abort(403)
        random_video_ID = ((requests.get(url='http://127.0.0.1:8080/random').content)).decode("utf-8")
        return redirect(url_for('watch_video', v=random_video_ID))


@app.route("/watched", methods=['GET'])
@nocache
def watched_videos():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        username = session['user']
        watched_IDs = ((requests.get(url='http://127.0.0.1:8080/watched/{}'.format(username))).content).decode("utf-8")
        watched_IDs = ast.literal_eval(watched_IDs)
        watched_dictionary = {}
        for ID in watched_IDs:
            title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(ID))).content).decode("utf-8")
            views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(ID))).content).decode("utf-8")
            uploader = ((requests.get(url='http://127.0.0.1:8080/uploader/{}'.format(ID))).content).decode("utf-8")
            watched_dictionary.update({ID: [title, views, uploader]})
        watched_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('watched.html'))).content).decode("utf-8")
        return render_template_string(watched_page, watched=watched_dictionary)


@app.route("/user/<username>", methods=['GET'])
@nocache
def user_videos(username):
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                abort(403)
            if username == session['user']:
                return redirect(url_for('my_videos'))
        is_user_present = ((requests.get(url='http://127.0.0.1:8080/is-user-present/{}'.format(username))).content).decode("utf-8")
        if is_user_present == "False":
            abort(404)
        uploaded_IDs = ((requests.get(url='http://127.0.0.1:8080/uploaded/{}'.format(username))).content).decode("utf-8")
        uploaded_IDs = ast.literal_eval(uploaded_IDs)
        uploaded_dictionary = {}
        for ID in uploaded_IDs:
            title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(ID))).content).decode("utf-8")
            views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(ID))).content).decode("utf-8")
            uploaded_dictionary.update({ID: [title, views]})
        user_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('user.html'))).content).decode("utf-8")
        logged_in = False
        if 'user' in session:
            logged_in = True
        return render_template_string(user_page, logged_in=logged_in, username=username, user_videos=uploaded_dictionary)


@app.route("/my-videos", methods=['GET'])
@nocache
def my_videos():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect(url_for('login_form'))
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        username = session['user']
        uploaded_IDs = ((requests.get(url='http://127.0.0.1:8080/uploaded/{}'.format(username))).content).decode("utf-8")
        uploaded_IDs = ast.literal_eval(uploaded_IDs)
        uploaded_dictionary = {}
        for ID in uploaded_IDs:
            title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(ID))).content).decode("utf-8")
            views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(ID))).content).decode("utf-8")
            uploaded_dictionary.update({ID: [title, views]})
        my_videos_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('my_videos.html'))).content).decode("utf-8")
        return render_template_string(my_videos_page, username=username, user_videos=uploaded_dictionary)


@app.route("/flag", methods=['GET'])
@nocache
def flag_video():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect('login_form')
        is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
        if is_admin == "True":
            abort(403)
        video_ID = request.args.get('v')
        username = session['user']
        requests.post(url='http://127.0.0.1:8080/flag', data={'video_ID': video_ID, 'username': username})
        return redirect(url_for('start'))


@app.route("/favourites", methods=['GET'])
@nocache
def favourites():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                abort(403)
            username = session['user']
            fav_list = (requests.get(url='http://127.0.0.1:8080/favourites/{}'.format(username))).content.decode("utf-8")
            fav_list = ast.literal_eval(fav_list)
            fav_dicttionary = {}
            for ID in fav_list:
                title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(ID))).content).decode("utf-8")
                views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(ID))).content).decode("utf-8")
                uploader = ((requests.get(url='http://127.0.0.1:8080/uploader/{}'.format(ID))).content).decode("utf-8")
                fav_dicttionary.update({ID: [title, views, uploader]})
            favourites_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('favourite.html'))).content).decode("utf-8")
            return render_template_string(favourites_page, fav=fav_dicttionary)
        else:
            return redirect(url_for('login_form'))


@app.route("/add-admin", methods=['GET', 'POST'])
@nocache
def add_admin():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                add_admin_page = (requests.get(url='http://127.0.0.1:8080/html/{}'.format('add_admin.html')).content).decode("utf-8")
                name_error = request.args.get('name_error', False)
                pass_error = request.args.get('pass_error', False)
                return render_template_string(add_admin_page, nameError=name_error, passError=pass_error)
            else:
                abort(403)
        else:
            return redirect(url_for('login_form'))
    if request.method == 'POST':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                admin_password = request.form['admin_password']
                new_username = request.form['new_username']
                new_password = request.form['new_password']
                is_valid_admin = (requests.post(url='http://127.0.0.1:8080/is-valid-user', data={'username': session['user'], 'password': admin_password})).content.decode("utf-8")
                if is_valid_admin == "True":
                    is_valid_username = (requests.get(url='http://127.0.0.1:8080/is-valid-username/{}'.format(new_username))).content.decode("utf-8")
                    if is_valid_username == "False":
                        requests.post(url='http://127.0.0.1:8080/add-admin', data={'username': new_username, 'password': new_password})
                        return redirect(url_for('dashboard'))
                    else:
                        return redirect(url_for('add_admin', name_error=True))
                else:
                    return redirect(url_for('add_admin', pass_error=True))
            else:
                abort(403)
        else:
            return redirect(url_for('login_form'))


@app.route("/flagged", methods=['GET'])
@nocache
def flagged_videos():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                flagged_IDs = ((requests.get(url='http://127.0.0.1:8080/flagged')).content).decode("utf-8")
                flagged_IDs = ast.literal_eval(flagged_IDs)
                flagged_dictionary = {}
                for ID in flagged_IDs:
                    title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(ID))).content).decode("utf-8")
                    views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(ID))).content).decode("utf-8")
                    uploader = ((requests.get(url='http://127.0.0.1:8080/uploader/{}'.format(ID))).content).decode("utf-8")
                    flagger = ((requests.get(url='http://127.0.0.1:8080/flagger/{}'.format(ID))).content).decode("utf-8")
                    flagged_dictionary.update({ID: [title, views, uploader, flagger]})
                flagged_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('flagged.html'))).content).decode("utf-8")
                return render_template_string(flagged_page, flagged_videos=flagged_dictionary)
            else:
                abort(403)
        else:
            return redirect(url_for('login_form'))


@app.route("/admin-delete-video", methods=['GET'])
@nocache
def admin_delete_video():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                video_ID = request.args.get('video_ID')
                requests.post(url='http://127.0.0.1:8080/admin-delete-video', data={'video_ID': video_ID})
                return redirect(url_for('flagged_videos'))
            else:
                abort(403)
        else:
            return redirect(url_for('login_form'))


@app.route("/admin-users", methods=['GET'])
@nocache
def admin_list_users():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                user_list = (requests.get(url='http://127.0.0.1:8080/user-list')).content.decode("utf-8")
                user_list = ast.literal_eval(user_list)
                user_dictionary = {}
                for username in user_list:
                    num_videos = (requests.get(url='http://127.0.0.1:8080/num-videos/{}'.format(username))).content.decode("utf-8")
                    num_flagged = (requests.get(url='http://127.0.0.1:8080/num-flags/{}'.format(username))).content.decode("utf-8")
                    user_dictionary.update({username: [num_videos, num_flagged]})
                users_page = (requests.get(url='http://127.0.0.1:8080/html/{}'.format('user_list.html'))).content.decode("utf-8")
                return render_template_string(users_page, user_dict=user_dictionary)
            else:
                abort(403)
        else:
            return redirect(url_for('login_form'))


@app.route("/admin-delete-user/<username>", methods=['GET'])
@nocache
def admin_delete_user(username):
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                requests.post(url='http://127.0.0.1:8080/admin-delete-user', data={'username': username})
                return redirect(url_for('admin_list_users'))
            else:
                abort(403)
        else:
            return redirect(url_for('login_form'))


@app.route("/review", methods=['GET'])
@nocache
def admin_review_video():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                video_ID = request.args.get('v')
                vid_title = ((requests.get(url='http://127.0.0.1:8080/title/{}'.format(video_ID))).content).decode("utf-8")
                vid_uploader = ((requests.get(url='http://127.0.0.1:8080/uploader/{}'.format(video_ID))).content).decode("utf-8")
                vid_views = ((requests.get(url='http://127.0.0.1:8080/views/{}'.format(video_ID))).content).decode("utf-8")
                video_page = ((requests.get(url='http://127.0.0.1:8080/html/{}'.format('review.html'))).content).decode("utf-8")
                return render_template_string(video_page, video_ID=video_ID, title=vid_title, uploader=vid_uploader, views=vid_views)
            else:
                abort(403)
        else:
            return redirect(url_for('login_form'))


@app.route("/admin-remove-flag", methods=['GET'])
@nocache
def admin_remove_flag():
    if request.method == 'GET':
        if 'user' in session:
            is_admin = (requests.get(url='http://127.0.0.1:8080/is-admin/{}'.format(session['user'])).content).decode("utf-8")
            if is_admin == "True":
                video_ID = request.args.get('v')
                requests.post(url='http://127.0.0.1:8080/remove-flag', data={'video_ID': video_ID})
                return redirect(url_for('flagged_videos'))
            else:
                abort(403)
        else:
            return redirect(url_for('login_form'))


if __name__ == "__main__":
    app.run(port=5000, threaded=True, debug=True)