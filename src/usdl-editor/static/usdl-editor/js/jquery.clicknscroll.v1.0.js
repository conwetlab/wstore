/* 
 * jQuery.clickNScroll v1.0
 *
 * Copyright (c) 2010 Joshua Faulkenberry
 * Dual licensed under the MIT and GPL licenses.
 * Joshua Faulkenberry
 *
 * $Date: 2010-10-25 18:55:27 -0700 (Mon, 25 Oct 2010) $
 * $Revision: 5 $
 */

(function($){ 
 
   jQuery.extend({
      mouse: {
         x: 0,
         y: 0
      },
      clickNScroll: {
         mousedown:false,
         emaX: 0,
         emaY: 0
      }  
   });
   
   jQuery.fn.extend({
      clickNScroll: function(options) {
         var ops = $.extend({
            allowHiliting:false,
            acceleration:.65,
            deceleration:.85,
            decelRate:64,
            reverse:false,
            rightMouse:false,
            allowThrowing:true,
            throwOnOut:true
         }, options || {});
         return this.each(function(){  
            var $this = $(this).data("options", ops);                                  
            if(!ops.allowHiliting) {
              if (jQuery.browser.msie) {
                 $this.get(0).onselectstart = function () { return false; };
              } 
              else {
                  $this.get(0).onmousedown = function(e){
		       var editable = jQuery(e.target).attr("contenteditable") == "true"
		                    || e.target.nodeName == "INPUT"
		                    || e.target.nodeName =="TEXTAREA"
                       if (!editable) e.preventDefault()}
              }   
            }
            $this.mousedown(function(e) {
               $.clickNScroll.mousedown = $this;
            }).mouseup(function(e) {                                   
               if(ops.allowThrowing) sling($(this));  
               $.clickNScroll.mousedown = false;
            }).mouseout(function(e) { 
            	var from = e.relatedTarget || e.toElement;
                if (!from || from.nodeName == "HTML") {
	               if($.clickNScroll.mousedown && ops.allowThrowing && ops.throwOnOut)  sling($(this));   
	               $.clickNScroll.mousedown = false;
            	}
            })  
         });
      }      
   });
   
   function sling($this) {        
      var ops    = $this.data("options"),    
          changeX = ($.clickNScroll.emaX)*ops.deceleration,   
          changeY = ($.clickNScroll.emaY)*ops.deceleration;                                           
      if((changeX < .01 && changeX > -.01) || (changeY < .01 && changeY > -.01)) {return;}  
      move($this, changeX, changeY);            
      setTimeout(function() {
         sling($this);
      }, 1000/ops.decelRate);            
   }
   
   function move($this, changeX, changeY) {                                                                        
         if(($.clickNScroll.emaX < 0 && changeX > 0) || ($.clickNScroll.emaX > 0 && changeX < 0)) $.clickNScroll.emaX = 0;
         if(($.clickNScroll.emaY < 0 && changeY > 0) || ($.clickNScroll.emaY > 0 && changeY < 0)) $.clickNScroll.emaY = 0;
         
         var ops    = $this.data("options"),                                                                       
             amntX = ops.acceleration * changeX + (1 - ops.acceleration) * $.clickNScroll.emaX,
             amntY = ops.acceleration * changeY + (1 - ops.acceleration) * $.clickNScroll.emaY,
             scrollRight = $this[0].scrollWidth ? $this[0].scrollWidth - $this[0].clientWidth : $this[0].body.scrollWidth - $this[0].body.clientWidth,
             scrollBottom = $this[0].scrollHeight ? $this[0].scrollHeight - $this[0].clientHeight : $this[0].body.scrollHeight - $this[0].body.clientHeight; 

         if(($this.scrollLeft() <= 0 && changeX <= 0) ||  ($this.scrollLeft() >= scrollRight && changeX >= 0)) {}  
         else $this.scrollLeft($this.scrollLeft() + (amntX));
         if(($this.scrollTop() <= 0 && changeY <= 0) ||  ($this.scrollTop() >= scrollBottom && changeY >= 0)) {}  
         else $this.scrollTop($this.scrollTop() + (amntY));                                                       
         $.clickNScroll.emaX = amntX;
         $.clickNScroll.emaY = amntY;
   }
   
   $(document).mousemove(function(e) {                                     
      if($.clickNScroll.mousedown) {      
         var $this  = $.clickNScroll.mousedown,
             ops    = $this.data("options");
         if(ops.rightMouse && e.button != 2) return;
         else if(!ops.rightMouse && e.button == 2) return;    
         var changeX = e.pageX - $.mouse.x,   
             changeY = e.pageY - $.mouse.y; 
         if(!ops.reverse) {
          changeX = 0-changeX;
          changeY = 0-changeY;
         }                                                                  
         move($this, changeX, changeY);
      }  
      $.mouse = {
         x: e.pageX,
         y: e.pageY
      };                          
   }); 
   
})(jQuery);
