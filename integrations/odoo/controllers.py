# -*- coding: utf-8 -*-

from collections import Counter
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

from django.utils.translation import ugettext as _

from .models import (
    StudentTutorRelationship,
    TutorProfile,
    TeacherProfile,
    StudentProfile,
    MedicalProfile,
    Allergy,
    MedicalCondition,
    Odoo)
from users.forms import (
    InlineEditBasicInfoUserForm,
    TeacherProfileUserForm,
    TutorProfileUserForm
)
from utils.controllers import ControllerResponse

from utils import services as utilities
from userprofiles.models import *

"""
Business logic for the odoo module integration
"""

__version__ = '0.1.0'
__author__ = 'Oscar Gil <info@edoo.io>'
__date__ = '23 September 2016'
__copyright__ = 'Copyright (c) 2012-2016 Samuel Chávez'
__license__ = 'THE LICENSE'
__status__ = 'development'
__docformat__ = 'reStructuredText'

User = get_user_model()


def set_contract(request, username):

    # Get the user data and response
    user = User.objects.get(username=username)

    # Student profile
    student_profile = user.studentprofile

    # Build response
    response = ControllerResponse(request, _(u"Mensaje de respuesta por defecto"))

    # Get student level and contract
    student_level = student_profile.level

    response.sets({
        'user': user,
        'student_profile': student_profile
    })
