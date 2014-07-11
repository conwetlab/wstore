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

        if (thirdListener) {
            this.thirdListener = thirdListener;
        }

        this.expanded = true;
        setListeners(this);
    };

    var clickHandlerDecrease = function clickHandlerDecrease() {
        this.expanded = false;
        $('.left-bar').animate({'width': '50px'}, 1000, function() {
            $('.left-bar').empty();
            $('.left-bar').append('<a><i class="icon-th-list"></i></a>');
            $('.left-bar a').click(clickHandlerIncrease.bind(this));
        }.bind(this));
    };

    var clickHandlerIncrease = function clickHandlerIncrease() {
        this.expanded = true;
        $('.left-bar').empty()
        $.template('menuTemplate', $('#menu-template'));
        $.tmpl('menuTemplate').appendTo('.left-bar');

        $('.left-bar .icon-remove').click(clickHandlerDecrease.bind(this))
        $('.left-bar').animate({'width': '205px'}, 1000, function() {
            setListeners(this);
        }.bind(this));
    };

    var setListeners = function setListerners(self) {
        $('#menu-first-text').off('click');
        $('#menu-second-text').off('click');
        $('#menu-third-text').off('click');

        $('#menu-first-text').click(function() {
            $('#menu-first-text').addClass('menu-first-hover');
            $('#menu-second-text').removeClass('menu-second-hover');
            $('#menu-third-text').removeClass('menu-third-hover');
            this.firstListener();
        }.bind(self));

        $('#menu-second-text').click(function() {
            $('#menu-first-text').removeClass('menu-first-hover');
            $('#menu-second-text').addClass('menu-second-hover');
            $('#menu-third-text').removeClass('menu-third-hover');
            this.secondListener();
        }.bind(self));

        if (self.thirdListener) {
            $('#menu-third-text').click(function() {
                $('#menu-first-text').removeClass('menu-first-hover');
                $('#menu-second-text').removeClass('menu-second-hover');
                $('#menu-third-text').addClass('menu-third-hover');
                this.thirdListener();
            }.bind(self));
        }
    };

    MenuPainter.prototype.decrease = function decrease() {
        if (this.expanded) {
            var clicker = clickHandlerDecrease.bind(this);
            clicker();
        }
    }

    MenuPainter.prototype.increase = function increase() {
        if (!this.expanded) {
            var clicker = clickHandlerIncrease.bind(this);
            clicker();
        }
    };
})();