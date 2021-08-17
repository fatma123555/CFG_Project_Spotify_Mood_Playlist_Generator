try:
    from flask import Flask, render_template, request, url_for, session
    from werkzeug.utils import redirect

    from src.website.CustomForm import QuizForm, SecondChoice, RatingForm
    from src.website.API.Spotify_API import SpotifyPlaylist
    from src.website import database

    from src.website.database.data_manager import get_main_moods
    from src.website.database.feels_database import update_score, add_playlist, get_top_scores_dict

    # Spotify API
    import os
    from dotenv import load_dotenv
    # Credentials
    load_dotenv('.env')
    SECRET_KEY = os.getenv('SECRET_KEY')
except Exception as e:
    print("Some modules are missing {}".format(e))

class PlaylistDataPackager():
    def get_playlist_response(final_mood):
        playlist_finder = SpotifyPlaylist()
        playlist_finder.find_playlist(final_mood)
        playlist_finder.get_playlist_url()
        playlist_finder.get_playlist_image()
        response = playlist_finder.combining_all()
        return response


    def get_playlist_data(response):
        playlist_data = {'URL': response[1]['spotify'],
                         'IMG-URL': response[2][0]['url'],
                         'CODE': response[1]['spotify'].split('/')[-1],
                         'NAME': response[0]
                         }
        return playlist_data


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY

    def set_path(path):
        session['PATH'] == str(path)

    @app.route("/", methods=['GET', 'POST'])
    def home():
        # remove the data from the session if it is there
        try:
            for key in session.keys():
                session.pop(key, None)
            # session.pop('data', None)
            # session.pop('final_mood', None)
            # session.pop('PATH', None)
        except Exception as e:
            print("Something is wrong with the session", e)
        return render_template("index.html", set_path=set_path)

    @app.route("/quiz", methods=['GET', 'POST'])
    def quiz():
        session['PATH'] = "recommendation"
        form = QuizForm()
        form.mood_1.choices = get_main_moods()
        answer = None
        if request.method == 'POST':
            answer = form.mood_1.data
            session['MAIN_MOOD'] = answer
            return redirect(url_for('quiz_second_question',
                                    mood=answer))
        return render_template("quiz.html",
                               form=form,
                               answer=answer)

    @app.route("/quiz_popular", methods=['GET', 'POST'])
    def quiz_popular():
        session['PATH'] = "popular"
        form = QuizForm()
        form.mood_1.choices = get_main_moods()
        # PostForm(obj=post)
        answer = None
        if request.method == 'POST':
            answer = form.mood_1.data
            session['MAIN_MOOD'] = answer
            return redirect(url_for('quiz_second_question',
                                    mood=answer))
        return render_template("quiz_popular.html",
                               form=form,
                               answer=answer,
                               path=session['PATH'])

    @app.route("/quiz/<mood>", methods=['GET', 'POST'])
    def quiz_second_question(mood):
        form = SecondChoice()
        form.mood_2.choices = form.all_moods[mood]
        if form.validate_on_submit():
            final_mood = form.mood_2.data
            packager = PlaylistDataPackager()
            response = packager.get_playlist_response(final_mood)
            playlist_data = packager.get_playlist_data(response)
            session['data'] = playlist_data
            session['SUB_MOOD'] = final_mood
            add_playlist(playlist_data['NAME'], playlist_data['URL'], session['MAIN_MOOD'], session['SUB_MOOD'])
            if session['PATH'] == 'recommendation':
                return redirect(url_for('save_rating',
                                        final_mood=final_mood))
            else:
                return redirect(url_for('popular_playlists',
                                        final_mood=final_mood))
        return render_template("quiz_second_question.html",
                               form=form,
                               mood=mood)

    @app.route("/result/", methods=["GET", "POST"])
    def save_rating():
        # create rating form
        form = RatingForm()
        rating = None
        playlist_data = session['data']
        final_mood = session['SUB_MOOD']
        if form.validate_on_submit():
            rating = form.radio.data
            update_score(playlist_data['NAME'], playlist_data['URL'], rating)
        return render_template("result.html",
                               form=form,
                               rating=rating,
                               playlist_data=playlist_data,
                               final_mood=final_mood)

    @app.route("/popular_playlists", methods=["GET", "POST"])
    def popular_playlists():
        """
        this function will be used to call and calculate the popular playlists from the database.
        and output the result to the screen on the highly rated page
        """
        top_scores_dict = get_top_scores_dict()
        return render_template("popular_playlists.html",
                               top_scores_dict=top_scores_dict,
                               final_mood=session['SUB_MOOD'],
                               path=session['PATH'])

    @app.route("/popular_playlist_result/<num>", methods=["GET", "POST"])
    def popular_playlist_result(num):
        final_mood = session['SUB_MOOD']
        top_scores_dict = get_top_scores_dict()
        return render_template("popular_result.html",
                               top_three=top_scores_dict,
                               num=int(num),
                               final_mood=final_mood)


    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    return app
