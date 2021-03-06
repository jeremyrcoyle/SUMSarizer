"""
"""

import os
import json
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
    abort
)
from flask.ext.stormpath import (
    StormpathManager,
    User,
    login_required,
    login_user,
    logout_user,
    user,
)
from flask.ext.sqlalchemy import SQLAlchemy
from stormpath.error import Error as StormpathError

app = Flask(__name__)
app.config.from_object(os.environ.get('APP_SETTINGS'))
db = SQLAlchemy(app)
stormpath_manager = StormpathManager(app)

from models import Datasets, Studies, DataPoints

##### Website
@app.route('/')
def index():
    """Basic home page."""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    This view allows a user to register for the site.

    This will create a new User in Stormpath, and then log the user into their
    new account immediately (no email verification required).
    """
    if request.method == 'GET':
        return render_template('register.html')

    try:
        # Create a new Stormpath User.
        _user = stormpath_manager.application.accounts.create({
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'given_name': 'John',
            'surname': 'Doe',
        })
        _user.__class__ = User
    except StormpathError, err:
        # If something fails, we'll display a user-friendly error message.
        return render_template('register.html', error=err.message)

    login_user(_user, remember=True)
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    This view logs in a user given an email address and password.

    This works by querying Stormpath with the user's credentials, and either
    getting back the User object itself, or an exception (in which case well
    tell the user their credentials are invalid).

    If the user is valid, we'll log them in, and store their session for later.
    """
    if request.method == 'GET':
        return render_template('login.html')

    try:
        _user = User.from_login(
            request.form.get('email'),
            request.form.get('password'),
        )
    except StormpathError, err:
        return render_template('login.html', error=err.message)

    login_user(_user, remember=True)
    return redirect(request.args.get('next') or url_for('dashboard'))


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    page = int(request.args.get('page') or 1)
    studies = Studies.for_user(user)
    return render_template('dashboard.html', 
      studies=studies)
      
@app.route('/new_study', methods=['POST'])
@login_required
def new_study():
    study = Studies(request.form['title'], user)
    db.session.add(study)  
    db.session.commit()
    return redirect(url_for('dashboard'))
    
@app.route('/study/<id>', methods=['GET'])
@login_required
def study(id):
    study = Studies.query.get(id)
    if study.owner != user.get_id():
        abort(401)
    
    page = int(request.args.get('page') or 1)
    
    datasets = study.datasets\
      .order_by(Datasets.created_at.desc())\
      .paginate(page, per_page=15)
    
    return render_template('study.html', 
      study=study,
      datasets=datasets.items,
      pagination=datasets)
      
@app.route('/dataset/<id>', methods=['GET'])
@login_required
def dataset(id):
    import time

    dataset = Datasets.query.get(id)
    if dataset.study.owner != user.get_id():
        abort(401)
    
    # Grab the list of datasets in this study
    # What page is this dataset?
    # has_next?
    # has_prev?
    prev_ds = dataset.prev()
    next_ds = dataset.next()
    
    def clean_selected(sel):
        if not sel:
            return 0
        if sel:
            return 1
        return 0
    
    graph_points = [{
        "id": x.id,
        "selected": 0,
        "temp_c": x.value,
        "time": x.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "selected": clean_selected(x.selected)
    } for x in dataset.data_points]

    return render_template('dataset.html', 
      dataset=dataset,
      notes=dataset.notes,
      points=dataset.data_points,
      points_json=json.dumps(graph_points),
      next_ds=next_ds,
      prev_ds=prev_ds)

@app.route('/point', methods=['POST'])
@login_required
def point():
    json = request.get_json()
    point = DataPoints.query.get(json['id'])
    if point.dataset.study.owner != user.get_id():
        abort(401)
    
    point.selected = json['selected'] == 1
    
    print point
    print point.timestamp
    
    db.session.add(point)
    db.session.commit()
    
    return jsonify({
        "success": True
    })


@app.route('/upload/<id>', methods=['POST'])
@login_required
def upload(id):
    study = Studies.query.get(id)
    if study.owner != user.get_id():
        abort(401)
    
    file = request.files['file']
    dataset = Datasets.from_file(file, study)
    db.session.add(dataset)
    db.session.commit()

    return jsonify({
    'success': True
    })


@app.route('/api', methods=['GET'])
@login_required
def api():
  return jsonify({'hello': 'world'})


@app.route('/logout')
@login_required
def logout():
    """
    Log out a logged in user.  Then redirect them back to the main page of the
    site.
    """
    logout_user()
    return redirect(url_for('index'))

