from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

DEFAULT_FROM_ADDR = 'LnL <lnl@wpi.edu>'

import pytz
import datetime

from events.models import Event

from django.conf import settings

EMAIL_KEY_START_END = settings.EMAIL_KEY_START_END
EMAIL_TARGET_START_END = settings.EMAIL_TARGET_START_END

def generate_notice_email(notice):
    subject = notice.subject
    from_email = DEFAULT_FROM_ADDR
    to_email = notice.email_to.email
    
    context = {}
    context['object'] = notice
    
    cont_html = render_to_string('emails/email_notice.html',context)
    cont_text = render_to_string('emails/email_notice.txt',context)
    
    email = EmailMultiAlternatives(subject,cont_text,from_email,[to_email])
    email.attach_alternative(cont_html, "text/html")
    
    return email


def generate_notice_cc_email(notice):
    subject = "Lens and Lights Crew List for %s" % notice.meeting.datetime.date
    from_email = DEFAULT_FROM_ADDR
    to_email = "lnl@wpi.edu"
    
    context = {}
    context['object'] = notice

    cont_html = render_to_string('emails/email_notice_cc.html',context)
    cont_text = render_to_string('emails/email_notice_cc.txt',context)
    
    email = EmailMultiAlternatives(subject,cont_text,from_email,[to_email])
    email.attach_alternative(cont_html, "text/html")
    
    return email


def generate_transfer_email(orgtransfer):
    subject = "LNL Organization Control Transfer for %s" % orgtransfer.org.name
    from_email = DEFAULT_FROM_ADDR
    to_email = "%s@wpi.edu" % orgtransfer.old_user_in_charge.username
    
    context = {}
    context['object']  = orgtransfer
    
    cont_html = render_to_string('emails/email_transfer.html',context)
    cont_text = render_to_string('emails/email_transfer.txt',context)
    
    email = EmailMultiAlternatives(subject,cont_text,from_email,[to_email])
    email.attach_alternative(cont_html, "text/html")
    
    return email

def generate_event_start_end_emails():
    subj_start = "Events Starting Now"
    subj_end = "Events Ending Now"
    # get the time
    unstripped = datetime.datetime.now(pytz.utc)
    # get rids of the zeroes
    now = unstripped.replace(second=0,microsecond=0)
    
    # set the headers for majordomo, may need a : after the Approved
    if EMAIL_KEY_START_END:
        headers = {'Approved': EMAIL_KEY_START_END}
    else:
        headers = None
    
    #for the start
    starting = Event.objects.filter(approved=True,datetime_start=now)
    ending = Event.objects.filter(approved=True,datetime_end=now)
    #print now
    #print starting.count()
    #print ending.count()
    
    from_email = DEFAULT_FROM_ADDR
    
    if starting:
        context_start = {}
        context_start['events'] = starting
        context_start['string'] = "Events Starting Now"
        context_start['stringtwo'] = ""
    
        content_start_txt  =render_to_string('emails/email_start_end.txt', context_start)
        content_start_html  =render_to_string('emails/email_start_end.html', context_start)
        
        email = EmailMultiAlternatives(subj_start,content_start_txt,from_email,[EMAIL_TARGET_START_END],headers=headers)
        email.attach_alternative(content_start_html, "text/html")
        email.send()
        #print "sent start email with %s events" % starting.count()
        
    elif ending:
        context_end = {}
        context_end['events'] = ending
        context_end['string'] = "Events Ending Now" 
        context_end['stringtwo'] = "Please help Strike!"
    
        content_end_txt  =render_to_string('emails/email_start_end.txt', context_end)
        content_end_html  =render_to_string('emails/email_start_end.html', context_end)
        
        email = EmailMultiAlternatives(subj_end,content_end_txt,from_email,[EMAIL_TARGET_START_END],headers=headers)
        email.attach_alternative(content_end_html, "text/html")
        email.send()
        #print "sent end email with %s events" % ending.count()
        
    else:
        #print "no events starting/ending"
        pass
        
        
# Cron Example
# * * * * * ~/bin/python ~/lnldb/manage.py send_start_end