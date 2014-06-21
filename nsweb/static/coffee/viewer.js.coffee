# VIEWER STUFF
window.loadImages = (imgs = null, clear = true) ->
  imgs = images if !imgs?   # Fall back on images loaded in the page
  # If clear is true, remove all images and add the anatomical underlay
  if clear
    window.viewer.clearImages()
    imgs.unshift({
      'id': 'anatomical', 
      'json': false,
      'name':'anatomical', 
      'colorPalette': 'grayscale', 
      'cache': true, 
      'url':'/images/anatomical' })
  for img in imgs
    # img.json = true
    img.url = '/images/' + img.id + '/' if img.id? and !img.url?
  viewer.loadImages(imgs)

# Turn text into HTML to make sure links are displayed
textToHTML = (el) ->
  $(el).html($(el).text())

$(document).ready ->
  # options = if 'no-zoom' in settings then { panzoomEnabled: false } else {}
  cache = settings.cache || true
  viewer = new Viewer("#layer-list", ".layer-settings", cache, options)
  viewer.addView "#view-axial", Viewer.AXIAL
  viewer.addView "#view-coronal", Viewer.CORONAL
  viewer.addView "#view-sagittal", Viewer.SAGITTAL

  if 'nav' in settings
    viewer.addSlider "nav-xaxis", ".slider#nav-xaxis", "horizontal",  0, 1, 0.5, 0.01, Viewer.XAXIS
    viewer.addSlider "nav-yaxis", ".slider#nav-yaxis", "vertical", 0, 1, 0.5, 0.01, Viewer.YAXIS
    viewer.addSlider "nav-zaxis", ".slider#nav-zaxis", "vertical", 0, 1, 0.5, 0.01, Viewer.ZAXIS

  if 'layers' in settings
    viewer.addSlider "opacity", ".slider#opacity", "horizontal", 0, 1, 1, 0.01, null, '#opacity-text'
    viewer.addSlider "pos-threshold", ".slider#pos-threshold", "horizontal", 0, 1, 0, 0.01, null, '#pos-threshold-text'
    viewer.addSlider "neg-threshold", ".slider#neg-threshold", "horizontal", -1, 0, 0, 0.01, null, '#neg-threshold-text'
    viewer.addColorSelect "#select-color"
    viewer.addSignSelect "#select-sign"
    viewer.addTextField "image-intent", "#image-intent"
    viewer.addTextField "description", "#image-description"
    viewer.addDataField "voxelValue", "#data-current-value"
    viewer.addDataField "currentCoords", "#data-current-coords"

  if 'checkboxes' in settings
    viewer.addSettingsCheckboxes('#checkbox-list', 'standard')

  window.viewer = viewer
  loadImages()

  # Kludge for link to Yeo et al
  $(viewer).on('imagesLoaded', (e) => textToHTML('#image-description'))

  # Hide description box when empty
  $(viewer).on('layerSelected', (e) =>
      textToHTML('#image-description')
      $('#description.data-row').toggle(!$('#image-description').is(':empty'))
  )

