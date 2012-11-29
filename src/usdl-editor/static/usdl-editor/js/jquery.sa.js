// Snippets jQuery-like plugin
//

// helpers

String.prototype.htmlEncode = function ()
{
    return this.replace(/&/mg,"&amp;").replace(/</mg,"&lt;").replace(/>/mg,"&gt;").replace(/\"/mg,"&quot;")
}

String.prototype.htmlDecode = function ()
{
    return this.replace(/&lt;/mg,"<").replace(/&gt;/mg,">").replace(/&quot;/mg,"\"").replace(/&amp;/mg,"&")
}

String.prototype.encodeLiteral = function () {
        return this.replace(/\"/g, '\\"')
}

String.prototype.decodeLiteral = function () {
        return this.replace(/\\"/g, '"')
}

Object.filter = function (obj, predicate) {
    var result = {}, key
    for (key in obj) {
        if (obj.hasOwnProperty(key) && predicate(obj[key])) {
            result[key] = obj[key];
        }
    }
    return result
}

Object.first = function (obj) {
   for (var propName in jsonObj) {
      if (jsonObj.hasOwnProperty(propName)) {
          return propName;    // or do something with it and break
      }
   }
}

// the $sa object

window.$sa = function (selector) {
    return new $sa.fn.init(selector)
}

$sa.fn = $sa.prototype = {
    init: function(selector) {
        this.snippets = []
        if (selector instanceof $sa.Snippet) {
            this.snippets = [selector]
        } else if (typeof selector == "string") {
            switch (selector.charAt(0)) {
                case "*": // all available snippets
                    this.snippets = $sa.store.getAllSnippets()
                    break;
                case "#": // #tagname
                    this.snippets = $sa.store.getSnippetsByTag(selector.substr(1))
                    break
                case "@": // @username
                    break
                case "[": // [field[value]]
                    var endOfFieldPos = selector.indexOf("[",1)
                    var endOfValuePos = selector.lastIndexOf("]]")
                    if (endOfFieldPos != -1 && endOfValuePos != -1 && endOfValuePos > endOfFieldPos) {
                        this.snippets = $sa.store.getSnippetsByField(selector.substring(1,endOfFieldPos),                                                          selector.substring(endOfFieldPos+1,endOfValuePos))
                    }
                    break;
                default: // snippetname
                    snippet = $sa.store.getSnippetById(selector)
                    this.snippets = snippet ? [snippet] : []
                    break
            }
        }
        return this
    },
    length: function () {
        return this.snippets.length
    },
    eq: function (index) {
        return this.snippets[index] || null
    },
    each: function (callback) {
        for(var t=0; t<this.snippets.length; t++) {
            callback.call(this.snippets[t],t)
        }
        return this
    },
    filter: function (selector) {
        var filtered = [];

        if (typeof selector == "string") {
            switch (selector.charAt(0)) {
                case "*": // all available snippets
                    filtered = this.snippets.slice()
                    break;
                case "#": // #tagname   
                    for(t = 0; t<this.snippets.length; t++) {
                        if (this.snippets[t].tags && $.inArray(selector.substr(1),this.snippets[t].tags) !== -1) {
                            filtered.push(this.snippets[t])
                        }
                    }
                    break
                case "@": // @username
                    break
                case "[": // [field[value]]
                    var endOfFieldPos = selector.indexOf("[",1)
                    var endOfValuePos = selector.lastIndexOf("]]")
                    if (endOfFieldPos != -1 && endOfValuePos != -1 && endOfValuePos > endOfFieldPos) {
                        for (t = 0; t<this.snippets.length; t++) {
                            if (this.snippets[t][selector.substring(1,endOfFieldPos)] === selector.substring(endOfFieldPos+1,endOfValuePos)) {
                                filtered.push(this.snippets[t])
                            }
                        }
                    }
                    break
                default: // snippetname
                    for(t = 0; t<this.snippets.length; t++) {
                        if (this.snippets[t].id === selector) {
                            filtered.push(this.snippets[t])
                        }
                    }
                    break
            }
        }
        return filtered
    }
};

$sa.fn.init.prototype = $sa.fn;

$sa.fn.render = function (options) {
    var defaults = {
        displayPoint: "body"
    }
    options = $.extend({},defaults,options);
    this.each(function (i) {
        $sa.display.renderSnippet(this).appendTo($(options.displayPoint))
    })
}

$sa.fn.navigate = function (options) {
    var defaults = {
        templateTitle: "core.templates.snippet.default",
        template: undefined
    };
    options = $.extend({},defaults,options)
    options.template = options.template ? options.template : $sa.store.getSnippet(options.templateTitle)
    this.each(function() {
        $sa.display.navigateSnippet(this,options)
    })
}


$sa.utils = {}
    
    $sa.utils.arrayRemove = function (array,from,to) {
        var rest = array.slice((to || from) + 1 || array.length)
        array.length = from < 0 ? array.length + from : from
        return array.push.apply(array, rest)
    };

    $sa.utils.addField = function (fields,name,value) {
        if ($.isArray(fields[name])) {
            fields[name].push(value)
        } else if (name in fields) {
            fields[name] = [fields[name],value]
        } else {
            fields[name] = value
        }
    };
    
    $sa.utils.parseFields = function (text) {
        var fields = {}
        var lines = text.split("\n")
        for (var t=0; t<lines.length; t++) {
            var c = lines[t].indexOf(":")
            if (c != -1)
                $sa.utils.addField(fields,$.trim(lines[t].substring(0,c)),$.trim(lines[t].substring(c+1)))
        }
        return fields
    };

    $sa.utils.renderObject = function (object,excludeNames) {
        var j = $([])
        for (var n in object) {
            if (!excludeNames || $.inArray(n,excludeNames) == -1) {
                var wrapper = $("<div/>").addClass("snippet_dataRow")
                $("<span/>").addClass("snippet_dataName").text(n).appendTo(wrapper)
                $("<span/>").addClass("snippet_dataValue").text(object[n].toString()).appendTo(wrapper)
                j = j.add(wrapper)
            }
        }
        return j
    }

    $sa.utils.renderArray = function (array,excludeNames) {
        var j = $([])
        for (var t=0; t<array.length; t++) {
            if (!excludeNames || $.inArray(array[t].name,excludeNames) == -1) {
                var wrapper = $("<div/>").addClass("snippet_dataRow")
                $("<span/>").addClass("snippet_dataName").text(array[t].name).appendTo(wrapper)
                $("<span/>").addClass("snippet_dataValue").text(array[t].value).appendTo(wrapper)
                j = j.add(wrapper)
            }

        }
        return j
    }

$sa.Snippet = function (fields) {
    this.title = fields.title
    this.id = fields.id
    this.text = fields.text
    this.tags = fields.tags
    this.type = fields.type
    this.fields = fields
}

$sa.Snippet.prototype.getText = function () {
        if (typeof this.text === "function") {
        this.text = this.text()
        this.fields.text = this.text
    }
    return this.text
}

$sa.Snippet.prototype.setText = function (t) {
        this.text = t
        this.fields.text = t
}

$sa.Snippet.prototype.getFields = function () {
    return this.fields
}

$sa.Snippet.prototype.toHtml = function () {
    var html;
    var text = this.getText()
    if(text !== undefined && $.trim(text) !== "") {
        switch (this.type) {
            case "text/html":
            case "text/css":
                html = $("<div/>").html(text).contents()
                break

            case "text/javascript":
            case "text/json":
                html = $("<pre/>").text(text)
                break
            default:
                html = $("<div/>").text(text).html()
                break
        }
    }
    return html
};

$sa.store = {}
    var snippets = {};
    var notificationCallbacks = [] // Array of {callback: function(), selector: selector}
    var triggeredNotifications = [] // Subarray of notifications that have already been tripped
    var untriggeredNotifications = [] // Subarray of notifications that have not yet been tripped
    var notificationTimer = null
    
    // Add a new notification handler {callback: function, selector: selector}
    $sa.store.addNotification = function (notification) {
        notificationCallbacks.push(notification)
    }

    $sa.store.registerModification = function (snippet) {
    // Set up the timeout to actually send the notifications
	if(!notificationTimer) {
		triggeredNotifications = []
		untriggeredNotifications = notificationCallbacks.slice() // Make a shallow copy of the notifications
		notificationTimer = window.setTimeout($sa.store.sendNotifications,0)
	}
	for (var t=untriggeredNotifications.length-1; t>=0; t--) {
		var n = untriggeredNotifications[t]
		if ($sa(snippet).filter(n.selector).length == 1) {
			triggeredNotifications.push(n)
			$sa.utils.arrayRemove(untriggeredNotifications,t)
		}
	}
    }
    
    $sa.store.sendNotifications = function () {
        notificationTimer = null
        $.each(triggeredNotifications, function (i, val) {
                                           val.callback()
                                       })
    }
    
    // Put a snippet to the store.
    // Returns the $sa.Snippet object if successful, or null if it failed
    $sa.store.storeSnippet = function (fields) {
        if (!"title" in fields)
            return null
        var title = fields.title
        if (title === "")
            return null
        var snippet = snippets[fields.id]
        if (!snippet) {
           snippet = new $sa.Snippet(fields)
           snippets[fields.id] = snippet
//           $sa.store.registerModification(snippet)
        }
        return snippet
    }
    
    $sa.store.getAllSnippets = function () {
        var result = []
        for (var t in snippets) {
            result.push(snippets[t])
        }
        return result
    }
    
    $sa.store.getSnippetsByTag = function (tag) {
        var result = []
        for (var t in snippets) {
            if( snippets[t].tags && $.inArray(tag,snippets[t].tags) != -1)
                result.push(snippets[t])
        }
        return result
    }
    
    $sa.store.getSnippetsByField = function (field,value) {
        var result = []
        for (var t in snippets) {
            var f = snippets[t].getFields()
            if (field in f && f[field] === value)
                result.push(snippets[t])
        }
        return result
    }

    $sa.store.getSnippetById = function (id,user,source) {
        if (id in snippets)
            return snippets[id]
        else
            return null
    }
    
    $sa.store.getSnippet = function (title,user,source) {
        if (title in snippets)
            return snippets[title]
        else
            return null
    }
    
    $sa.store.loadContent = function () {
        $(".snippet").each(function () {
                             var snippet = $sa.serialisers.html.loadSnippet(this)
                             $sa.store.storeSnippet(snippet)
                           })
    }

    $sa.store.saveSnippet = function(snippet) {
            var elem = $sa.serialisers[snippet.fields.format].saveSnippet(snippet)
            return elem
    }

    $sa.store.saveStore = function (store) {

          var html = $("<html/>")
                     .append($("<head/>")
                             .append($("<title/>").text(title))
                             .append($("<style/>", { type: "text/css" }).text(".snippet { display: none; }")))
                     .append($("<body/>"))
        }

$sa.serialisers = {}

$sa.serialisers.html = {
    nodeName: "DIV",
    className: "snippet"
}
    
$sa.serialisers.html.loadSnippet = function(elem) {
        var title = $(elem).children(".snippet_title").text()
        var id = $(elem).attr("id")
        var type = $(elem).children(".snippet_type").eq(0).attr("title")
        var format = $(elem).children(".snippet_format").eq(0).attr("title")
        var html = $(elem).children(".snippet_body").clone()
        var text = function() {return html.html()}
        var tags = []
        $(elem).find(".snippet_tags a[rel='tag']").each(function(i) {
            tags.push($(this).text())
        })
        $(elem).remove()
        return {
            title: title,
            id: id,
            text: text,
            tags: tags,
            type: type?type:"text/html",
            format: format?format:"html"
        }
}

$sa.serialisers.html.saveSnippet = function (snippet) {
       var tags = $("<div/>", { "class": "snippet_tags" })
       for (var t in snippet.tags) {
           tags.append($("<a/>", { href: "#" + snippet.tags[t], rel: "tag" }).text(snippet.tags[t]))
       }
   
       return $("<div/>", { "class": "snippet", id: snippet.title})
            .append($("<h1/>", { "class": "snippet_title ui-widget-header" }))
            .append($("<abbr/>", { "class": "snippet_created published",
                                  title: snippet.created }).text(snippet.created))
            .append($("<abbr/>", { "class": "snippet_modified updated",
                                  title: snippet.updated }).text(snippet.created))
            .append(tags) 
            .append($("<div/>", { "class": "snippet_body ui-widget-content" }).text(snippet.text))
}

$sa.display = {}

    $sa.display.renderSnippet = function (snippet) {
        var html = $(snippet.toHtml())
        return html
    };

    $sa.display.navigateSnippet = function (snippet,options) {
        var defaults = {
            templateTitle: "core.templates.snippet.default",
            template: null,
            jOrigin: null
        }
        options = $.extend({},defaults,options)
        options.template = options.template ? options.template : $sa.store.getSnippet(options.templateTitle)

        var elemSnippet = $("[data-snippet-id='" + snippet.id + "'].snippetFrame")
        if (elemSnippet.length === 0) {
            elemSnippet = $sa.display.chooseDisplayPoint(snippet,options)
        } else {
            elemSnippet = elemSnippet.eq(0)
        }

        elemSnippet.addClass("snippetFrame")
        elemSnippet.attr("data-snippet-id",snippet.id)
        elemSnippet.attr("data-template-id",options.template.id)
        elemSnippet.data("options", options)
        elemSnippet.addClass("dataTag")
        var html = $(options.template.toHtml())
        elemSnippet.html(html)
    }
    
    $sa.display.chooseDisplayPoint = function (snippet,options) {
        var elemSnippet = null

        if (elemSnippet === null && options.displayPoint) {
            elemSnippet = $("<div>")
            elemSnippet.appendTo(options.displayPoint)
        }

        if (elemSnippet === null) {
            var containers = $(".snippetContainer")
            containers.each(function(i) {
                if(elemSnippet === null) {
                    elemSnippet = $sa.display.createSnippetFrameInContainer($(this),snippet,options)
                }
            })
        }
        if (elemSnippet === null) {
            elemSnippet = $("<div>")
            elemSnippet.appendTo("body")
        }
        return elemSnippet
    }
    
    $sa.display.createSnippetFrameInContainer = function (elemContainer,snippet,options) {
        var elemSnippet = null
        elemSnippet = $sa.display.insertSnippetFrameInContainer(elemContainer,snippet,options)
        return elemSnippet
    }
    
    $sa.display.refresh = function() {
	$sa.display.refreshNodes($(document).children())
    }

    $sa.display.refreshNodes = function(elements) {
	$sa.display.processNodes("refresh", elements)
    }

    $sa.display.processNodes = function(method,elements) {
	$(elements).each(function(i) {
			   var e = $(this);
			   if (!e.hasClass("ignore")) {
			      if (e.hasClass("macro")) {
                                  var it = e.clone(true)
                                  var p = e.parent()
                                  it.insertAfter(e)
                                  e.remove()
//                                  $sa.display.processNodes(method,it.children());
			      } else {
				var c = e.children()
				if (c)
                                   $sa.display.processNodes(method,c)
			      }
			   }
		         })
    }
    
    $sa.display.insertSnippetFrameInContainer = function (elemContainer,snippet,options) {
        var elemSnippet = null
        elemSnippet = $("<div/>").appendTo(elemContainer.find(".snippetContent").eq(0))
        return elemSnippet
    }


$('.transclude').livequery(function () {
   $(this).addClass('macro')
   if (document.running) {
        var title = $(this).attr("data-snippet")
        var templateTitle = $(this).attr("data-template")
        var template = templateTitle ? $sa.store.getSnippet(templateTitle) : null
        var snippet = $sa.store.getSnippetById(title)
        var param = $(this).attr("data-parameter")
        if (param) {
           $(this).data("options", {param: param})
           $(this).addClass("dataTag")
        }
        if (template) {
            $(this).addClass("snippetFrame")
            $(this).attr("data-snippet-id",snippet.id)
            $(this).attr("data-template-id",template.id)
            html = $(template.toHtml())
            $(this).html(html)
        } else {
            html = $(snippet.toHtml())
            $(this).html(html)
        }
   }
})

// view
$('.snippetView').livequery(function () {
   $(this).addClass('macro')
   if (document.running) {
        var field = $(this).attr("data-field")
        var fmt = $(this).attr("data-format")
        var className = $(this).attr("data-class")
        var snippetFrame = $(this).closest(".snippetFrame")
        var title = snippetFrame.attr("data-snippet-id")
        var snippet = $sa.store.getSnippetById(title)
        var fields = snippet.getFields()
        if (field in fields) {
            switch(fmt) {
                case "text":
                    $(this).text(fields[field])
                    break
                case "html":
                    if(field === "text") {
                        $(this).html(snippet.toHtml())
                    } else {
                        $(this).html(fields[field])
                    }
            }
        }
        if (className)
            $(this).addClass(className)
   }
})

$sa.actions = {};

$sa.actions.snippet_close = function(target,e) {
    var elemSnippet = target.closest(".snippetFrame")
    if (elemSnippet) {
        elemSnippet.hide("drop",{direction: "down"},500,function() {elemSnippet.remove() })
    }
}

$sa.command = {};
$sa.command.commands = {
    close_snippet: {text: "Close this card", action: $sa.actions.snippet_close}
};


//simple button functionality

        $('.command').livequery(function () {
		$(this).addClass('macro')
                var commandName = $(this).attr("data-name")
                var command = $sa.command.commands[commandName]
                if (command) {
                   $(this).attr("title",command.text)
                   var self = this
                   $(this).bind("click",function (e) {
                                           command.action($(self),e)
                                         })
                }
             })

        $('.delete').livequery(function () {
             $(this).click(function(e) {
                   var snippet = $(this).parents(".snippetFrame:first")
		   var p =  $(this).prev()
                   var target = p.attr("data-parameter")
                   if (target) {
		      var triples = document.kb.about('<'+target+'>')
                      triples.each(function () {
                          var triple = '<'+target+'> <'+this.property.value+ '> <' + this.value.value + '>'
                          document.kb.remove(triple)
                      })
//                      document.kb = document.kb.except(triples) // we should all ?s ?p <target> too?
                      document.kb.setDirty = true
/*
                      document.kb.prefix('foaf', 'http://xmlns.com/foaf/0.1/')
                                .prefix('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
                                .prefix('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
                                .prefix('msm', 'http://cms-wg.sti2.org/ns/minimal-service-model#')
                                .prefix('owl', 'http://www.w3.org/2002/07/owl#')
                                .prefix('dcterms', 'http://purl.org/dc/terms/')
                                .prefix('usdl', 'http://www.linked-usdl.org/ns/usdl-core#')
                                .prefix('legal', 'http://www.linked-usdl.org/ns/usdl-legal#')
                                .prefix('price', 'http://www.linked-usdl.org/ns/usdl-pricing#')
                                .prefix('sla', 'http://www.linked-usdl.org/ns/usdl-sla#')
                                .prefix('blueprint', 'http://bizweb.sap.com/TR/blueprint#')
                                .prefix('vcard', 'http://www.w3.org/2006/vcard/ns#')
                                .prefix('xsd', 'http://www.w3.org/2001/XMLSchema#"')
                                .prefix('ctag', 'http://commontag.org/ns#')
                                .prefix('org', 'http://www.w3.org/ns/org#')
                                .prefix('skos', 'http://www.w3.org/2004/02/skos/core#')
                                .prefix('time', 'http://www.w3.org/2006/time#')
                                .prefix('gr', 'http://purl.org/goodrelations/v1#')
                                .prefix('doap', 'http://usefulinc.com/ns/doap#')
*/
                      $("#columnStory .snippetFrame").hide("puff")
                      $sa.store.registerModification(snippet)
                   }
	     })
	})

        $('.link').livequery(function () {
             var subj = params.subject //$.cookie('subject')
             var param = $(this).attr("data-parameter")
             if (subj && (subj == param)) $(this).parent().addClass('ui-selected')
             $(this).addClass('macro')
             if ($(this).text() == "") $(this).text($(this).attr("placeholder"))
             $(this).click(function(e) {
                             var target = $(this).attr("data-link-target")
                             var options = {jOrigin: this}
                             var persist = $(this).attr("data-persist")
                             var param = $(this).attr("data-parameter")
                             if (param) options.param = param
                             if (persist) {
                                params.subject = param //$.cookie(persist, param)
			        var current = $("#columnStory .snippetFrame")
                                if (current.length > 0)
                                    current.hide("puff", {}, "normal",
                                          function() {
                                              $(this).remove()
                                              show(params.activeTab, params.subject)
                                          })
                                else
                                      show(params.activeTab, params.subject)
                             } else
                                $sa(target).navigate(options)
			     return true
                         })
             })

        $('.addObject').livequery(function () {
             $(this).click(function(e) {
                             var snippetframe =  $(this).parents('.dataTag:first')
                             var snippet = snippetframe.attr("data-snippet-id")
                             var opt = snippetframe.data('options')
                             var subject = opt?encodeSubject(opt.param):undefined
                             var target = $(this).attr("data-link-target")
                             var property = $(this).attr("data-property")
                             var inverseProperty = $(this).attr("data-inverse-property")
                             var template = $(this).attr("data-template")
                             var templateText = $sa.store.getSnippetById(template).text()
                             var resource = "#"+Math.uuid(17)
                             var substituted = templateText.replace(/#subject/, resource)
                             var base = document.kb.databank.baseURI
                             substituted = substituted.replace(/#baseurl/, base)
                             substituted = substituted.replace(/#name/, "")
                             var options = {jOrigin: this, param: resource}
                             document.kb.load(substituted)
                             if (property) document.kb.add(subject+" "+property+" <"+resource+">")
                             if (inverseProperty) document.kb.add("<"+resource+"> "+inverseProperty+" "+subject)
                             document.kb.setDirty = true
		             
                             $sa(target).navigate(options)
                             $sa.store.registerModification("Service")
                          })
             })

    getElemByLabel = function (arr, label) {
        for (var i in arr)
            if (arr[i].label == label)
               return arr[i]
        return null
    }

        $('.addLink').livequery(function () {
             $(this).click(function(e) {
                             var snippetframe =  $(this).parents('.dataTag:first')
                             var opt = snippetframe.data('options')
                             var subject = opt?encodeSubject(opt.param):undefined
                             var target = $(this).attr("data-link-target")
                             var property = $(this).attr("data-property")
                             var inverseProperty = $(this).attr("data-inverse-property")
                             var template = $(this).attr("data-template")
                             var type = $(this).attr("data-resource-type")
// display selection popup first
                             var dia = $("<div/>")
                             var inner = $("<div/>").addClass("dialog").appendTo(dia)
                             var label = $("<label/>").attr("for", "auto").text("Resource:" ).appendTo(inner)
                             var auto = $("<input/>").attr("id", "auto").width("95%").appendTo(inner)
                             var results = $.map(type.split(','), function (val) {
                                                                     return document.kb.where("?subject rdf:type "+val)
                                                                  })
                             var union = false
                             $.each(results, function (i, val) {
                                                if (union)
                                                   union = union.add(val)
                                                else
                                                   union = val
                                             })
                             var result = union.where("?subject dcterms:title ?title")
                             var source = []
                             result.each(function () {
                                             source.push({label: this.title.value,
                                                          subject: this.subject.value._string })
                                           })

                             auto.autocomplete({
                                               minLength: 0,
                                               source: source
                                          })

                             dia.dialog({ buttons: { "Cancel": function () {
                                                                  $(this).dialog("close")
                                                               },
                                                     "Add": function () {
                                                              var name = auto.val()
                                                              var res = getElemByLabel(source, name)
                                                              if (res) {
                                                                 var resource = res.subject
                                                                 if (property) document.kb.add(subject+" "+property+" <"+resource+">")
                                                                 if (inverseProperty) document.kb.add("<"+resource+"> "+inverseProperty+" "+subject)
                                                                 document.kb.setDirty = true
                                                                 $sa.store.registerModification('Service')
                                                              }
                                                              $(this).dialog("close")
                                                            },
                                                     "Create ...": function () {
                                                                     var name = auto.val()
                                                                     var templateText = $sa.store.getSnippetById(template).text()
                                                                     var resource = "#"+Math.uuid(17)
                                                                     var substituted = templateText.replace(/#subject/, resource)
                                                                     var base = document.kb.databank.baseURI
                                                                     substituted = substituted.replace(/#baseurl/, base)
                                                                     substituted = substituted.replace(/#name/, name)
                                                                     var options = {jOrigin: this, param: resource}
                                                                     document.kb.load(substituted)
                                                                     if (property) document.kb.add(subject+" "+property+" <"+resource+">")
                                                                     if (inverseProperty) document.kb.add("<"+resource+"> "+inverseProperty+" "+subject)
                                                                     document.kb.setDirty = true
                                                                     $sa.store.registerModification('Service')
                                                                     $(this).dialog("close")
                                                                     $sa(target).navigate(options)
                                                                   }
                                                   },
                                          title: 'Select',
                                          modal: true
                                        })
                               })
             })

        $('.addProperty').livequery(function () {
             $(this).click(function(e) {
                             var snippetframe =  $(this).parents('.dataTag:first')
                             var opt = snippetframe.data('options')
                             var subject = opt?encodeSubject(opt.param):undefined
                             var template = $(this).attr("data-template")
// display selection popup first
                             var dia = $("<div/>")
                             var inner = $("<div/>").addClass("dialog").appendTo(dia)
                             var label = $("<label/>").attr("for", "auto").text("Name" ).appendTo(inner)
                             var auto = $("<input/>").attr("id", "auto").width("95%").appendTo(inner)
                             var kb = document.kb
                             if (document.voc) kb = kb.add(document.voc)
                             var props = kb.where("?p rdfs:subPropertyOf gr:quantitativeProductOrServiceProperty")
                             props = props.where("?p rdfs:label ?label")
                             var source = []
                             props.each(function () {
                                             source.push({label: this.label.value,
                                                          property: this.p.value._string })
                                           })

                             auto.autocomplete({
                                               minLength: 0,
                                               source: source
                                          })

                             dia.dialog({ buttons: { "Cancel": function () {
                                                                  $(this).dialog("close")
                                                               },
                                                     "Add": function () {
                                                              var name = auto.val()
                                                              var property = false
                                                              $.each(source, function (i, v) {
                                                                              if (v.label == name) {
                                                                                 property = v.property
                                                                                 return false
                                                                              }
                                                                            })

                                                              var templateText = $sa.store.getSnippetById(template).text()
                                                              var resource = "#"+Math.uuid(17)
                                                              var substituted = templateText.replace(/#subject/, resource)
                                                              var base = document.kb.databank.baseURI
                                                              substituted = substituted.replace(/#baseurl/, base)
                                                              var options = {jOrigin: this, param: resource}
                                                              document.kb.load(substituted)
                                                              if (property)
								 document.kb.add(subject+" <"+property+"> <"+resource+">")
							      else {
								      // add property type to database
                                                                 var property = "#"+Math.uuid(17)
								 document.kb.add("<"+property+"> rdf:type owl:Property")
								 document.kb.add("<"+property+"> rdfs:subPropertyOf gr:quantitativeProductOrServiceProperty")
								 document.kb.add("<"+property+"> rdfs:label \""+ name +"\"")
								 document.kb.add("<"+property+"> rdfs:domain gr:ProductOrService")
								 document.kb.add("<"+property+"> rdfs:range gr:QuantitativeValue")
								 document.kb.add(subject+" <"+property+"> <"+resource+">")
							      }
                                                              document.kb.setDirty = true
                                                              $sa.store.registerModification('Properties')
                                                              $(this).dialog("close")
                                                            }
                                                   },
                                          title: 'Select',
                                          modal: true
                                        })
                               })
             })

        $('.repositoryCollections').livequery(function () {
	   var self = this
           var snippetframe =  $(this).parents('.dataTag:first')
           var opt = snippetframe.data('options')
           var collection = opt.param||''

	   $.ajax({
		   url: params.repositoryURL+collection+'/',
	           dataType: 'json',
	           success: function (data) {
                                  $(self).find('[data-view]')
		                         .each(function () {
                                            var self = this
					    data.forEach(function (d) {
					        var e = $(self).clone()
					        e.find('td')
					         .html(d)
					         .attr('data-parameter', d)
					         .appendTo($(self).parent())
					    })
	                                    $(self).hide()
				          })
		   },
	           error: function(xhr, textStatus, error) {
				  alert(textStatus)
			  }
	   })
	})

function basename(loc) {
    var last = loc.lastIndexOf('/')
    return loc.substring(last+1)
}

accessToken = "ya29.AHES6ZTWqvseL66LjgyCANG-Y8uecbukhG-bbDIlX8VjVn8F9sVQg-s"

        $('.repositoryResources').livequery(function () {
	   var self = this
           var snippetframe =  $(this).parents('.dataTag:first')
           var opt = snippetframe.data('options')
           var collURL = params.repositoryURL+(opt?opt.param:'')+'/'

           snippetframe.bind("dragenter",
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
                                 var files = e.originalEvent.dataTransfer.files
                                 console.log("FILES: "+files[0].name)
                                 var reader = new FileReader();
                                 reader.onload = function (event) {
                                     var content = event.target.result
                                     $.jGrowl("Uploading "+files[0].name+" ...")
                                     $.ajax({
                                         type: 'PUT',
                                         beforeSend: function (xhr) {
                                                       xhr.setRequestHeader("Authorization","Bearer "+accessToken)
                                                     },
                                         url: collURL+files[0].name,
                                         contentType: mime.lookup(files[0].name), 
                                         data: content,
                                         success: function (data) {
                                                   $.jGrowl(files[0].name+' uploaded.')
                                                  },
                                         error: function(xhr, textStatus, err) {
                                                   $.jGrowl('Error uploading '+
                                                            files[0].name)
                                                }
                                     })
                                 }
                                 reader.readAsText(files[0]);
                                 return false
                               })

	   $.ajax({
                   type: 'GET',
		   url: collURL,
	           dataType: 'json',
	           success: function (data) {
                           $(self).find('[data-view]')
		                  .each(function () {
                                         var self = this
					 data.forEach(function (d) {
						var e = $(self).clone()
						e.find('td')
						 .html(basename(d._id))
						e.appendTo($(self).parent())
					 })
	                                 $(self).hide()
				  })
		   },
	           error: function(xhr, textStatus, error) {
				  $.jGrowl(textStatus)
			  }
	   })
	})


// magic rdf templating engine

        $('.lens').livequery(function () {
                    $(this).addClass('macro')
                    if (document.running) {
                               var self = this
                               var snippetframe =  $(this).parents('.dataTag:first')
                               var opt = snippetframe.data('options')
                               var res = opt?opt.param:undefined
                               var show = { "literal":  function (v) {
                                                          return v 
                                                        },
                                            "uri-anchor":  function (v) {
                                                              return v._string.split('#')[1]
                                                           },
                                            "uri":  function (v) {
                                                       return v._string
                                                    }
                                          }
                                 var query = (function () {
                                              var query = $(self).attr('data-query')
                                              if (res) 
                                                 if (res.match(/^_:.*/)) // blank node
                                                    query = query.replace(/\?o /ig, res+' ')
                                                 else
                                                    query = query.replace(/\?o /ig, '<'+res+'> ')
                                              return query
                                             })()
                                 var update = function () {
                                                 // generate kb query by disjunction and conjunction of triples
                                                 var rdfA = document.kb
                                                 if (document.voc) rdfA = rdfA.add(document.voc)
                                                 $.each(query.split('. '), 
                                                        function (index, value) {
                                                           if (value.match(/\(.*\)/))
                                                              rdfA = rdfA.optional(value.replace(/[\(\)]/g,''))
                                                           else
                                                              rdfA = rdfA.where(value)
                                                        })
                                                 var kbQuery = rdfA
                                                 // fiddle result into the template
                                                 $(self).find('[data-view]').each(function () {
                                                                       var self = this
                                                                       $(self).hide()

                                                                       var fill = function() {
                                                                          var that = this
                                                                          var it = $(self).clone()
                                                                                          .appendTo($(self).parent())
                                                                          var s = $(self).attr('data-subject')
                                                                          var subject = res
                                                                          if (s)
                                                                             if (this[s])
                                                                                subject = this[s].value

                                                                       var contentFill = function () {
                                                                          var e = $(this)
                                                                          var ev = e.attr('data-content')
                                                                              
                                                                             e.attr('data-subject', subject)
                                                                             var f = e.attr('data-format')
                                                                             var s = e.attr('data-show')
                                                                             var b = ''
                                                                             var tev = (ev=='subject')?{value: res}:that[ev]
                                                                             if (tev) {
                                                                                b = tev.value
                                                                                if (tev.lang)
                                                                                   e.attr('data-lang', tev.lang)
                                                                                if (tev.datatype)
                                                                                   e.attr('data-type', tev.datatype._string)
                                                                             } else {
                                                                                   // use default language and type settings
                                                                                b = ""
                                                                             }
                                                                             var val = show[s](b)
                                                                             if (f == "html")
                                                                                e.html(val)
                                                                             else
                                                                                e.text(val)
                                                                             e.data("content.orig", val)
                                                                       }
                                                                       var attributeFill = function () {
                                                                          var e = $(this)
                                                                          var ev = e.attr('data-attribute')
                                                                              
                                                                             e.attr('data-subject', subject)
                                                                             var n = e.attr('data-attribute-name')
                                                                             var s = e.attr('data-show')
                                                                             var b = ''
                                                                             var tev = (ev=='subject')?{value: res}:that[ev]
                                                                             if (tev) {
                                                                                b = tev.value
                                                                                if (tev.lang)
                                                                                   e.attr('data-lang', tev.lang)
                                                                                if (tev.datatype)
                                                                                   e.attr('data-type', tev.datatype._string)
                                                                             } else {
                                                                                // set default lang and datatype
                                                                                b = ""
                                                                             }
                                                                             var val = show[s](b)
                                                                             e.attr(n, val)
                                                                             e.data("content.orig", val)
                                                                       }

                                                                          if (it.attr('data-content'))
                                                                             $(it).each(contentFill)
                                                                          else {
                                                                              var e = it.find('[data-content]')
                                                                              e.each(contentFill)
                                                                          }
                                                                          if (it.attr('data-attribute'))
                                                                             $(it).each(attributeFill)
                                                                          else {
                                                                             var e = it.find('[data-attribute]')
                                                                             e.each(attributeFill)
                                                                          }
                                                                         it.show()
                                                                       }
                                                                       if (kbQuery.length > 0) 
                                                                          kbQuery.each(fill)
                                                                       else {
                                                                          var def = $(self).attr('data-defaults')
                                                                          if (def)
                                                                             fill(JSON.parse(def)) // just fill with defaults
                                                                       }
                                                                       $(self).hide()
                                                                    })
                                             }
                               if (document.kb) update()
               }

        })

var encodeSubject = function (s) {
     if (s.match(/^_:.*/)) // blank node
        return s
     else if (s.match(/^<.*>$/))
	return s
     else
        return '<'+s+'>'
}

// edit a simple text field

	$.editableFactory.xsdString = {
		toEditable: function($this,options){
			$('<input/>').appendTo($this)
				     .val($this.data('editable.current').decodeLiteral())
		},
		getValue: function($this,options){
			return $this.children().val()
		}
	}

	$.editableFactory.uriString = {
		toEditable: function($this,options){
			$('<input/>').appendTo($this)
						 .val($this.data('editable.current'))
		},
		getValue: function($this,options){
			return $this.children().val()
		}
	}

        $('.textEdit').livequery(function () {
		                    $(this).editable({
                                             type: "xsdString",
                                             onSubmit: function (content) {
                                                           var snippet =  $(this).parents('.dataTag:first')
                                                                                .attr("data-snippet-id")
                                                           var subject = encodeSubject($(this).attr("data-subject"))
                                                           var type = $(this).attr("data-type")
                                                           type = (type)?'^^<'+type+'>':''
                                                           var lang = $(this).attr("data-lang")
                                                           var property = $(this).attr("data-property")

                                                           lang = (lang)?'@'+lang:''
                                                           var oldTriple = subject + ' '
                                                                         + property + ' "'
					                                 + content.previous.encodeLiteral()
                                                                         + '"' + type + lang + ' .'
                                                           var newTriple = subject + ' '
                                                                         + property + ' "'
					                                 + content.current.encodeLiteral()
                                                                         + '"' + type + lang + ' .'
					                   document.kb.where(oldTriple)
					                           .each(function (bindings, i, triples) {
									   document.kb.remove(triples[0])
								   })
                                                           // document.kb = document.kb.remove(oldTriple)
                                                           document.kb = document.kb.add(newTriple)
                                                           document.kb.isDirty = true
                                                           $sa.store.registerModification(snippet)
                                                       }                                              
                                                     })
                                 })

        $('.uriEdit').livequery(function () {
		                    $(this).editable({
                                             type: "uriString",
                                             onSubmit: function (content) {
                                                           var snippet = $(this).parents(".snippetFrame:first")
                                                                                .attr("data-snippet-id")
                                                           var subject = encodeSubject($(this).attr("data-subject"))
                                                           var property = $(this).attr("data-property")
                                                           var oldTriple = subject + ' '
                                                                         + property + ' <' + content.previous
                                                                         + '>'
                                                           var newTriple = subject + ' '
                                                                         + property + ' <' + content.current
                                                                         + '>'
					                   if (content.previous != content.current) {
                                                              if (content.previous != '') {
							         document.kb = document.kb.remove(oldTriple)
                                                                 document.kb.isDirty = true
							      }
                                                              if (content.current != '') {
							         document.kb = document.kb.add(newTriple)
                                                                 document.kb.isDirty = true
					                      }
							   }
                                                           if (document.kb.isDirty)  $sa.store.registerModification(snippet)
                                                       }                                              
                                                     })
                                 })

        $('.baseEdit').livequery(function () {
		                    $(this).editable({
                                             type: "uriString",
                                             onSubmit: function (content) {
					                   if (content.previous != content.current) {
                                                              var reg = new RegExp(content.previous.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&"),"g")
                                                              var ttl = document.kb.databank.dump({format: "text/turtle"})
                                                              var ttl2 = ttl.replace(reg, content.current)
                                                              document.kb = $.rdf().load(ttl2)
                                                              document.kb
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
                                                                 .base(content.current)
                                                           }
                                                     }
                                 })
                       })


        $('.iconEdit').livequery(function () {
                                   $(this).click(function () { $(this).next().toggleClass("hidden") })
                                })

        $('.selectEdit').livequery(function () {
//		                    $(this).addClass('macro')
		                    $(this).editable({
                                              type: 'select',
                                              editClass: 'valueColEdit',
                                              options: $(this).attr("options").split(","),
                                              onSubmit: function (content) {
                                                           var snippet = $(this).parents(".snippetFrame:first")
                                                                                .attr("data-snippet-id")
                                                           var subject = encodeSubject($(this).attr("data-subject"))
                                                           var property = $(this).attr("data-property")
                                                           var prefix = $(this).attr("data-prefix")
                                                           var type = $(this).attr("data-type")
                                                           type = (type)?'^^<'+type+'>':''
                                                           var lang = $(this).attr("data-lang")
                                                           lang = (lang)?'@'+lang:''
                                                           var oldTriple, newTriple
							   if (prefix) {
                                                              oldTriple = subject + ' '
                                                                         + property + ' '
									 + encodeSubject(prefix+content.previous)
                                                              newTriple = subject + ' '
                                                                         + property + ' ' 
									 + encodeSubject(prefix+content.current)
							   } else {
                                                              oldTriple = subject + ' '
                                                                         + property + ' "' + content.previous
                                                                         + '"' + type + lang
                                                              newTriple = subject + ' '
                                                                         + property + ' "' + content.current
                                                                         + '"' + type + lang
							   }
				    		           document.kb.where(oldTriple)
					                              .each(function (bindings, i, triples) {
									      document.kb.remove(triples[0])
								      })
                                                           document.kb = document.kb.add(newTriple)
                                                           document.kb.isDirty = true
                                                           $sa.store.registerModification(snippet)
                                                       }                                              
                                                     })
                                 })


$.editableFactory.html = {
		toEditable: function ($this,options){

                       $("body").one("click", function () { $("div[contentEditable]").blur() })

                        var ec = $('<div/>').css("position", "relative").appendTo($this)

			var ta = $('<div/>').appendTo(ec)
                                   .addClass('editable')
			           .html($this.data('editable.current').decodeLiteral())
			           .attr('contentEditable', 'true')
                                   .css('border', '1px inset #1D7DB3')
                                   .focus()


                        var tb = $('<div class="easyEditorToolBar">')
                                   .append($('<button title="Undo" class="button">⤾</button>')
                                            .click(function(e) {
                                               document.execCommand('undo', null, null)
                                               ta.focus()
                                             }))
                                   .append($('<button title="Bold" class="button" style="font-weight: bold;">B</button>')
                                            .click(function(e) {
                                               document.execCommand('bold', null, null)
                                               ta.focus()
                                             }))
                                   .append($('<button title="Italic" class="button" style="font-style:italic;">I</button>')
                                            .click(function(e) {
                                               document.execCommand('italic', null, null)
                                             }))
                                   .append($('<button title="Italic" class="button"><span style="text-decoration:underline">U</span></button>')
                                            .click(function(e) {
                                               document.execCommand('underline', null, null)
                                             }))
                                   .append($('<button title="Increase font size" class="button">A+</button>')
                                            .click(function(e) {
                                               document.execCommand('increaseFontSize', null, null)
                                             }))
                                   .append($('<button title="Decrease font size" class="button">A-</button>')
                                            .click(function(e) {
                                               document.execCommand('decreaseFontSize', null, null)
                                             }))
                                   .append($('<button title="Remove format" class="button" data-alt="◯╳">∅</button>')
                                            .click(function(e) {
                                               document.execCommand('removeFormat', null, null)
                                             }))
/*
                                   .append($('<button title="Format as paragraph" class="button">P</button>')
                                            .click(function(e) {
                                               document.execCommand('insertParagraph', null, null)
                                             }))
*/
                                   .append($('<button title="Unordered list" class="button">●</button>')
                                            .click(function(e) {
                                               document.execCommand('insertUnorderedList', false, null)
                                             }))
                                   .append($('<button title="Ordered list" class="button">1.</button></div>')
                                            .click(function(e) {
                                               document.execCommand('InsertOrderedList', false, null)
                                             }))
                       .buttonset()
                       .css({ position: "absolute", top: "-4em", left: "-5em" })
                       .appendTo(ec)

		},
		getValue: function($this,options) {
			var ta = $this.find('.editable')
                        return ta.html()
		}
	};

        $('.editHtml').livequery(function () {
		                    $(this).editable({
                                             type: "html",
                                             editBy: 'click',
                                             submitBy: 'blur',
                                             onSubmit: function (content){
                                                           var snippet = $(this).parents(".snippetFrame:first")
                                                                                .attr("data-snippet-id")
                                                           var subject = encodeSubject($(this).attr("data-subject"))
                                                           var property = $(this).attr("data-property")
                                                           var type = $(this).attr("data-type")
                                                           type = (type)?'^^<'+type+'>':''
                                                           var lang = $(this).attr("data-lang")
                                                           lang = (lang)?'@'+lang:''
                                                           var oldTriple = subject + ' '
                                                                         + property + ' "'
                                                                         + $(this).data("content.orig").encodeLiteral()
                                                                         + '"' + type + lang
                                                           var newTriple = subject + ' '
                                                                         + property + ' "'
					                                 + content.current.encodeLiteral()
                                                                         + '"' + type + lang
                                                           document.kb = document.kb.remove(oldTriple).add(newTriple)
                                                           document.kb.isDirty = true
                                                           $(this).data("content.orig", content.current)
                                                           $sa.store.registerModification(snippet)
                                                       }    
                                                     })
                                            .click(function (e) { e.preventDefault(); return false })
                                 })

        $('.dateTimeEdit').livequery(function () {
                            var input = this
                            $(this).datetimepicker({
                                              dateFormat: 'yy-mm-dd',separator:'T',
                                              timeFormat: 'hh:mm',
//                                              withTime: false,
                                              onSelect: function (picked, inst) {
                                                           var snippet = $(this).parents(".snippetFrame:first")
                                                                                .attr("data-snippet-id")
                                                           var value = picked
                                                           var subject = encodeSubject($(input).attr("data-subject"))
                                                           var property = $(input).attr("data-property")
                                                           var type = $(input).attr("data-type")
                                                           type = (type)?'^^<'+type+'>':''
                                                           var lang = $(input).attr("data-lang")
                                                           lang = (lang)?'@'+lang:''
                                                           var oldTriple = subject + ' '
                                                                         + property + ' "'
                                                                         + $(input).data("content.orig")
                                                                         + '"' + type + lang
                                                           var newTriple = subject + ' '
                                                                         + property + ' "' + value
                                                                         + '"' + type + lang
				    		           document.kb.where(oldTriple)
					                              .each(function (bindings, i, triples) {
									      document.kb.remove(triples[0])
								      })
                                                           document.kb = document.kb.add(newTriple)
                                                           document.kb.isDirty = true
                                                           $(input).data("content.orig", value)
                                                           $sa.store.registerModification(snippet)
                                                              }
                                             })   
                                 })


function getParameters()
{
  if (window.location.hash)
     return decodeURIComponent(window.location.hash.substr(1))
  else
     return null
}

$('.infovis').livequery(function () {

})
