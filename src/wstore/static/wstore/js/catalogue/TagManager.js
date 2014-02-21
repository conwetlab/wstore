(function() {

    /**
     * The Tag manager is used to update offering Tags
     * @param offering, The offering Element object that describes
     * the corresponding offering
     */
    TagManager = function TagManager (offering, caller) {
        this.offering = offering;
        this.finalTags = offering.getTags().slice(0);
        this.caller = caller;
    }

    /**
     * Tag Manager is a subclass of ModalForm
     */
    TagManager.prototype = new ModalForm('Update tags', '#update_tags_template');
    TagManager.prototype.constructor = TagManager;

    /**
     * Private method that includes tag elements in the 
     * view, composed of a tag icon, the tag, and the 
     * remove tag button
     * @param tag, tag to be included
     * @param classContext, this of the class
     */
    var addTag = function addTag(tag, classContext) {
        var tagElem = $.tmpl('includedTagTemplate', {'tag': tag });
        // Include listeners
        // Hover
        tagElem.find('.icon-remove-sign').hover((function(elem) {
            return function() {
                // Mark the corresponding tag
                var span = elem.find('span');
                span.css('text-shadow', 'rgb(255,0,0) 0.1em 0.1em 0.1em');
            };
        })(tagElem), (function(elem) {
            return function() {
                // Mark the corresponding tag
                var span = elem.find('span');
                span.removeAttr('style');
            };
        })(tagElem));

        // Click
        tagElem.find('.icon-remove-sign').click((function(elem, self) {
            return function() {
                var index = self.finalTags.indexOf(tag);
                self.finalTags.splice(index, 1);
                elem.empty()
            }
        })(tagElem, classContext));
        tagElem.appendTo('#sel-tags');
    };

    /**
     * Include needed information in the displayed window
     */
    TagManager.prototype.includeContents = function includeContents() {
        // Fill existing tags
        $.template('includedTagTemplate', $('#included_tag_template'));

        for (var i = 0; i < this.finalTags.length; i++) {
            addTag(this.finalTags[i], this);
        }
    };

    /**
     * Set Main listeners of the modal
     */
    TagManager.prototype.setListeners = function setListeners() {
        // Set Add tag listener
        $('#add-tag').click((function() {
            if ($.trim($('#tag-text').val()) && this.finalTags.indexOf($.trim($('#tag-text').val())) == -1) {
                // Add tag to the list
                this.finalTags.push($.trim($('#tag-text').val()));

                // Create tag entry
                addTag($.trim($('#tag-text').val()), this);
            }
            $('#tag-text').val('');
        }).bind(this));

        // Set Accept listener
        $('.modal-footer > .btn').click((function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            this.getRecommendedTags();
        }).bind(this))
    };

    /**
     * Client for the tagging recommendation API
     */
    TagManager.prototype.getRecommendedTags = function getRecommendedTags() {
        var tagStr = '';

        for (var i = 0; i < this.finalTags.length; i++) {
            tagStr += this.finalTags[i];

            if (i != this.finalTags.length -1) {
                tagStr += ',';
            }
        }
        // Make ajax request
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('TAG_ENTRY', {
                'organization': this.offering.getOrganization(),
                'name': this.offering.getName(),
                'version': this.offering.getVersion()
            }) + '?action=recommend&tags=' + tagStr,
            dataType: 'json',
            success: (function (response) {
                // Check if any tag is suggested
                if (response.tags.length) {
                    // Display suggested tags view
                    this.displaySuggestions(response.tags);
                } else {
                    this.updateTags();
                }
            }).bind(this),
            error: (function (xhr) {
                this.updateTags();
            }).bind(this)
        });
    };

    var paintSuggestions = function paintSuggestions(self, partialTags) {
        // partial Tags should contain at most 10 tags
        $.template('tagSugTemplate', $('#tag_suggestion_template'));
        $('#tag-column1').empty();
        $('#tag-column2').empty();
        for (var i = 0; i  < partialTags.length; i++) {
            var tagSug;
            if (i < 5) {
                // Paint first column
                tagSug = $.tmpl('tagSugTemplate', {'tag': partialTags[i]}).appendTo('#tag-column1');
            } else {
                // Paint second column
                tagSug = $.tmpl('tagSugTemplate', {'tag': partialTags[i]}).appendTo('#tag-column2');
            }
            // Check if selected
            if (self.finalTags.indexOf(partialTags[i]) != -1) {
                tagSug.find('span').css('text-shadow', 'rgb(96, 193, 207) 0.1em 0.1em 0.1em');
                tagSug.find('.main-icon').removeClass('icon-plus-sign');
                tagSug.find('.main-icon').addClass('icon-remove-sign');
            }
            // Set listeners
            tagSug.find('.main-icon').click((function(that, tag) {
                return function() {
                    var obj = $(this);
                    var span = obj.siblings('span');
                    // Add or remove the tag from the list
                    if (that.finalTags.indexOf(tag) == -1) {
                        that.finalTags.push(tag);
                    } else {
                        that.finalTags.splice(that.finalTags.indexOf(tag), 1);
                    }
                    // Change style
                    if (obj.hasClass('icon-plus-sign')) {
                        span.css('text-shadow', 'rgb(0, 43, 103) 0.1em 0.1em 0.1em');
                        obj.removeClass('icon-plus-sign');
                        obj.addClass('icon-remove-sign');
                    } else {
                        span.removeAttr('style');
                        obj.removeClass('icon-remove-sign');
                        obj.addClass('icon-plus-sign');
                    }
                }
            })(self, partialTags[i]));
        }
    };

    /**
     * Include the pagination element for the suggested tags
     */
    var includePagination = function includePagination(self, tags) {
        // Calculate number of pages
        var nPages = Math.ceil(tags.length / 10)
        var pagElem, ul, li, remaining = 10;
        self.tagsPages = {
            'currentPage': 0,
            'pagesContent': {}
        };

        for (var i = 0; i < nPages; i++) {
            self.tagsPages.pagesContent['page-' + i] = [];

            // Calculate last iteration size
            if (i == (nPages - 1)) {
                remaining = tags.length - 10*(i);
            }

            for (var k = 0; k < remaining; k++) {
                self.tagsPages.pagesContent['page-' + i].push(tags[10*i + k]);
            }
        }
        // Create pagination component
        pagElem = $('<div></div>').addClass('pagination pagination-centered');
        ul = $('<ul></ul>');
        li = $('<li></li>').attr('id', 'prev').click((function(that) {
            return function() {
                if (that.tagsPages.currentPage > 0) {
                    that.tagsPages.currentPage -= 1;
                    paintSuggestions(that, that.tagsPages.pagesContent['page-' + that.tagsPages.currentPage]);
                }
            }
        })(self)).appendTo(ul);

        $('<a></a>').append('<i></i>').attr('class', 'icon-chevron-left').appendTo(li);

        li = $('<li></li>').attr('id', 'next').click((function(that) {
            return function() {
                if (that.tagsPages.currentPage < (nPages - 1)) {
                    that.tagsPages.currentPage += 1;
                    paintSuggestions(that, that.tagsPages.pagesContent['page-' + that.tagsPages.currentPage]);
                }
            }
        })(self)).appendTo(ul);

        $('<a></a>').append('<i></i>').attr('class', 'icon-chevron-right').appendTo(li);
        ul.appendTo(pagElem);
        pagElem.appendTo('#pagination');

        //Load first page
        paintSuggestions(self, self.tagsPages.pagesContent['page-0']);
    };

    TagManager.prototype.displaySuggestions = function displaySuggestions(tags) {

        $('.modal-body').empty();
        $.template('suggestionTemplate', $('#suggestion_template'))
        $.tmpl('suggestionTemplate').appendTo('.modal-body');

        if (tags.length > 10) {
            includePagination(this, tags);
        } else {
            paintSuggestions(this, tags);
        }

        $('.modal-footer').empty();
        $('<input></input>').val('Accept').attr('type', 'button').addClass('btn btn-basic').click((function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            this.updateTags();
        }).bind(this)).appendTo('.modal-footer');
    };

    /**
     * Client for the tagging update API
     */
    TagManager.prototype.updateTags = function updateTags() {
        // Update Tags
        var csrfToken = $.cookie('csrftoken');
        var request = {
            'tags': this.finalTags
        };
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: "PUT",
            url: EndpointManager.getEndpoint('TAG_ENTRY', {
                'organization': this.offering.getOrganization(),
                'name': this.offering.getName(),
                'version': this.offering.getVersion()
            }),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(request),
            success: (function (response) {
                $('#message').modal('hide');
                MessageManager.showMessage('Updated', 'The offering has been updated')
                this.caller.refreshAndUpdateDetailsView();
            }).bind(this),
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                $('#message').modal('hide');
                MessageManager.showMessage('Error', msg);
            }
        });
    };

})();