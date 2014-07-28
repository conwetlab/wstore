/*
 * Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid
 *
 * This file is part of WStore.
 *
 * WStore is free software: you can redistribute it and/or modify
 * it under the terms of the European Union Public Licence (EUPL) 
 * as published by the European Commission, either version 1.1 
 * of the License, or (at your option) any later version.
 *
 * WStore is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * European Union Public Licence for more details.
 *
 * You should have received a copy of the European Union Public Licence
 * along with WStore.  
 * If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.
 */

(function() {

    MenuPainter = function MenuPainter(firstListener, secondListener, thirdListener) {
        this.firstListener = firstListener;
        this.secondListener = secondListener;
        this.currentState = '';

        if (thirdListener) {
            this.thirdListener = thirdListener;
        }

        this.expanded = true;
        setListeners(this);
    };

    var clickHandlerDecrease = function clickHandlerDecrease() {
        this.expanded = false;
        $('.store-menu-container').css('opacity', '0');
        $('.left-bar').animate({'width': '0'}, 1000, function() {
            $('.left-bar').empty();
            $('.left-bar').append('<a><i class="icon-th-list"></i></a>');
            $('.left-bar a').click(clickHandlerIncrease.bind(this));
            $('.left-bar').animate({'width': '50px'}, 500);
        }.bind(this));
    };

    var clickHandlerIncrease = function clickHandlerIncrease() {
        this.expanded = true;
        $('.left-bar').animate({'width': '0'}, 500, function() {
            $('.left-bar').empty()
            $.template('menuTemplate', $('#menu-template'));
            $.tmpl('menuTemplate').appendTo('.left-bar');
            this.setState(this.currentState);

            $('.store-menu-container').css('opacity', '1');
            $('.left-bar').animate({'width': '205px'}, 1000, function() {
                setListeners(this);
            }.bind(this));
        }.bind(this));
    };

    var setListeners = function setListerners(self) {
        $('.store-menu-container').css('opacity', '1');
        // Set close button listeners
        $('.close-btn').off();
        $('.close-btn').mouseover(function() {
            $('.store-menu').css('left', '25px');
            $('.store-sub-menu').css('left', '25px');
        });

        $('.close-btn').mouseout(function() {
            $('.store-menu').removeAttr('style');
            $('.store-sub-menu').removeAttr('style');
        });

        $('.close-btn').click(function() {
            this.decrease();
        }.bind(self));

        // Set button listeners
        $('#menu-first-text').off('click');
        $('#menu-second-text').off('click');
        $('#menu-third-text').off('click');

        $('#menu-first-text').click(function() {
            this.setState('first');
            this.firstListener();
        }.bind(self));

        $('#menu-second-text').click(function() {
            this.setState('second');
            this.secondListener();
        }.bind(self));

        if (self.thirdListener) {
            $('#menu-third-text').click(function() {
                this.setState('third');
                this.thirdListener();
            }.bind(self));
        }

        // Set navigation listeners
        $('.store-sub-menu li').click(function() {
            var anchor = $(this).find('a');
            window.location = anchor.attr('href');
        });
    };

    /**
     * Launches  the decreasing animation
     */
    MenuPainter.prototype.decrease = function decrease() {
        if (this.expanded) {
            var clicker = clickHandlerDecrease.bind(this);
            clicker();
        }
    }

    /**
     * Launches the increasing animation
     */
    MenuPainter.prototype.increase = function increase() {
        if (!this.expanded) {
            var clicker = clickHandlerIncrease.bind(this);
            clicker();
        }
    };

    var getCurrentButton = function getCurrentButton(self) {
        var ids = {
           'first': '#menu-first-text',
           'second': '#menu-second-text',
           'third': '#menu-third-text'
        }

        var cssClasses = {
            'first': 'menu-first-hover',
            'second': 'menu-second-hover',
            'third': 'menu-third-hover'
        }

        return {
            'id': ids[self.currentState],
            'cssClass': cssClasses[self.currentState]
        };
    };

    MenuPainter.prototype.setState = function setState(state) {
        this.currentState = state;

        // Set the proper selection in the menu
        $('#menu-first-text').removeClass('menu-first-hover');
        $('#menu-second-text').removeClass('menu-second-hover');
        $('#menu-third-text').removeClass('menu-third-hover');

        if (this.currentState) {
            var selectedBtn;

            selectedBtn = getCurrentButton(this);
            $(selectedBtn.id).addClass(selectedBtn.cssClass);
        }
    };

})();