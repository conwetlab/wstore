=========================
User and Programmer Guide
=========================

------------
Introduction
------------

This page contains the user and programmer guide for WStore, a reference implementation of the `Store Generic Enabler`_.

.. _Store Generic Enabler: https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/FIWARE.OpenSpecification.Apps.Store

----------
User Guide
----------

This user guide contains a description of the different tasks that can be performed in WStore using its web interface from different points of view, depending on the roles of the corresponding user.

Profile configuration
=====================

All users can configure their profile including some information such as a default tax address.

To configure the user profile, move your mouse to username on the top right of the page and choose settings.

.. image:: /images/Wstore_ug.png
   :align: center

In the displayed modal, it is possible to view user profile info. To change this info or provide new one, select the Edit button.

.. image:: /images/none.png
   :align: center

Fill the different fields through the Tabs and press Update.

.. image:: /images/none.png
   :align: center

.. image:: /images/none.png
   :align: center

Service provider
================

This section explains how a service provider can create and monetize her service offerings using WStore GUI.

Registering a resource
----------------------

Resources are used in the offerings in order to allow to include downloadable digital assets, such as applications, widgets, etc.

To register a resource, select the My Offerings view.

.. image:: /images/none.png
   :align: center

Select the options dropdown and choose Register resource

.. image:: /images/none.png
   :align: center

In the displayed modal, the first step is filling the resource name, the resource version and the resource description. Then, it is necessary to provide a mime type for the resource. The next step consists on uploading the resource or providing a link from where the resource can be accessed.

Finally, it is required to choose whether the resource is open or not. This flag is used to specify if the resource can contain an authorization mechanism that does not depend on WStore, for example an API resource that requires authenticated users.

.. image:: /images/none.png
   :align: center

Viewing resources
-----------------

A service provider is able to view the resources which are already registered. To view the resources, select the catalogue view and choose View resources in the dropdown menu.

.. image:: /images/none.png
   :align: center

In the displayed modal, you can see the different resources you have registered.

.. image:: /images/none.png
   :align: center

It is possible to view the details of a registered resource clicking on it.

.. image:: /images/none.png
   :align: center

Editing a resource
------------------

Depending on the state of the resource (created or used) a service provider can edit the information of a resource.

To edit a resource, click on the edit button inside the resource details view.

.. image:: /images/none.png
   :align: center

If the resource is in created state, that is, the resource has not been included in any offering, it is possible to modify the description, the content type and whether the resource is open or not.

.. image:: /images/none.png
   :align: center

If the resource is in used state, only the description can be modified.

.. image:: /images/none.png
   :align: center

Upgrading a resource
--------------------

It is possible to upgrade resources providing a new version of them. Note that when a new version of a resource is provided all the offerings that include this resource are automatically updated, so this is the mechanism that allows providers to perform automatic updates on their published apps, for example for including a patch.

To upgade a resource, click on the upgrade button in the resource details view.

.. image:: /images/none.png
   :align: center

Then, it is necesary to provide the new version number and the new resource itself.

.. image:: /images/none.png
   :align: center

Deleting a resource
-------------------

A provider can delete their resources, depending on the state of the resource this action has different behaviours. If the resource is in created state, so it is not being used in any existing offering, the resource is completely removed from WStore. On the other hand, if the resource is in used state, it is set as deleted and cannot be included in more offerings.

To remove a resource, click on the remove button in the resource details view.

.. image:: /images/none.png
   :align: center

Then, press Accept when asked.

.. image:: /images/none.png
   :align: center

Creating an offering
--------------------

Offerings are the main entity managed by WStore and include all the relevant information such as the pricing model, legal conditions, interactions, service level agreement, etc. To create an offering, go to My Offerings. and choose Create offering from the Provider Options dropdown.

.. image:: /images/none.png
   :align: center

In the displayed modal, fill the name, version and description fields. Next, provide an image and an optional set of screenshots

The next step consits on selecting how to provide the notification URL. This field is used by WStore to notify the service provider when its offering has been purchased. There are three different options: (a) Provide a new notification URL for this offering. (b) Use the default notification URL of the provider that can be configured in the user profile configuration form. (c) Not using a notification URL for this offering.

Finally, choose whether the offering is open or not, that is, all the resources will be direcly accessible by WStore customers whitout the need of acquiring the offering. Note that if the offering is created as open, only open resources (resources that do not contain an external authetication mechanism that do not depend on WStore)can be bound to it.

.. image:: /images/none.png
   :align: center

The next step is providing an USDL document describing the offering. There are three possible options: (a) Create a simple USDL just by using the provided form. (b) Upload a USDL document. (c) Provide an URL pointing to the USDL document if it as been previously uploaded into a repository.

.. image:: /images/none.png
   :align: center

.. image:: /images/none.png
   :align: center

.. image:: /images/none.png
   :align: center

Once the USDL info has been provided, the next step consist of including Applications. This applications need to be uderstood as OAuth2 Applications and are those registered in the Identity Manger by the provider. Including Applications in an offering allows to grant real access to the related services via OAuth2 to the customers that acquire the offering.

.. image:: /images/none.png
   :align: center

The final step consist of selecting resources previously registered by the provider.

.. image:: /images/none.png
   :align: center

Updating an offering
--------------------

It is possible to update an offering info by providing a new USDL description or including new images.

To update an offering, go to My Offerings view and the Provided section. This tab contains the offerings provided by the service provider.

.. image:: /images/none.png
   :align: center

Select the offering to be updated. Note that only offerings with uploaded state (Offerings that have not been published yet) can be updated.

.. image:: /images/none.png
   :align: center

In the advanced operations, select Edit.

.. image:: /images/none.png
   :align: center

In the displayed modal, it is possible to provide a USDL as in the offering creation. It is also possible to provide some screenshots or a new logo.

.. image:: /images/none.png
   :align: center

Binding resources
-----------------

Once an offering has been created it is still possible to manage the included resources. To bind resources, select the My Offerings view and the Provided section. Then select the offering to be bound. Note that only offerings with uploaded state can be updated.

Select the “Bind resources” option.

.. image:: /images/none.png
   :align: center

In the displayed modal, select the resources to be bound and press Accept

.. image:: /images/none.png
   :align: center

Note that this operation is an absolute update, that is, the selected resources are the bound resources. Therefore, it is possible to bind and unbind resources in the same action.

Publishing an offering
----------------------

Publishing an offering means start selling it. To publish an offering select the My Offerings view and the Provided section. Then select the offering to be published.

In the offering details view select the Publish option.

.. image:: /images/none.png
   :align: center

In the displayed modal, select the Marketplaces where publish the offerings. Note that selecting a Marketplace is not mandatory.

.. image:: /images/none.png
   :align: center

The offering is now Published and cannot be updated.

Tagging an offering
-------------------

It is possible for an offering provider to tag their offerings. To tag an offering, select the My Offerings view and the Provided section. Then select the offering to be tagged.

Select the Update tags option

.. image:: /images/none.png
   :align: center

Include the different tags and press Accept

.. image:: /images/none.png
   :align: center

You may also be suggested some tags that may fit your offering.

.. image:: /images/none.png
   :align: center

Deleting an offering
--------------------

The action of deleting an offering has different effects depending on its state. If the offering has not been published, it is completely deleted from WStore. However, If the offering has been published, its state changes to deleted and cannot be acquired anymore, but customers that has already acquired it still has access to the offering and its resources.

To delete an offering, select the My Offerings view and the Provided section. Then select the offering to be deleted.

In the offering details view, select the Delete offering option

.. image:: /images/none.png
   :align: center

Select accept in the displayed window.

.. image:: /images/none.png
   :align: center

If the offering has been published the option Delete replaces Publish as main action.

.. image:: /images/none.png
   :align: center

Customer
========

This section explains how a customer can search and acquire offerings using WStore GUI.

Searching for offerings
-----------------------

There are some options for searching offerings in WStore, As it can be seen in the following image, the main page contains the Top rated and the latest offerings.

.. image:: /images/customer/Wstore_ug_search_1.png
   :align: center

To search using a keyword type it in the textbox and press Search.

.. image:: /images/customer/Wstore_ug_search_2.png
   :align: center

The offerings that match the search are shown.

.. image:: /images/customer/Wstore_ug_search_3.png
   :align: center

It is also possible to view all the offerings selecting the *All* button.

.. image:: /images/customer/Wstore_ug_search_2.png
   :align: center

Acquiring an offering
---------------------

The first step to acquire a published offering is selecting it after searching. To start with the purchasing process click on the button included in the offering.

.. image:: /images/customer/Wstore_ug_pur_1.png
   :align: center

Arternatively, it is possible to select the Acquire button in the offering details view.

.. image:: /images/customer/Wstore_ug_pur_2.png
   :align: center

If the offering has some legal terms, you will be forced to accept them in order to be able to acquire it.

.. image:: /images/customer/WStore_Accepting_Terms.png
   :align: center

Once that you have accepted the terms, you will have to provide a tax address for the purchase. Is possible to use the default tax address from the user profile by clicking the checkbox Use user profile tax address. Then, select Accept.

.. image:: /images/customer/Wstore_ug_pur_3.png
   :align: center

In case the offering can be acquired under different pricing models, the first step is selecting the plan.

.. image:: /images/customer/Select_plan.png
   :align: center

WStore informs that the payment process will continue in a separate window.

.. image:: /images/customer/Wstore_ug_pur_4.png
   :align: center

WStore redirects the browser to the PayPal confirmation page.

.. image:: /images/customer/Wstore_ug_pur_5.png
   :align: center

Introduce your PayPal credentials and confirm the payment.

.. image:: /images/customer/Wstore_ug_pur_6.png
   :align: center

Return to WStore page and end the process by closing the displayed window.

.. image:: /images/customer/Wstore_ug_pur_7.png
   :align: center

Downloading resources and invoices
----------------------------------

To download the resources and the invoices of a purchased offering, select the My Offerings view and the Acquired section . Then, select the offering.

.. image:: /images/customer/Wstore_ug_downl_1.png
   :align: center

Select the Resources button.

.. image:: /images/customer/Wstore_ug_downl_2.png
   :align: center

In the displayed modal, is possible to download invoices and resources by clicking on the link.

.. image:: /images/customer/Wstore_ug_downl_3.png
   :align: center

Reviewing an offering
---------------------
To review and rate an offering, select an acquired or an open offering and click on the Review button situated in the Reviews section.

.. image:: /images/customer/Wstore_ug_com_1.png
   :align: center

Fill the number of stars and give a comment.

.. image:: /images/customer/Wstore_ug_com_2.png
   :align: center

Admin
=====

This section describes the different tasks that can be performed by an admin user using WStore GUI.

Registering WStore on a Marketplace
-----------------------------------

WStore can be registered on a Marketplace in order to allow service providers to publish their offerings on them, making their offerings available to potential customers that search for offerings in the Marketplace.

Note that this process is made from WStore GUI, since WStore needs to have information about in what Marketplaces is registered on.

To register WStore on a Marketplace, select the Administration view.

.. image:: /images/none.png
   :align: center

Press the Add symbol of the Marketplaces row.

.. image:: /images/none.png
   :align: center

Fill the internal name and the host of the Marketplace.

.. image:: /images/none.png
   :align: center

Pressing on the Marketplaces row is possible to view in what Marketplaces WStore is registered on.

.. image:: /images/none.png
   :align: center

.. image:: /images/none.png
   :align: center

Registering a Repository on WStore
----------------------------------

It is possible to register some instances of the Repository GE in order to allow service providers to Upload USDL documents directly when creating an offering.

To register a Repository on WStore select the Administration view and press the Add symbol of the Repositories row.

.. image:: /images/none.png
   :align: center

Fill the internal name and the host of the Repository.

.. image:: /images/none.png
   :align: center

Pressing on the Repositories row is possible to view what Repositories are registered on WStore.

.. image:: /images/none.png
   :align: center

.. image:: /images/none.png
   :align: center

Registering a RSS on WStore
---------------------------

It is possible to register RSS instances on WStore in order to perform the revenue sharing of the purchased offerings.

To register a RSS on WStore select the Administration view and press the Add symbol of the RSS row.

.. image:: /images/none.png
   :align: center

Fill the internal name and the host of the RSS, as well as the default expenditure limits for WStore.

.. image:: /images/none.png
   :align: center

Pressing on the RSS row is possible to view what RSSs are registered on WStore.

.. image:: /images/none.png
   :align: center

.. image:: /images/none.png
   :align: center

Registering a Price Unit
------------------------

Price Units are used in order to determine the concrete pricing model that applies to an offering.

To include a new supported price unit select the Administration view and click the add symbol in the Pricing model units row.

.. image:: /images/none.png
   :align: center

Fill the name and the defined model of the unit. If the defined model is Subscription it is also necessary to specify the renovation period.

.. image:: /images/none.png
   :align: center

It is possible to view existing units by click on the Pricing model units row.

.. image:: /images/none.png
   :align: center

.. image:: /images/none.png
   :align: center

----------------
Programmer Guide
----------------

The programmer guide contains a description of the actions that can be performed by a developer, in order to integrate WStore capabilities with her solution using WStore API. For a complete description of WStore API view `Store GE Open API Specification`_.

.. _Store GE Open API Specification: https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/FIWARE.OpenSpecification.Apps.Store

API Authentication and authorization
====================================

WStore API requires users to be authenticated and requires them to authorize developer‘s application in order to access WStore API in their name. To perform this process WStore uses an OAuth2 approach.

Depending on the authorization mode of the WStore instance there are two possible ways for API authorization. If the WStore instance is using an idM GE, the developer application should include a valid token obtained from the idM in all the related requests. For information on how to authorize an application using the idM GE have a look at `Identitity Management GE User and Programmers Guide`_.

.. _Identitity Management GE User and Programmers Guide: https://forge.fi-ware.eu/plugins/mediawiki/wiki/fiware/index.php/Identity_Management_-_KeyRock_-_User_and_Programmers_Guide

In case the WStore instance uses it own authentication mechanism the developer should follow the following process.

The first step consist on user authentication and application authorization. Note that the application should be registered in WStore in order to have a client_id and a client_secret. To perform this step is necessary to make the following request: ::

	GET /oauth2/auth HTTP/1.1
	Accept: application/json


This request must include the following params.

* client_id: Id of the application in WStore.
* redirect_uri: URI where WStore redirects when the call finishes
* response_type:

When this request is performed the user is redirected to a page where the user can log in

.. image:: /images/none.png
   :align: center

and authorize the application.

.. image:: /images/none.png
   :align: center

Once the user has authorized the application, an authorization code is returned to the redirect_uri provided.

The next step is to acquire the access token. To perform this step, it is necessary to make the following request: ::

	POST /oauth2/token HTTP/1.1


This request must include the following params.

* client_id: Id of the application in WStore
* client_secret: Secret of the application in WStore
* grant_type:
* code: Authorization code provided in the previous step
* redirect_uri: URI where WStore redirects when the call finishes

WStore responds to this request providing an access and a refresh token. The access token must be included as a header in all API requests, and the refresh token is used to acquire a new access token in case it expires.

To refresh the access token is necessary to make the following request: ::

	POST /oauth2/token HTTP/1.1


This request must include the following params.
* client_id: Id of the application in WStore,
* client_secret: Secret of the application in WStore,
* grant_type:
* refresh_token: refresh token provided in the previous step

Resources management integration
================================

It is possible for a developer to integrate the Resources API in order to monetize different catalogues included in the developer solution. To perform this monetization, it is necessary to register the resources using a POST request, making them available to be bound in an offering.

Registering resources
---------------------

The contents of the request depends on the resource characteristics and the developer criteria.

* Downloadable resource

	If the resource is a downloadable resource and the resource is provided, it is possible to provide the resource itself by creating a multipart request or encode it in base64 and include this encoding in the JSON ::

		POST /api/offering/resources HTTP 1.1
		Content-type: multipart/form-data
		{

		   “name”: “Smart City Lights Mashup”,
		   “version”: “1.0”,
		   “description”: “This resource contains a mashup for Smart City Lights”,
		   “content_type”: “application/x-mashup+mashable-application-component”

		}
		+ FILE


	::

		POST /api/offering/resources HTTP 1.1
		Content-type: application/json
		{

		   “name”: “Smart City Lights Mashup”,
		   “version”: “1.0”,
		   “description”: “This resource contains a mashup for Smart City Lights”,
		   “content_type”: “application/x-mashup+mashable-application-component”,
		   “content”: {
		       “name”: “SmartCityLights.wgt”,
		       “data”: “encoded_data”
		   }
		}


* Downloadable resource providing link

	If the resource is a downloadable resource but the service provider has her own server to serve media files, s/he can provide an URL where the resource can be downloaded instead of the resource itself, making the request as follows. ::

		POST /api/offering/resources HTTP 1.1
		Content-type: application/json
		{
		    “name”: “Smart City Lights Mashup”,
		    “version”: “1.0”,
		    “description”: “This resource contains a mashup for Smart City Lights”,
		    “content_type”: “application//x-mashup+mashable-application-component”,
		    “link”: “https://downloadmashuplink.com/smartcity”
		}

	All this requests return a 201 code if everything is sucessful.

Getting resources
-----------------

It is also possible to retrieve the information of the different resources belonging to the user making the following call. ::

	GET /api/offering/resources HTTP 1.1
	Accept: application/json

This call returns a list with the following format ::

	HTTP/1.1 200 OK
	Content-Type: application/json
	Vary: Cookie

	{
	  [
	     {
	        “content_type”: "application/x-mashup+mashable-application-component"
	        “description”: "Smart City Lights is an app"
	        “name”: "Smart City Management"
	        “version”: "1.0"
	     }
	  ]
	}


Offerings management integration
================================

WStore also offers the different operations to manage offerings through its API in order to allow developers to create different applications capable of performing this management and allowing external applications to enrich their resources with pricing models, service level agreements, etc.

Getting offerings
-----------------

The next request shows how is possible to retrieve offerings using WStore API. The next call is supposed to return all the offerings published (its state is published) in WStore. ::

	GET /api/offering/offerings HTTP 1.1
	Accept: application/json


WStore responds with a list of offerings with the following format: ::

	HTTP/1.1 200 OK
	Content-Type: application/json
	Vary: Cookie

	[
	    {
	        "name":"SmartCityLights",
	        "owner_organization": "CoNWeT",
	        "owner_admin_user": "app_provider",
	        "version": "1.0",
	        "state": "published",
	        "description_url": "http://examplerepository.com/storeCollection/SmartCityLights",
	        "marketplaces": [example_marketplace],
	        "resources": [{
	             “name”: “Smart City Lights Mashup”,
	             “version”: “1.0”,
	             “description”: “This resource contains a mashup for Smart City Lights”,
	        }],
	        "applications": [{
	            "id": 18,
	            "name": "Context broker",
	            "url": "https://orion.lab.fi-ware.eu",
	            "description": "Context broker"
	        }],
	        "rating": "5",
	        "comments": [{
	             "date": "2013/01/16",
	             "user": "admin",
	             "rating": "5",
	             "comments": "Good offering"
	        }],
	        "tags": [smart, city],
	        "image_url": "http://examplestore.com/media/image",
	        "related_images": [],
	        "offering_description": {parsed USDL description info},
	    }
	]


The applications field only appears if an identity manager is being used. This field contains the different OAuth2 applications offered in the offering.

Note that the resources field contains the information of the resources bound to the offering. In case that the offering had been purchased by the user making the call and that the resource was a downloadable resource, this field contains also a URL where download the resource. As it is mentioned above the previous call returns all offerings whose state is published. However it is possible to configure the API call using query strings in order to limit the number, select the first offering expected or ask for the user offerings (provided and purchased). To perform this calls the following query strings can be used and combined.

* filter=published : Returns published offerings
* filter=purchased : Returns the offerings purchased by the user making the call
* filter=provided : Returns the offerings provided by the user making the call

* sort=date : Sorts the returned offerings using the date (default).
* sort=name : Sorts he returned offerings using the name.
* sort=popularity : Sorts he returned offerings using the popularity.

* start=<number> : Defines the first offering to be returned
* limit=<number> : Defines the number of offerings to be returned

This two query strings can be combined with the filter query string and are used to paginate the results. Additionally is possible to use action=count. This query string can be combined with filter, and modifies the functionally of the call that now returns the number of offerings instead of the offerings info. It is also possible to request a single offering by making the following request ::

	GET /api/offering/offerings/{organization}/{name}/{version} HTTP 1.1
	Accept: application/json


The response of that call is similar as the previous one but only an offering is returned instead of a list of offerings.

Searching offerings
-------------------

WStore allows to search for offerings using a keyword. To perform this action it is necessary to make the following call. ::

	GET /api/search/{keyword} HTTP 1.1
	Accept: application/json

In this case the response is similar to the getting offerings call but only offerings that satisfy the keyword are returned

Creating an offering
--------------------

WStore allows to create new offerings through its offering API. There are three different ways of creating an offering depending on the state of the USDL describing the offering. If the user has the USDL, s/he can include it in the request as in the following call. ::

	POST  /api/offering/offerings HTTP 1.1
	Content-Type: application/json
	{
	   "name": "SmartCityLigths",
	   "version": "1.0",
	   "image": {
	       “name”: “catalogue.png”,
	       “data”: <encoded_data>,
	   },
	   "applications": [{
	       "id": 18,
	       "name": "Context broker",
	       "url": "https://orion.lab.fi-ware.eu",
	       "description": "Context broker"
	   }],
	   "related_images": [],
	   "repository": "testbed_repository",
	   "resources": [{
	        "provider": "app_provider",
	        "name": "Smart City Management",
	        "version": "1.0"
	    }],
	   "offering_description": {
	       “content_type”: “text/turtle”,
	       “data”: "raw USDL document (RDF XML, N3 , Turtle)"
	   }
	}


If the USDL is uploaded previously into a repository then the user can include its URL as in the following request. ::

	POST  /api/offering/offerings HTTP 1.1
	Content-Type: application/json
	{

	   "name": "example_offering",
	   "version": "1.0",
	   "image": {
	       “name”: “catalogue.png”,
	       “data”: <encoded_data>,
	   },
	   "applications": [{
	       "id": 18,
	       "name": "Context broker",
	       "url": "https://orion.lab.fi-ware.eu",
	       "description": "Context broker"
	   }],
	   "related_images": [],
	   "resources": [{
	        "provider": "app_provider",
	        "name": "Smart City Management",
	        "version": "1.0"
	    }],
	   "description_url”: “http://examplerepository/collection/SmartCity.rdf”
	}


Finally, If the user does not have an USDL s/he can provide basic info that is used to create an USDL document in WStore. ::

	POST  /api/offering/offerings HTTP 1.1
	Content-Type: application/json
	{

	   "name": "example_offering",
	   "version": "1.0",
	   "image": {
	       “name”: “catalogue.png”,
	       “data”: <encoded_data>,
	   },
	   "related_images": [],
	   "resources": [{
	        "provider": "app_provider",
	        "name": "Smart City Management",
	        "version": "1.0"
	    }],
	   "offering_info": {
	       "description": "Description of the offering",
	       "pricing": {
	           "price_model": "free"
	       },
	       "legal" : {
	           "title": "Terms and conditions",
	           "text": "Text of terms and conditions"
	       }
	   }
	}

The images passed in this call are included in the JSON document directly, encoded in base64 format; moreover, screenshots must be included in the related_images field as a list of elements with the same format as the image field.

WStore responds to this call with a 201 Created code if the request is successful. Note that to perform this action the user making the call must have the provider role.

Updating an offering
--------------------

WStore supports updating created offerings that have not been published yet. To update an uploaded offering, new logo, screenshots or USDL can be provided. Note that the name and version of the offering cannot be changed since are used to identify the offering. Similarly to the offering creation, there are three different ways of updating an offering depending on where the USDL is. If the USDL document is directly provided, this document overrides the previous USDL description in the repository; therefore, this method for updating can be used even if the offering was created using a repository link. ::

	PUT /api/offering/offerings/{organization}/{name}/{version} HTTP 1.1
	Content-Type: application/json
	{
	   "image": {
	       “name”: “catalogue.png”,
	       “data”: <encoded_data>,
	   },
	   "related_images": [],
	   "repository": "example_repository",
	   "offering_description":  {
	       “content_type”: “text/turtle”,
	       “data”: "raw USDL document (RDF XML, N3 , Turtle)"
	   }
	}


If a USDL link is provided, this URL must be the same as the provided when the offering was created. This method is the one used in case that multiple applications were writing over the USDL description. ::

	PUT /api/offering/offerings/{organization}/{name}/{version} HTTP 1.1
	Content-Type: application/json
	{
	   "image": {
	       “name”: “catalogue.png”,
	       “data”: <encoded_data>,
	   },
	   "related_images": [],
	   "repository": "example_repository",
	   "description_url": "http://examplerepository/collection/SmartCity.rdf"
	}


If the information is included, the new created USDL will override the existing one. ::

	PUT /api/offering/offerings/{organization}/{name}/{version} HTTP 1.1
	Content-Type: application/json
	{
	   "image": {
	       “name”: “catalogue.png”,
	       “data”: <encoded_data>,
	   },
	   "related_images": [],
	   "repository": "example_repository",
	   "offering_info": {
	       "description": "Description of the offering",
	       "pricing": {
	           "price_model": "free"
	       },
	       "legal" : {
	           "title": "Terms and conditions",
	           "text": "Text of terms and conditions"
	       }
	   }
	}

WStore returns a 200 OK code in case the request is successful. Note that to perform this action, the user making the call must be the owner of the offering.

Binding resources
-----------------

WStore supports bind registered resources with created offerings using the offering management API. To perform the binding, it is necessary to have the resources info, so may be useful to make a getting resources request as defined in the resources management section. ::

	POST /api/offering/offerings/{organization}/{name}/{version}/bind
	Content-Type: application/json
	{

	   “resources”: [{
	        "provider": "app_provider",
	        "name": "Smart City Management",
	        "version": "1.0"
	   },

	   {
	        "provider": "app_provider",
	        "name": "HistoryMod",
	        "version": "1.0"
	   }]

	}


WStore returns a 200 OK code in case the request is successful.

The binding process is an absolute update, that is, when the request finishes, the offering resources are the same as the contained in the request. Note that this action only can be performed if the offering is not published.

Publishing an offering
----------------------

WStore supports publishing an offering using the offerings management API, Publishing an offering means start selling it. Note that in this request is possible to select in what Marketplaces (WStore must be registered on them) the offering is going to be published. It is also possible not publishing the offering in any Marketplace. ::

	POST /api/offering/offerings/{organization}/{name}/{version}/publish
	Content-Type: application/json
	{

	   “marketplaces”: [“testbed_marketplace”,]

	}


WStore returns a 200 OK code in case the request is successful.

The marketplaces list contains the name of the different Marketplaces as was included in WStore when WStore was registered in those marketplaces.


Deleting an offering
--------------------

WStore supports to delete offerings via API. Note if the offering has been published it is not deleted but its state is changed to deleted. ::

	DELETE /api/offering/offerings/{organization}/{name}/{version} HTTP 1.1


WStore returns a 204 No content code if the request is successful

Purchases
=========

Purchase API integration
------------------------

WStore supports to integrate purchases with different external applications using the purchases API directly. Using this method to integrate purchases requires the developer to take into account the payment method since it is possible that it needs to redirect users to the PayPal confirmation page.

The requests to perform a purchase directly using the purchases API are different depending on the payment method selected.

* Credit card

	The following request shows how to perform a purchase using a credit card. If no tax address or credit card provided, then default values stored in user’s profile are used. Moreover, the field offering used to identify the offering to be purchased could contain different values, apart for the method used in the request (organization, name, version), it is also possible to provide the URL of the USDL in the Repository GEi (description_url field in offering requests), this method is useful to purchase offerings that have been searched in a Marketplace GEi. The plan label field is used to identify the price plan when there are more than one, if only a plan exists this field is not mandatory. ::

		POST /api/contracting HTTP 1.1
		Content-Type: application/json
		{
		   “offering”: {
		       “organization”: "CoNWeT"
		       “name”: "SmartCityLights"
		       “version”: "1.0"
		   },
		   "plan_label": "update",
		   “tax_address”: {
		       “street”: "C/Los alamos n 17",
		       “city”: "Santander",
		       “postal”: "39011",
		       “country”: "Spain"
		   }
		   “payment_info”: {
		       “payment_method”: “credit card”,
		       “credit_card”: {
		           “number”: "546798367265",
		           “type”: "MasterCard",
		           “expire_year”: "2018",
		           “expire_month”: "5",
		           “cvv2”: "111"
		       }
		   }
		}

	WStore responds with a 201 Created code is the request is successful.

* PayPal

	The following request shows how to perform a purchase using a PayPal account. Note that if no tax address provided the default value is used. ::

		POST /api/contracting HTTP 1.1
		Content-Type: application/json
		Accept: application/json
		{ 
		    “offering”: {
		        “organization”: "CoNWeT"
		        “name”: "SmartCityLights"
		        “version”: "1.0"
		    },
		    "plan_label": "update",
		    “tax_address”: {
		        “street”: "C/Los alamos n 17",
		        “city”: "Santander",
		        “postal”: "39011",
		        “country”: "Spain"
		    }
		    “payment_info”: {
		        “payment_method”: “paypal”
		    }
		}


	If the request is success WStore will respond with a redirection URL. This URL is created by PayPal and the user browser should be redirected to that window, since, PayPal requires user authentication and confirmation to perform the payment.
	
	Response: ::

		HTTP/1.1 200 OK
		Content-Type: application/json
		Vary: Cookie

		{
		    "redirection_link": "http://paypalredirectionlink.com/"
		}


Purchase redirection integration
--------------------------------

WStore also supports to integrate external applications with the purchase process using WStore web interface to perform the payment. To integrate an application using this method, the client application requests for a purchase formulary for a concrete offering and WStore responds with a redirection URL where the client application should redirect the user browser in order to start the purchasing process. ::

	POST /api/contracting/form HTTP 1.1
	Content-Type: application/json
	Accept: application/json
	{
	    "offering": {
	        "organization": "CoNWeT",
	        "name": "SmartCityLights",
	        "version": 1.0,
	    },
	    "redirect_uri": "http://customerredirecturi.com"
	}

Note that the offering field, used to identify the offering, could also contain the URL pointing to the USDL description in the Repository GEi (description_url field in offering request) in order to allow to integrate WStore with a solution that uses a Marketplace GEi for searching offerings.

Response: ::

	HTTP/1.1 200 OK
	Content-Type: application/json
	Vary: Cookie

	{
	    "url": "http://wstore.lab.fi-ware.eu/contracting/form?ID=63865adf6c2ca6f7"
	}


The URL returned should be used to redirect the user browser. This URL points to a formulary that allows the user to pay using the WStore GUI.

When the user ends the purchase, the window is closed and WStore sends a notification to the client application using the redirect URI provided in the call.

Purchases notifications
-----------------------

When a service provider publish an offering in WStore, s/he should provide an URL where s/he can receive a notification when her offering is purchased in order to know the customer and the purchase reference. The provided URL should support a POST request with the following structure. ::

	POST notification_url HTTP 1.1
	Content-Type: application/json
	{
	    "offering": {
	        "organization": "CoNWeT",
	        "name": "SmartCityLights",
	        "version": "1.0"
	    }
	    "reference": "51c2d2825d9af944d0d1cfe0",
	    "customer": "santander_crm"
	}


Accounting and Pay-Per-Use integration
======================================

If a service provider wants to provide a service under a pay-per-use pricing model, it is necessary to develop some modules in charge of providing accounting info to WStore in order to allow it to perform the charging process. To perform the accounting process, the service provider must have received the purchase notification as defined in the previous section since the offering, the customer, and the reference are required.

The accounting request is defined as follows: ::

	POST /api/contracting/{reference}/accounting HTTP 1.1
	Content-Type: application/json
	{
	    “offering”: {
	        “name”: “offering_name”
	        “version”: “1.0”
	        “organization”: “organization”
	    },
	    "component_label": "issues",
	    “customer”: “test_user”,
	    “correlation_number”: “1”,
	    “time_stamp”: “2013-07-01T10:00:00-0”,
	    “record_type”: “event”,
	    “value”: “1”,
	    “unit”: “issue”
	}

