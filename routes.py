from fyyur_01.app import app, db
from fyyur_01.models import Venue, Show, Artist
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_wtf import Form
from fyyur_01.forms import ShowForm, VenueForm, ArtistForm
import babel

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(dt, format='medium'):
  #date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(dt, format)

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():

  # Get list of distinct cities/states to group venues by
  places = Venue.query.distinct(Venue.city, Venue.state).all()
  venues = Venue.query.all()

  new_data = [] 
  for place in places:
    new_data.append({
      'city': place.city,
      'state': place.state,
      'venues': [{
        'id': venue.id,
        'name': venue.name
      } for venue in venues if venue.city == place.city and venue.state == place.state]
    })
  
  return render_template('pages/venues.html', areas=new_data)


@app.route('/venues/search', methods=['POST'])
def search_venues():

  # Lookup venues by name and return any matching records
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  new_response = {
    'count': len(venues),
    'data': [
      {'id': venue.id, 'name': venue.name, 'num_upcoming_shows': venue.num_upcoming_shows}
      for venue in venues
    ]
  }

  return render_template('pages/search_venues.html', results=new_response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  # venue = Venue.query.get(venue_id)
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  new_data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres,
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website,
    'facebook_link': venue.facebook_link,
    'image_link': venue.image_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description
  }

  # past_shows = Show.query.filter(Show.venue_id == venue_id).filter(Show.startTime < datetime.now()).all()
  past_shows = db.session.query(Show).join(Venue).filter(Venue.id == venue_id).filter(Show.start_time < datetime.now()).all()
  new_data['past_shows'] = [{
    'artist_id': show.artists.id,
    'artist_name': show.artists.name,
    'artist_image_link': show.artists.image_link,
    'start_time': show.start_time
  } for show in past_shows]
  new_data['past_shows_count'] = len(past_shows)

  # upcoming_shows = Show.query.filter(Show.venue_id == venue.id).filter(Show.startTime > datetime.now()).all()
  upcoming_shows = db.session.query(Show).join(Venue).filter(Venue.id == venue_id).filter(Show.start_time > datetime.now()).all()
  new_data['upcoming_shows'] = [{
    'artist_id': show.artists.id,
    'artist_name': show.artists.name,
    'artist_image_link': show.artists.image_link,
    'start_time': show.start_time
  } for show in upcoming_shows]
  new_data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=new_data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm(meta={'csrf': False})
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      venue = Venue()
      form.populate_obj(venue)
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash(f'Failed to list venue {request.form["venue"]}!')
    finally:
      db.session.close()
  else:
    msg = []
    for field, err in form.errors.items():
      msg.append(field + ' ' + '|'.join(err))
    flash(f'Error validating new entry: {str(msg)}')

  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter(Venue.id==venue_id).delete()
    db.session.commit()
    flash(f'Venue {venue_id} deleted!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(f'Failed to delete venue {venue_id}')
  finally:
    db.session.close()

  return 'OK'


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  
  venue = Venue.query.first_or_404(venue_id)
  form = VenueForm(obj=venue, meta={'csrf': False})
  return render_template('forms/edit_venue.html', form=form, venue_id=venue_id, venue_name=venue.name)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  venue = Venue.query.first_or_404(venue_id)
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      form.populate_obj(venue)
      db.session.commit()
      flash(f'Venue {venue_id} updated succesfully')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash(f'Failed to updated venue {venue_id}')
    finally:
      db.session.close()
  else:
    msg = []
    for field, err in form.errors.items():
      msg.append(field + ' ' + '|'.join(err))
    flash(f'Error validating new entry: {str(msg)}')

  return redirect(url_for('show_venue', venue_id=venue_id))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  artists = Artist.query.all()
  new_data = [
    {'id': artist.id, 'name': artist.name}
    for artist in artists
  ]
  return render_template('pages/artists.html', artists=new_data)


@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  new_response = {
    'count': len(artists),
    'data': [
      {'id': artist.id, 'name': artist.name, 'num_upcoming_shows': artist.num_upcoming_shows}
      for artist in artists
    ]
  }
  return render_template('pages/search_artists.html', results=new_response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)
  new_data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website,
    'facebook_link': artist.facebook_link,
    'image_link': artist.image_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description
  }

  # past_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.startTime < datetime.now()).all()
  past_shows = db.session.query(Show).join(Artist).filter(Artist.id == artist_id).filter(Show.start_time < datetime.now()).all()
  new_data['past_shows'] = [{
    'venue_id': show.venue_id,
    'venue_name': show.venues.name,
    'venue_image_link': show.venues.image_link,
    'start_time': show.start_time
  } for show in past_shows]
  new_data['past_shows_count'] = len(past_shows)

  # upcoming_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.startTime > datetime.now()).all()
  upcoming_shows = db.session.query(Show).join(Artist).filter(Artist.id == artist_id).filter(Show.start_time > datetime.now()).all()
  new_data['upcoming_shows'] = [{
    'venue_id': show.venues.id,
    'venue_name': show.venues.name,
    'venue_image_link': show.venues.image_link,
    'start_time': show.start_time
  } for show in upcoming_shows]
  new_data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_artist.html', artist=new_data)


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  artist = Artist.query.first_or_404(artist_id)
  form = ArtistForm(artist, meta={'csrf': False})
  return render_template('forms/edit_artist.html', form=form, artist_id=artist_id, artist_name=artist.name)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  artist = Artist.query.first_or_404(artist_id)
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validat():
    try:
      form.populate_obj(artist)
      db.session.commit()
      flash(f'Artist {artist_id} updated succesfully!')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash(f'Failed to update artist {artist_id}')
    finally:
      db.session.close()
  else:
    msg = []
    for field, err in form.errors.items():
      msg.append(field + ' ' + '|'.join(err))
    flash(f'Error validating new entry: {str(msg)}')

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:
    Artist.query.filter(Artist.id==artist_id).delete()
    db.session.commit()
    flash(f'Artist {artist_id} deleted!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(f'Failed to delete artist {artist_id}')
  finally:
    db.session.close()

  return 'OK'


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm(meta={'csrf': False})
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      artist = Artist()
      form.populate_obj(artist)
      db.session.add(artist)
      db.session.commit()      
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      print(e)
      db.session.rollback()
      flash(f'Failed to list artist {request.form["name"]}!')
    finally:
      db.session.close()
  else:
    msg = []
    for field, err in form.errors.items():
      msg.append(field + ' ' + '|'.join(err))
    flash(f'Error validating new entry: {str(msg)}')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():

  all_shows = Show.query.all()
  new_data = [{
    'venue_id': show.venue_id,
    'venue_name': show.venues.name,
    'artist_id': show.artist_id,
    'artist_name': show.artists.name,
    'artist_image_link': show.artists.image_link,
    'start_time': show.start_time
  }
  for show in all_shows]    

  return render_template('pages/shows.html', shows=new_data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm(meta={'csrf': False})
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  form = ShowForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      show = Show()
      form.populate_obj(show)
      db.session.add(show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    except:
      db.session.rollback()
      flash('Failed to list Show!')
    finally:
      db.session.close()
  else:
    msg = []
    for field, err in form.errors.items():
      msg.append(field + ' ' + '|'.join(err))
    flash(f'Error validating new entry: {str(msg)}')

  return render_template('pages/home.html')


#  Error handlers
#  ----------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500
