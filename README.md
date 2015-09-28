# WStore

 * [Introduction](#introduction)
 * [GEi Overall Description](#gei-overall-description)
 * [Installation](#build-and-install)
 * [API Overview](#api-overview)
 * [API Reference](#api-reference)
 * [Testing](#testing)
 * [Advanced Topics](#advanced-topics)

# Introduction

This is the code repository for WStore, the reference implementation of the Store GE.

This project is part of [FIWARE](http://www.fiware.org). Check also the [FIWARE Catalogue entry for WStore](http://catalogue.fiware.org/enablers/store-wstore)!

Any feedback is highly welcome, including bugs, typos or things you think should be included but aren't. You can use [GitHub Issues](https://github.com/conwetlab/wstore/issues/new) to provide feedback.

You can find the User & Programmer's Manual and the Administration Guide on [readthedocs.org](https://wstore.readthedocs.org)

# GEi Overal Description

WStore provides functionality for the monetization of different kind of digital assets, including the management of assets and offerings as well as support for acquisitions, charging, billing, and accounting of pay-per-use services.


# Installation

The instructions to install WStore can be found at [the Installation Guide](http://wstore.readthedocs.org/en/latest/installation-administration-guide.html). You can install the software in three different ways:

* Using the provided scripts
* Using a [Docker Container](https://hub.docker.com/r/fiware/wstore/)
* Manually

# API Overview

# API Reference

For further documentation, you can check the API Reference available at:

* [Apiary](http://docs.fiwarestore.apiary.io)
* [GitHub Pages](http://conwetlab.github.io/wstore)

# Testing
### End-to-End tests

End-to-End tests are described in the [Installation Guide](http://wstore.readthedocs.org/en/latest/installation-adminstration-guide.html#end-to-end-testing)

### Unit tests

To execute the unit tests, just run:

```
python manage.py test
```

## Advanced Topics

* [User & Programmers Guide](doc/user-programmer-guide.rst)
* [Installation & Administration Guide](doc/installation-administration-guide.rst)

You can also find this documentation on [ReadTheDocs](http://wstore.readthedocs.org)
