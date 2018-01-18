#####################
Odoo-integration
#####################

Integración con software de contabilidad Odoo.


Quik deployment in Ubuntu:

Supponsing we have an virtual environment, we need run following commands in order
to get working on this module and start commiting.

Go to folder where module is instaled:
- cd venv/lib/python2.7/site-packages

Remove current module folder:
- rm -rf odoo

Clone module repo:
- git clone https://github.com/nahualventure/edoo-odoo-integration.git

Rename folder to 'odoo':
- mv edoo-odoo-integration odoo
- cd odoo

Make symlinks to files required by python:
- ln -s odoo/api.py api.py
- ln -s odoo/controllers.py controllers.py
- ln -s odoo/forms.py forms.py
- ln -s odoo/__init__.py __init__.py
- ln -s odoo/services.py services.py
- ln -s odoo/urls.py urls.py
- ln -s odoo/_version.py _version.py
- ln -s odoo/views.py views.py

Start commiting!
