/*
 * 	slidedeck 0.1 - jQuery plugin
 *	written by Torsten Leidig	
 *
 *	Copyright (c) 2010 Torsten Leidig
 *	Licensed under the BSD LICENSE
 *	Built for jQuery library http://jquery.com
 */

(function($) {
	$.fn.slidedeck = function(options) {
	
	var defaults = {			
                deckOffset: 100,
                slideClass: "slide"
	}
			
	return this.each(function() {
		var settings = $.extend(defaults, options)		
                var slideClass = settings.slideClass
		if (!$(this).find('.'+slideClass+'.active').size()) { 
//			$(this).find('.'+slideClass+':first').addClass('active')
		}

                $(this).find('.'+slideClass)
                       .css({top: 0,
                             height: settings.deckHeight,
                            })
                
		var redraw = function (d) {
                   var offset = 0
                   $(d).find('.'+slideClass).each(function(i) {
                     if (!this.removed) {
                       $(this).animate({left: offset}, 
                                       {duration: 500, easing: "swing", queue: false })
                       if ($(this).hasClass("active"))
                          offset+=$(this).outerWidth()
                       else
                          offset+=settings.deckOffset
                     }
		   })
	        }
		$.fn.slidedeck.slide = function(s) {
                        var p = s.parentNode
                        s.removed = false
			$(p).find('.'+slideClass).removeClass('active')
			$(s).addClass('active')	
			redraw(p)
                }
		var activateSlide = function(e) {
                        var s = e.target
                        var f = $(s).closest('.'+slideClass)
                        if (//!$(f).hasClass("active") &&
                             ($(s).hasClass("snippetFrame") ||
                              $(s).hasClass("snippet_content") ||
                              $(s).hasClass("canvas"))
                           )
                           $(f.parentNode).slidedeck.slide(f[0])
		}
//		$(this).find('.'+slideClass+':not(active)').live("click", activateSlide)
		$(this).find('.'+slideClass).live("click", activateSlide)

                $(this).bind('DOMNodeInserted', function (e) {
                                                 if ($(e.target).hasClass("snippetFrame")
                                                     && e.target.parentNode == this
                                                     && $(e.target).css("display") != "none" )
                                                    activateSlide(e)
                                                })

                       .bind('DOMNodeRemoved', function (e) {
                                                 if ($(e.target).hasClass("snippetFrame")
                                                     && e.target.parentNode == this
                                                     && $(e.target).css("display") != "none"
                                                     && !e.target.removed) {
                                                    e.target.removed = true
                                                    redraw(this)
                                                 }
                                               })
	})
     }
})(jQuery)
