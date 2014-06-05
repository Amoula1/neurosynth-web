from flask import send_from_directory, Blueprint, abort, jsonify, redirect, url_for
from nsweb.models import Image, Feature, Location
from nsweb.initializers.settings import IMAGE_DIR
from nsweb.core import add_blueprint

bp = Blueprint('images',__name__,url_prefix='/images')

@bp.route('/<int:val>/')
def download(val):
    if '..' in val or val.startswith('/'):
        abort(404)
    filename = Image.query.get_or_404(val)
    if filename.download:
        filename=filename.image_file
    else:
        abort(404)
    return send_from_directory(IMAGE_DIR, filename)

@bp.route('/anatomical/data')
def brain():
    json = jsonify()
    json.data=open(IMAGE_DIR+'data.json').read()
    return json

@bp.route('/<int:val>')
def image(val):
    image = Image.query.get_or_404(val)
    return jsonify()
 
@bp.route('/feature/<int:val>/')
def featureimage_download(val):
    images=Feature.query.get_or_404(val)
    images=images.images
    return
 
@bp.route('/feature/<string:name>/')
def find_feature(name):
    """ If the passed ID isn't numeric, assume it's a feature name,
    and retrieve the corresponding numeric ID. 
    """
    val = Feature.query.filter_by(feature=name).first().id
    return redirect(url_for('images.featureimage_download',val=val))
 
@bp.route('/location/<int:val>/')
def locationimage_download(val):
    images=Location.query.query.get_or_404(val)
    images=images.images
    return
 
@bp.route('/location/<string:val>/')
def find_location(val):
    x,y,z = [int(i) for i in val.split('_')]
    val=Location.query.filter_by(x=x,y=y,z=z)
    val=val.id
    return redirect(url_for('images.locationimage_download',val=val))

add_blueprint(bp)