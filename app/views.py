from flask import render_template, request, redirect, make_response, flash, send_from_directory
from datetime import date
import pandas as pd
import numpy as np

from dateutil.relativedelta import relativedelta
import pickle
from datetime import datetime
from collections import OrderedDict
import os

import logging

## imports for task scheduler
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from flask import send_file
from io import BytesIO

from config import STAGE
from app import app
import app.models  as m
#from app.states import StateManager
#import app.ops as ops
#import app.presentation as pres

####

## scheduler
#scheduler = BackgroundScheduler()
#scheduler.start()
#scheduler.add_job(
#    func=ops.update_repository,
#    trigger=IntervalTrigger(minutes=15),
#    id='FTP_server_scan',
#    name='Periodically scan FTP server and transfer new files',
#    replace_existing=True)

# Shut down the scheduler when exiting the app
#atexit.register(lambda: scheduler.shutdown())
####

#logging.basicConfig()
#logging.getLogger('apscheduler').setLevel(logging.DEBUG)


#@app.context_processor
#def inject_params():
#    last_update = FTPUpdateLog.last_update_str()
#    return dict(last_update=last_update)

@app.template_filter('formatpercent')
def _jinja2_filter_percent(amount):
    if pd.isnull(amount):
        return '--'
    return '{:.0f}{}'.format(100*amount,'%')

@app.route("/", methods=['GET','POST'])
@app.route("/<pathid>", methods=['GET','POST'])
@app.route("/<pathid>/<photoid>", methods=['GET','POST'])
def default_view(pathid=None, photoid=None):
    image = None
    meta = {}
    if not pathid:
        pathid = m.Path.root_path_id
    
    pathname = m.Path.get_full_path(pathid, root=STAGE)

    if photoid:
        photoid = int(photoid)
        image = m.Photo.filename_for(photoid, root=STAGE)


    path = m.Path.query.filter(m.Path.recid==pathid).one()
    actions = path.actions(current_photo_id=photoid)

    if request.method=="POST":
        print("POST")
        for k,v in request.form.items():
            print(k,v)

    return render_template("base.html", meta=meta, actions=actions, path=pathname, image=image)

@app.route("/inventory/<pathid>")
def inventory(pathid):
    path = m.Path.query.filter(m.Path.recid==pathid).one()
    path.inventory()
    flash("inventory complete for " + path.get_full_path(path.recid))
    return redirect("/" + str(path.recid))

#def _repo_viewer_params():
#    params = dict(
#                filter_forms = [#dict(fieldname='FY_key', label='FY', type='select', choices=choices_for("FY_obj"), curval=5), # default FY20
#                            dict(fieldname='program', label='Program', type='select', choices=choices_for("program")),
#                            dict(fieldname='classification', label='File Type', type='select', choices=choices_for("classification")),
#                            dict(fieldname='submitter', label='Provider', type='select', choices=choices_for("submitter")),
#                            dict(fieldname='within_last', label='Uploaded in the Last', type='select', choices=choices_for("within_last"), curval=7),
#                            dict(fieldname='date_from', label='Uploaded Since', type='date'),
#                            dict(fieldname='status', label='Status', type='select', choices=choices_for("status"))
#                    ],
#                
#                sort_order = ['time_modified'],
#                sort_direction = [False],
#                data = None,
#                mode='display'
#                )
#    return params
#
#_configs = StateManager(default_init=_repo_viewer_params)
#
#def repo_viewer_actions_for(mode='filter', inits={}):
#    actions = []
#    if mode=='filter':
#        actions = [pres.render_button(name='fetch',label='View Files',style='warning')]
#
#    elif mode=='display':
#        actions = [pres.render_button(name='set_mode',value='filter',label='Set Filters',style='default')]
#    
#    universal_actions = []
#
#    actions = actions + universal_actions
#    return actions
#
#def _init_TLS_Monthly_Worklist():
#    params = [dict(fieldname='program', label='Program', type='select', choices=choices_for("program"), curval='TLS'),
#             dict(fieldname='classification', label='File Type', type='select', choices=choices_for("classification"), curval='report'),
#             dict(fieldname='submitter', label='Provider', type='select', choices=choices_for("submitter")),
#             dict(fieldname='within_last', label='Uploaded in the Last', type='select', choices=choices_for("within_last"), curval=32),
#             dict(fieldname='date_from', label='Uploaded Since', type='date'),
#             dict(fieldname='status', label='Status', type='select', choices=choices_for("status"), curval='new')]
#    return params
#
#_custom_views_dict = {}
#_custom_views_dict['TLS Monthly Worklist'] = _init_TLS_Monthly_Worklist
#
#_custom_views_buttonset = []
#for label in _custom_views_dict.keys():
#    _custom_views_buttonset.append(pres.render_button(name='load_view',label=label,style='default',value=label))
#
#@app.route("/view_OCJ_repo", methods=['GET','POST'])
#@app.route("/view_OCJ_repo/<config_id>", methods=['GET','POST'])
#def view_repo_viewer(HOME='LEGAL_SERVICES', config_id=None):
#    user_IP = request.remote_addr
#
#    if True:
#        config = _configs.get(config_id)
#        config_id = config.id
#        redirectURL = "/view_OCJ_repo/" + str(config_id)
#       
#        filters = {}
#        for f in config.get("filter_forms"):
#            curval = f.get('curval','')
#            if curval not in ('','None'):
#                filters[f['fieldname']] = curval
#        html = FTPMeta.fetch(format='html', **filters)
#        config.set("html",html)
#
#        if request.method=="POST":
#            if 'fetch' in request.form.keys():
#                filter_forms = []
#                for f in config.get("filter_forms"):
#                    fieldname = f['fieldname']
#                    v = request.form[fieldname]
#                    if v not in ('','None'):
#                        try:
#                            f['curval'] = int(v)
#                        except (TypeError, ValueError):
#                            f['curval'] = v
#                    else:
#                        f['curval'] = ''
#                    filter_forms.append(f)
#                config.set("filter_forms",filter_forms)
#                config.set("mode","display")
#                return redirect(redirectURL)
#
#            if 'set_mode' in request.form.keys():
#                config.set("mode",request.form['set_mode'])
#                return redirect(redirectURL)
#
#            if 'download' in request.form.keys():
#                fileid = request.form['download']
#                D = FTPRepo.query.filter(FTPRepo.recid==int(fileid)).one()
#                dirpath = FTP_REPO
#                filename = D.filename
#                print("downloading file",dirpath,filename)
#                return send_from_directory(dirpath, filename, as_attachment=True)
#            
#            if 'mark_processed' in request.form.keys():
#                fileid = request.form['mark_processed']
#                D = FTPRepo.query.filter(FTPRepo.recid==int(fileid)).one()
#                D.set_status("processed")
#                return redirect(redirectURL)
#            
#            if 'send_to_gobbler' in request.form.keys():
#                fileid = request.form['send_to_gobbler']
#                D = FTPRepo.query.filter(FTPRepo.recid==int(fileid)).one()
#                dirpath = FTP_REPO.replace('\\','%5C')
#                filename = D.filename
#                print("staging to gobbler",dirpath,filename)
#                URL = GOBBLER + "/filename=" + dirpath + filename + ';provider=' + D.meta.submitter + ';program=' + D.meta.program
#                print("redirecting",URL)
#                return redirect(URL)
#
#            if 'load_view' in request.form.keys():
#                #config_id = request.form['load_view']
#                config = _configs.get(None)
#                config_id = config.id
#                filters = request.form['load_view']
#                config.set("filter_forms",_custom_views_dict[filters]())
#                return redirect("/view_OCJ_repo/" + str(config_id))
#
#        buttonset =  repo_viewer_actions_for(config.get("mode"))
#        session = dict(
#            filters=config.get("filter_forms"),
#            custom_views=_custom_views_buttonset
#        )
#
#        html = config.get("html")
#        
#        return render_template("repo_browser.html", html=html, mode=config.get("mode"), session=session, buttonset=buttonset)
#    flash("not authorized")
#    return redirect("/")
#
#@app.route("/seek", methods=['GET','POST'])
#@app.route("/seek/<raw>", methods=['GET','POST'])
#def seek_view(raw=None):
#    if request.method=='GET':
#        frags = raw.split(";")
#        tokens = {}
#        for frag in frags:
#            token, val = frag.split("=")
#            tokens[token] = val
#
#        print("FTP seek request")
#        print(tokens)
#        print(request.headers.get("User-Agent"))
#
#    return redirect("/")
#    #return render_template("search.html")
#
#@app.route("/post", methods=['GET','POST'])
#@app.route("/post/<tokens>", methods=['GET','POST'])
#def post_view(DOMAIN=LGL_SVCS, tokens=None):
#
#    docs_form = OrderedDict()
#    docs_form['domain'] = dict(fieldname='domain',label='domain',type='select',curval=DOMAIN, choices=[{'label':v, 'value':v} for v in ['LEGAL_SERVICES']])
#    docs_form['destination'] = dict(fieldname='destination',label='recipient',type='select',curval='', choices=[{'label':'', 'value':''}] + [{'label':k, 'value':v} for k,v in sorted(lgl_svcs_dirs_dict.items())])
#    if request.method=="POST":
#        if 'post_to_server' in request.form:
#            f = request.files.get('upload_file',None)
#            if f:
#                f.save(os.path.join(FTP_OUTBOUND, f.filename))
#                doc_inputs = {'filename':f.filename,\
#                            'pathname':FTP_OUTBOUND}
#                for fieldname, field in docs_form.items():
#                    stage_val = ''
#                    if fieldname in request.form.keys():
#                        stage_val = request.form[fieldname]
#                        doc_inputs[fieldname] = stage_val
#                        if fieldname=='destination':
#                            if str(stage_val) in ('None',''):
#                                flash("No recipient selected")
#                                return redirect("/post")
#                success, msg = ops.post_to_server(**doc_inputs) 
#                ops.refresh_uploads(nodes=[doc_inputs['destination']])
#                if not success:
#                    flash(msg)
#            return redirect("/post")
#
#    recent = ops.recent_uploads()
#    return render_template("post.html", docs_form=docs_form, recent=recent)
#
#@app.route("/jobs", methods=['GET','POST'])
#@app.route("/jobs/<tokens>", methods=['GET','POST'])
#def jobs_view(tokens=None):
#    flash("not yet...")
#    return redirect("/")
#
#@app.route("/update_repo", methods=['GET','POST'])
#def update_view():
#    msg = ops.update_repository()
#    flash(msg)
#    return redirect('/')
#
#@app.route("/update_repo_past_month", methods=['GET','POST'])
#def update_view_past_month():
#    msg = ops.update_repository_30_day_lookback()
#    flash(msg)
#    return redirect('/')
#
#@app.route("/update_repo_past_year", methods=['GET','POST'])
#def update_view_past_year():
#    msg = ops.update_repository_one_year()
#    flash(msg)
#    return redirect('/')
#
#@app.route("/update_repo_by_node/<node>", methods=['GET','POST'])
#@app.route("/update_repo_by_node/<node>/<days>", methods=['GET','POST'])
#def update_view_by_node(node, days=30):
#    date_from = date.today() - relativedelta(days=days)
#    msg = ops.update_repository(nodes=[node], scope='since', date_from=date_from)
#    flash(msg)
#    return redirect('/')
