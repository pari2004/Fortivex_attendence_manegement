from django.contrib import admin

from ats_shortlisting.models import ATSCandidate, ATSJobDescription

admin.site.register(ATSJobDescription)
admin.site.register(ATSCandidate)
