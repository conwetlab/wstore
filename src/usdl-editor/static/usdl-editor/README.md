# usdl-editor
A simple Web application for editing Linked USDL descriptions.

## Installation

Download the directory into a subfolder of your Web server documents folder. Invoke `index.html` from a browser (Firefox, Chrome, Safari).

On Google Chrome you have the option to install it as a Web App. Open `chrome://chrome/extensions/`  and load the folder as an unpacked extension. Installing the editor as a Web app, allows to run it locally without any XSS hassle.

## Usage

The editor opens with an empty service description. You can create as many service or models you in the current description on the left hand side. For a selected service or model you can use the different tab sections to create  or add information for this service in specific cards. You can switch between the cards by clicking into the card frame or close a card by clicking into the 'X' button on the upper right of a card. You can scroll inside a card by swiping on the card.

The about tab provides a dialog for the information of the description as a whole, whereas the other tabs always refer to the selected service or model.

For saving a description click on the publish button in the lower command area. Choose an option for the format by clicking on one of the icon (RDF, TURTLE, JSON).

In order to load an existing service description you have to drag&drop it from your file system. There is no connection to the repository currently).

Loading additional domain vocabularies is done automatically if the `owl:imports` property of the service description is used. Please note that the same origing policy is maintained for importing vocabularies. 
Importing vocabularies is necessary for editing properties.

(The settings and repository button do not work currently).

## Development

- Source hosted at [GitHub](https://github.com/linked-usdl/usdl-editor)
- Report issues, questions, feature requests on [GitHub Issues](https://github.com/linked-usdl/usdl-editor/issues)

## Authors

[Torsten Leidig] (https://github.com/drleidig)

License: [MIT] (https://github.com/linked-usdl/usdl-editor/blob/master/LICENSE.md)

For convinience the project comes with many other Open Source libraries, which have their own license statement.
