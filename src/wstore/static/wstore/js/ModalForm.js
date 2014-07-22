(function() {

    /**
     * Abstract class defining a modal window with a 
     * form
     * 
     * @param title Title of the window
     * @param mainTemplate Template used in the window
     */
    ModalForm = function ModalForm(title, mainTemplate) {
        this.title = title;
        this.mainTemplate = mainTemplate;
        this.modalCreated = false;
    };

    /**
     * Method to be implemented by child classes, Include the
     * contents of the modal window
     */
    ModalForm.prototype.includeContents = function includeContents() {  
    };

    /**
     * Method to be implemented by child classes, Set listeners of
     * the modal window
     */
    ModalForm.prototype.setListeners = function setListeners() {
    };

    /**
     * Displays the modal window and renders the template
     */
    ModalForm.prototype.display = function display(container) {
        if (!this.modalCreated) {
            if (container) {
                MessageManager.showMessage(this.title, '', container);
            } else {
                MessageManager.showMessage(this.title, '');
            }
            this.modalCreated = true;
        }

        $('.modal-body').empty();
        $.template('modalTemplate', $(this.mainTemplate));
        $.tmpl('modalTemplate').appendTo('.modal-body');

        this.includeContents();
        this.setListeners();
    }
})();