# Place all the behaviors and hooks related to the matching controller here.
# All this logic will automatically be available in application.js.
# You can use CoffeeScript in this file: http://jashkenas.github.com/coffee-script/
$(document).ready ->
  tbl=$('#features_table').dataTable
    "sPaginationType": "full_numbers"
    "iDisplayLength": 10
    "bProcessing": true
    "bServerSide": true
    "sAjaxSource": '/api/features'
    "bDeferRender": true
    "bStateSave": true
  tbl.fnSetFilteringDelay(iDelay=400)

  url_id=document.URL.split('/')
  url_id.pop()
  $('#feature_table').dataTable
    "sPaginationType": "full_numbers"
    "iDisplayLength": 10
    "bProcessing": true
    "sAjaxSource": '/api/features/'+url_id.pop()
    "bDeferRender": true
    "bStateSave": true
  $('#feature-content-menu').click (e) ->
    e.preventDefault()
   $(this).tab('show')
   return
    # $('#feature_image_select').change((e) ->
        # label = $(this).children("option:selected").text()
        # id = $(this).val()
        # img = [{
            # name: label
            # id: id
            # download: "/images/#{id}/download"
            # }]
        # window.loadImages(
            # img
        # )
    # )
#
    # $('#name.search-features').bind('railsAutocomplete.select', (e, data) ->
        # $(this).parents('form')[0].submit()
    # )
#
    # $('#feature-content-menu a').click ((e) =>
        # e.preventDefault()
        # activeTab = $('#feature-content-menu a').index($(e.target))
        # window.cookie.set('featureTab', activeTab)
        # $(e.target).tab('show')
        # if activeTab == 0
    # )
#
    # $('#load-location').click((e) ->
        # coords = viewer.coords_xyz()
        # window.location = '/locations/' + coords.join('_')
    # )
#
    # # Load state (e.g., which tab to display)
    # activeTab = window.cookie.get('featureTab')
    # $("#feature-content-menu li:eq(#{activeTab}) a").tab('show')