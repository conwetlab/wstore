# Introduction to WStore

.fx: cover

@conwet

---

## Introduction

.fx: section-title

---
## Introduction

* WStore is the reference implementation of the Store GE, and enables selling digital assets (i.e. applications, services and data) for consumers as well as developers of future Internet applications, and is responsible for managing offerings and sales 

* WStore supports:
    - Registration and publication of new offerings by application/service and data providers
    - Contracting of applications/services and data
    - Gathering application/services (including data services) usage accounting info
    - Charging for the acquisition and usage of application/services, on the basis of the predefined price model. 

* WStore is offered under a EUPL (European Union Public Licence) v 1.1+

---
## Basic Concepts

.fx: section-title

---
## Offerings and resources

* WStore separates the concepts of resource and offering in order to give flexibility to service providers that want to create composite offerings that include multiple digital assets of different types

    - Resources are the concrete digital assets being sold in WStore. WStore allows the registration of API resources or downloadable resources (e.g a widget, an app, etc.)

    - Offerings are the abtractions used in WStore where resources are offered, taking into account that an offering can include any number of resources and that a resource can be offered in multiple offerings

---
## Roles

* WStore defines some roles that allow the users of the system to perform different actions.

* Users must have at least one and may have any number of roles. The user roles defined depending on the privileges and possible interactions with WStore are as follows:

    - **Admin**: This role is responsible for system administration. System administration includes database administration, as well as the registration of instances of the different GEis which WStore is integrated with
    - **Provider**: This role has the option of publishing service offerings 

---
## Roles

* Wstore roles:
    - **Customer**: This role has the option of acquiring an offering that may or may not become part of the services acquired by any of the organizations of which the customer is a member.
    - **Developer**: This role has the option of acquiring an offering that define a special price plan for developers that may include a revenue sharing model between the provider and the customer.

---
## Pricing

* Offerings in WStore contain pricing models. These models are used by WStore in order to calculate the amount to be charged to the different customers that have acquire an offering.

* Pricing models in WStore are based on the combination of three types of basic models:
    - Single payment: This basic model defines a payment that is charged once when the offering is acquired
    - Subscription: This basic model defines a payment that is charged once when the offering is acquired and then is charged periodically.
    - Pay-per-use: This basic model defines a payment that depends on the use made by the customer of the acquired resources.

---
## Architecture

.fx: section-title

---
## Architecture

<img class="im" src="images/Arq_store_FMC.png"/>

---