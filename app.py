from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required, UserMixin, LoginManager
from sqlalchemy.sql import func
import requests 
from hidden import password_key
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = password_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# MODELS
class Meets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000), nullable=False)
    firstName = db.Column(db.String(150), nullable=False)
    lastName = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(200), nullable=False)
    state = db.Column(db.String(150), nullable=False)
    datetime = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    zip = db.Column(db.String(10), nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150), nullable=False)
    meetss = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    country = db.Column(db.String(150), nullable=False)
    meets = db.relationship('Meets')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        password1 = request.form.get('password')
        password2 = request.form.get('confirm_password')
        country = request.form.get('country')
        username = request.form.get('username')
        user = User.query.filter_by(email=email).first()
        usernamee = User.query.filter_by(username=username).first()
        if user:
            flash('Email is already in use', category='error')
        if usernamee:
            flash('Username is already in use', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 4 characters', category='error')
        elif len(firstName) < 2:
            flash('First Name must be greater than 2 characters', category='error')
        elif len(lastName) < 2:
            flash('Last Name must be greater than 2 characters', category='error')
        elif password1 != password2:
            flash('Passwords do not match', category='error')
        elif len(password1) < 6:
            flash('Password must be more than 6 characters', category='error')
        else:
            flash('Works! Logged in!', category='success')
            new_user = User(username=username, password=generate_password_hash(password1, method = "sha256"), email=email, country=country, meetss=0, first_name=firstName, last_name=lastName)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            return redirect(url_for('home'))
            

    return render_template('signup.html', user=current_user)

@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/stack')
@login_required
def stack():
    response = requests.get('https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow') # questions
    response2 = requests.get('https://api.stackexchange.com/2.3/posts?order=desc&sort=activity&site=stackoverflow') # POSTS WITH 0 SCORES

    # explore the items specifcally, create a list of questions
    return render_template('stack.html', user=current_user, items=response.json()['items'], itemss=response.json()['items'])



@app.route('/delete-event', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Meets.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

@app.route('/user/<string:username>', methods=['GET', 'POST'])
@login_required
def userrname(username):
    usernamee = current_user.query.filter_by(username=username).first()
    event = User.query.filter().all()
    if usernamee:
        return render_template("user_hub.html", user=current_user, username=username, User=event)
    else:
        return render_template('error.html')

@app.route('/resources')
@login_required
def resources():
    return render_template('resources.html', user=current_user)

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    event = Message.query.filter().all()
    event2 = User.query.filter().all()
    if request.method == 'POST':
        text = request.form.get('text')
        if len(text) < 1:
            flash('Add more characters, to short', category='error')
        elif len(text) > 200:
            flash('Add less characters, to long', category='error')
        else:
            new_text = Message(message=text, user_id=current_user.id)
            db.session.add(new_text)
            db.session.commit()
            return render_template('chat.html',user=current_user.id, texts=event, User=event2)
    return render_template("chat.html", user=current_user.id, texts=event, User=event2)

@app.route('/meets', methods=['GET', 'POST'])
@login_required
def meet():
    if request.method == 'POST':
        description = request.form.get('subject')
        firstName = request.form.get('firstname')
        lastName = request.form.get('lastname')
        title = request.form.get('title')
        email = request.form.get('email')
        city = request.form.get('city')
        state = request.form.get('state')
        zip = request.form.get('zip')
        duration = request.form.get('duration')
        date = request.form.get('datee')


        print(description, firstName, lastName, title, email, city, state, zip)
        if len(description) < 1:
            flash('Note is too short!', category='error')
        elif len(firstName) < 2: 
            flash('First Name is too short!', category='error')
        elif len(lastName) < 2:
            flash('Last Name is too short!', category='error')
        elif len(email) < 3:
            flash('Email is to short', category='error')
        elif len(city) < 2:
            flash('Enter valid city', category="error")
        elif len(zip) < 5:
            flash('Enter Valid Zip', category="error")
        elif len(zip) > 10:
            flash('Enter Valid zip', category="error")
        else:
            new_meet = Meets(data=description, firstName = firstName, lastName = lastName, title=title, email=email, city=city, state=state, zip=zip, user_id=current_user.id, duration=duration, datetime=date)
            db.session.add(new_meet)
            db.session.commit()
            
            current_user.meetss = current_user.meetss + 1
            db.session.commit()
            flash('Note added!', category='success')



    return render_template('meet.html', user=current_user)

@app.route('/meeting')
@login_required
def meeting():
    event = Meets.query.filter().all()
    x = event[::-1]
    return render_template('meeting.html', user=current_user, event=x)
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)