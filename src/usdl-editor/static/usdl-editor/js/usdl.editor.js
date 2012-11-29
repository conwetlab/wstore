$(function() {

    jQuery.support.cors = true;
    params = { }
    params.activeTab = "Service"
    params.subject = null
    params.repositoryURL = 'https://fiware01.sapvcm.com:5000'
//    params.repositoryURL = 'http://cybyl.selfip.com:5000'

    $sa.store.loadContent()

    show = function (val, subj) {
        if (subj) {
           var query = document.kb.where(encodeSubject(subj)+' ?pred ?obj')
           if (query.length > 0) {
              $sa(val).navigate({param: subj})
           } else
	      $sa(val).navigate()
        } /* else
	    $sa(val).navigate() */
}

    findBase = function (kb) {
                      var base = kb.databank.baseURI
                      var services = kb.where("?service rdf:type usdl:Service")
                      services = kb.optional("?service rdf:type usdl:ServiceModel")
                      services.each(function () {
                                      var selection = this["service"]
                                      var url = selection.value._string
                                      base = url.split('#')[0]
                                    })
                      return base
}

function dirname(loc) {
    var last = loc.lastIndexOf('/')
    return loc.substring(0, last)
}

// command for generating rdf
    $sa.command.commands.rdf = { text: "Show RDF",
                                 action: function(target,e) {
                                                var format= target.attr("data-format")
                                                if (format == "rdf") {
                                                   var dmp = document.kb.databank.dump({format:'application/rdf+xml',
                                                                                        serialize: true})
                                                   var uueFile = Base64.encode(dmp)
                                                   var uri = 'data:application/rdf+xml;base64,' + encodeURIComponent(uueFile)
                                                   window.open(uri)
                                                } else if (format == "ttl") {
                                                        var dmp = document.kb.databank.dump({format:'text/turtle',
								                             indent: true,
                                                                                             serialize: true})
                                                        var uueFile = Base64.encode(dmp)
                                                        var uri = 'data:text/turtle;base64,' + encodeURIComponent(uueFile)
                                                        window.open(uri)
                                                } else if (format == "json") {
                                                        var dmp = $.toJSON(document.kb.databank.dump())
                                                        var uueFile = Base64.encode(dmp)
                                                        var uri = 'data:application/rdf+json;base64,' + encodeURIComponent(uueFile)
                                                        window.open(uri)
                                                } else
                                                   return
                                         }
                               }

    $sa.command.commands.publish = { text: "Publish to store",
                                     action: function(target,e) {
                                               var store = target.attr("data-parameter")

         var rdfdmp = document.kb.databank.dump({format:'application/rdf+xml', serialize: true})
                                                var running = true
                                                jQuery.ajax({
                                                         type : "POST",
                                                         url : portalConfig.storeWebApiUrl+"importusdl",
                                                         data : {
                                                            meshFileId : params.usdlFileId[0],
                                                            storeType : store, // all, mobile, enterprise, service
                                                         },
                                                         error : function(xhr, status, e) {
                                                                    $('.activityIndicator',$(target).parents('.snippetFrame:first')).addClass('noactivity')
                                                                    running = false
                                                                    $.jGrowl("ERROR: "+ xhr.statusText,
                                                                             {closer: false})
                                                                 },
                                                         success : function(data, status, xhr) {
                                                                    $('.activityIndicator',$(target).parents('.snippetFrame:first')).addClass('noactivity')
                                                                    running = false
                                                                    $.jGrowl("Soluton was published.",
                                                                             {closer: false})
                                                                   }
                                                       })
                                                if (running) $('.activityIndicator',$(target).parents('.snippetFrame:first'))
                                                 .removeClass('noactivity')
                                             }
                                   }
// create a fresh database
    var kb = $.rdf()
              .prefix('foaf', 'http://xmlns.com/foaf/0.1/')
              .prefix('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
              .prefix('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
              .prefix('msm', 'http://cms-wg.sti2.org/ns/minimal-service-model#')
              .prefix('owl', 'http://www.w3.org/2002/07/owl#')
              .prefix('dcterms', 'http://purl.org/dc/terms/')
              .prefix('usdl', 'http://www.linked-usdl.org/ns/usdl-core#')
              .prefix('legal', 'http://www.linked-usdl.org/ns/usdl-legal#')
              .prefix('price', 'http://www.linked-usdl.org/ns/usdl-pricing#')
              .prefix('sla', 'http://www.linked-usdl.org/ns/usdl-sla#')
              .prefix('sec', 'http://www.linked-usdl.org/ns/usdl-sec#')
              .prefix('blueprint', 'http://bizweb.sap.com/TR/blueprint#')
              .prefix('vcard', 'http://www.w3.org/2006/vcard/ns#')
              .prefix('xsd', 'http://www.w3.org/2001/XMLSchema#')
              .prefix('ctag', 'http://commontag.org/ns#')
              .prefix('org', 'http://www.w3.org/ns/org#')
              .prefix('skos', 'http://www.w3.org/2004/02/skos/core#')
              .prefix('time', 'http://www.w3.org/2006/time#')
              .prefix('gr', 'http://purl.org/goodrelations/v1#')
              .prefix('doap', 'http://usefulinc.com/ns/doap#')
//	      .add('<> rdf:type usdl:ServiceDescription')

	      .load('@prefix dcterms:  <http://purl.org/dc/terms/> .\
      @prefix foaf:    <http://xmlns.com/foaf/0.1/> .\
      @prefix usdl:  <http://www.linked-usdl.org/ns/usdl-core#> .\
      @prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .\
      <> a usdl:ServiceDescription;\
      dcterms:title ""@en ;\
      dcterms:description ""@en;\
      dcterms:modified ""^^xsd:datetime;\
      dcterms:created ""^^xsd:datetime;\
      dcterms:creator [ a foaf:Person;\
                        foaf:name ""\
			] .')

	      document.kb = kb
    $sa("core.templates.page.default").render()
    $('#application').addClass('chrome')
    $('#tabs').livequery(function () {
                           var fc = $(this).find('li a[data-target='+params.activeTab+']').parent()
	                   var left = fc.position().left
	                   var width = fc.width()
                           $("#tabs .sapUiUx3NavBarArrow").animate({left: fc.position().left
                                                                          + fc.width()/2}, 500)
                           $('#tabs li a').removeClass('sapUiUx3NavBarItemSel')
                           fc.children().addClass('sapUiUx3NavBarItemSel')
                           $('li', this).click(function (event) {
                                                 var snippet = $(event.target).attr("data-target")
                                                 var subj = $(event.target).attr("data-subject")
                                                 if (snippet != params.activeTab)
                                                    params.activeTab = snippet
                                                 $('#tabs li a').removeClass('sapUiUx3NavBarItemSel')
                                                 $(event.target).addClass('sapUiUx3NavBarItemSel')
                                                 $("#tabs .sapUiUx3NavBarArrow")
				                       .animate({left: $(this).position().left
                                                                       + $(this).width()/2},
                                                                500)
                                                 var elems = $("#columnStory .snippetFrame")
                                                 if (elems.length > 0)
                                                    elems.hide("drop",{direction: "down"}, 500,
                                                               function () {
                                                                  $(this).remove()
                                                                  show(snippet,(subj)?subj:params.subject)
                                                               })
                                                 else
                                                    show(snippet, (subj)?subj:params.subj)
                                               })
                         })
    $(".snippetContent").slidedeck({slideClass: "snippetFrame", deckOffset: 60})
    $('.snippet_content').livequery(function () { $(this).clickNScroll()})

    $('#menuServiceModels').livequery(function () {
                                       $('li', this).click(function(event) {
                                                             $('#menuServiceModels li').removeClass('ui-selected')
                                                             $('#menuServices li').removeClass('ui-selected')
                                                             $(this).addClass('ui-selected')
                                                           })
                                      })
    $('#menuServices').livequery(function () {
                                       $('li', this).click(function(event) {
                                                             $('#menuServices li').removeClass('ui-selected')
                                                             $('#menuServiceModels li').removeClass('ui-selected')
                                                             $(this).addClass('ui-selected')
                                                          })
                                 })

    $sa.store.addNotification({callback:  function () {
	                                      $sa.display.refresh()
	                                  }
	                     , selector: "*"})

    $sa.store.addNotification({ selector: "About",
                                callback: function () {
                                               // get the imported vocabulary uri and load it
                                               var vocs = document.kb.where("?desc owl:imports ?voc")
                                               vocs.each(function () {
                                                           var voc = this.voc.value
                                                           var kb = $.rdf()
		                                           var options = {
                                                               type: 'GET',
                                                               url: voc._string,
                                                               success: function (data) {
                                                                         kb.load(data)
                                                                         document.voc = kb
                                                                         $.jGrowl('vocabulary loaded.')
                                                                        },
                                                               error: function(xhr, textStatus, err) {
                                                                         $.jGrowl('Error loading vocabulary')
                                                                      }
		                                              }
                                                           $.ajax(options)
                                                       })
/*
                                               var descs = document.kb.where("?desc rdf:type usdl:ServiceDescription")
                                               descs.each(function () {
                                                           var desc = this.desc.value._string
                                                           if (document.kb.base() != desc)
                                                              document.kb.base(desc)
                                               })
*/
                                          }
                              })
    $(".snippet").css("visibility", "visible")
    $("#workarea").bind("dragenter",
                               function (e) {
                                 return false
                               })
                  .bind("dragover",
                               function (e) {
                                 return false
                               })
                  .bind("drop",
                               function (e) {
                                 e.preventDefault();
				 var dt = e.originalEvent.dataTransfer
				 var moz_url= dt.getData('text/x-moz-url')
                                 var files = dt.files
			         if (files.length == 1) {
                                   var reader = new FileReader();
                                   reader.onload = function (event) {
                                     var content = event.target.result
                                     var kb = $.rdf()
                                     kb.load(content)
                                     
                                     kb.prefix('foaf', 'http://xmlns.com/foaf/0.1/')
                                       .prefix('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
                                       .prefix('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
                                       .prefix('msm', 'http://cms-wg.sti2.org/ns/minimal-service-model#')
                                       .prefix('owl', 'http://www.w3.org/2002/07/owl#')
                                       .prefix('dcterms', 'http://purl.org/dc/terms/')
                                       .prefix('usdl', 'http://www.linked-usdl.org/ns/usdl-core#')
                                       .prefix('legal', 'http://www.linked-usdl.org/ns/usdl-legal#')
                                       .prefix('price', 'http://www.linked-usdl.org/ns/usdl-pricing#')
                                       .prefix('sla', 'http://www.linked-usdl.org/ns/usdl-sla#')
                                       .prefix('sec', 'http://www.linked-usdl.org/ns/usdl-sec#')
                                       .prefix('blueprint', 'http://bizweb.sap.com/TR/blueprint#')
                                       .prefix('vcard', 'http://www.w3.org/2006/vcard/ns#')
                                       .prefix('xsd', 'http://www.w3.org/2001/XMLSchema#')
                                       .prefix('ctag', 'http://commontag.org/ns#')
                                       .prefix('org', 'http://www.w3.org/ns/org#')
                                       .prefix('skos', 'http://www.w3.org/2004/02/skos/core#')
                                       .prefix('time', 'http://www.w3.org/2006/time#')
                                       .prefix('gr', 'http://purl.org/goodrelations/v1#')
                                       .prefix('doap', 'http://usefulinc.com/ns/doap#')
                                       .base(findBase(kb))

                                     document.kb = kb
                                     $sa.store.registerModification('About')
				     params.subject = null
                                     var elems = $("#columnStory .snippetFrame")
                                     if (elems.length > 0)
                                        elems.hide("drop",{direction: "down"}, 500,
                                                   function () {
                                                      $(this).remove()
                                                   })
                                     $.jGrowl("File "+files[0].name+" loaded.",  {closer: false})
                                   }
                                   reader.readAsText(files[0]);
                                   return false
				 } else {
                                     var kb = $.rdf()
                                     kb.prefix('foaf', 'http://xmlns.com/foaf/0.1/')
                                       .prefix('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
                                       .prefix('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
                                       .prefix('msm', 'http://cms-wg.sti2.org/ns/minimal-service-model#')
                                       .prefix('owl', 'http://www.w3.org/2002/07/owl#')
                                       .prefix('dcterms', 'http://purl.org/dc/terms/')
                                       .prefix('usdl', 'http://www.linked-usdl.org/ns/usdl-core#')
                                       .prefix('legal', 'http://www.linked-usdl.org/ns/usdl-legal#')
                                       .prefix('price', 'http://www.linked-usdl.org/ns/usdl-pricing#')
                                       .prefix('sla', 'http://www.linked-usdl.org/ns/usdl-sla#')
                                       .prefix('sec', 'http://www.linked-usdl.org/ns/usdl-sec#')
                                       .prefix('blueprint', 'http://bizweb.sap.com/TR/blueprint#')
                                       .prefix('vcard', 'http://www.w3.org/2006/vcard/ns#')
                                       .prefix('xsd', 'http://www.w3.org/2001/XMLSchema#')
                                       .prefix('ctag', 'http://commontag.org/ns#')
                                       .prefix('org', 'http://www.w3.org/ns/org#')
                                       .prefix('skos', 'http://www.w3.org/2004/02/skos/core#')
                                       .prefix('time', 'http://www.w3.org/2006/time#')
                                       .prefix('gr', 'http://purl.org/goodrelations/v1#')
                                       .prefix('doap', 'http://usefulinc.com/ns/doap#')
                                     kb.load(moz_url)
                                     $.jGrowl("Resource "+moz_url+" loaded.",  {closer: false})
			         }
                               })
    show(params.activeTab, params.subject)
    document.running = true
})
