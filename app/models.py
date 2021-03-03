from sqlalchemy.inspection import inspect
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import func

from app import db
from config import ROOT#, STAGE

import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import os

#association_photo_tag = db.Table('photo_tag', db.metadata,
#            db.Column('photoid', db.Integer, db.ForeignKey('Photo.recid')),
#            db.Column('tagid', db.Integer, db.ForeignKey('Tag.recid')))
#
#class Tag(db.Model):
#    __tablename__ = 'tag'
#    recid = db.Column(db.Integer, primary_key=True)
#    segment = db.Column(db.String)

class Photo(db.Model):
    __tablename__ = 'photo'
    recid = db.Column(db.Integer, primary_key=True)
    pathid = db.Column(db.Integer, db.ForeignKey('path.recid'))
    filename = db.Column(db.String)
    date_created = db.Column(db.Date)
    date_indexed = db.Column(db.Date)
    invisible = db.Column(db.Boolean, default=False)
    viewed = db.Column(db.Boolean, default=False)
    touches = db.Column(db.Integer, default=0)

    meta = db.relationship('PhotoMeta', backref='photo', uselist=False)
#    tags = db.relationship('Tag', secondary='association_photo_tag', back_populates='photos')
   
    @hybrid_method
    def add_photo(self, pathid, filename):
        try:
            exists = Photo.query.filter(Photo.pathid==int(pathid), Photo.filename==filename).one()
        except NoResultFound:
            frags = filename.split(".")
            xtn = frags[-1].lower()
            if xtn in ['jpg','jpeg','tiff','tif','png','gif']:
                try:
                    addP = Photo(pathid=int(pathid), filename=filename, date_indexed=datetime.date.today())
                    db.session.add(addP)
                    db.session.commit()

                except NoResultFound:
                    print("Photo.add_image ERROR: invalid pathid: " + str(pathid))
            else:
                print("ignoring file",filename,pathid)

    @hybrid_method
    def filename_for(self, photoid, root=None):
        p = Photo.query.filter(Photo.recid==int(photoid)).one()
        p.viewed = True
        p.touches += 1
        db.session.commit()
        return os.path.join(Path.get_full_path(p.pathid, root=root), p.filename)

    @hybrid_property
    def download_button(self):
        html = '<button class="btn btn-default" type="submit" name="doc_download" value="' + str(self.id) + '"><span class="glyphicon glyphicon-download-alt"></span></button>'
        return html
    
    @hybrid_property
    def explorer_button(self):
        html = '<button class="btn btn-default" type="submit" name="doc_launch_explorer" value="' + str(self.id) + '"><span class="glyphicon glyphicon-certificate"></span></button>'
        return html

    @hybrid_method
    def insert_or_update(self, **kwargs):
        doc = None
        status = 'failed'
        try:
            doc = FTPRepo.query.filter(FTPRepo.filename==kwargs['filename'], FTPRepo.node==kwargs['node']).one()
            status = 'updated'
        except:
            doc = FTPRepo(date_created = kwargs['date_modified'])
            db.session.add(doc)
            status = 'inserted'
        
        frags = kwargs['filename'].split(".")
        if len(frags)==1:
            kwargs['filetype']='unknown'
        else:
            kwargs['filetype'] = frags[-1]
        for k,v in kwargs.items():
            try:
                setattr(doc, k, v)
            except AttributeError:
                print("FTPRepo failed to set attribute " + k + " " + str(v))
        db.session.commit()
        FTPMeta.insert(doc)
        return status 

    @hybrid_method
    def delete_doc(self, docid):
        try:
            D = FTPRepo.query.filter(FTPRepo.id==docid).one() 
            D.active = False
            db.session.commit()
            return ''
        except NoResultFound:
            return "No document with id " + str(docid) + " was found"

    @hybrid_method
    def set_status(self, status):
        self.meta.status = status
        db.session.commit()

class Path(db.Model):
    __tablename__ = 'path'
    recid = db.Column(db.Integer, primary_key=True)
    parentid = db.Column(db.Integer, db.ForeignKey(Photo.recid))
    depth = db.Column(db.Integer)
    segment = db.Column(db.String)
    invisible = db.Column(db.Boolean, default=False)

    @hybrid_property
    def children(self):
        return Path.query.filter(Path.parentid==self.recid, Path.invisible==False).all()

    @hybrid_property
    def parent(self):
        if self.parentid:
            return Path.query.filter(Path.recid==self.parentid).one()
        return None

    @hybrid_property
    def images(self):
        return Photo.query.filter(Photo.pathid==self.recid, Photo.invisible==False).order_by(Photo.filename).all()

    @hybrid_method
    def get_full_path(self, pathid=None, root=None):
        if not pathid:
            return Path.get_full_path(Path.root_path_id)
        P = Path.query.filter(Path.recid==pathid).one()
        path = P.segment
        print("build path",pathid,path)
        while P.parent:
            P = P.parent
            #print("in while",P.recid,P.parent)
            if root:# and not P.parent:
                path = os.path.join(root, path)
            else: 
                path = os.path.join(P.segment, path)
        return path

    @hybrid_method
    def actions(self, **kwargs):
        actions_for = []
        actions_for.append('<a href="/inventory/' + str(self.recid) + '"><span class="glyphicon glyphicon-search"></span></a>')
        if self.parent:
            actions_for.append('<a href="/' + str(self.parentid) + '"><span class="glyphicon glyphicon-arrow-up"></span></a>')
        for c in self.children:
            actions_for.append('<a href="/' + str(c.recid) + '"><span class="glyphicon glyphicon-folder-open"></span>' + c.segment + '</a>')
        for i in self.images:
            if kwargs.get('current_photo_id',None)==i.recid:
                actions_for.append('<a href="/' + str(self.recid) + '/' + str(i.recid) + '" style="background-color:mistyrose;"><span class="glyphicon glyphicon-eye-open" style="color:red;"></span> ' + i.filename + '</a>')
            elif i.viewed:
                actions_for.append('<a href="/' + str(self.recid) + '/' + str(i.recid) + '"><span class="glyphicon glyphicon-picture"></span> ' + i.filename + '</a>')
            else:
                actions_for.append('<a href="/' + str(self.recid) + '/' + str(i.recid) + '"><span class="glyphicon glyphicon-flash" style="color:green;"></span> ' + i.filename + '</a>')
        return actions_for 

    @hybrid_method
    def add_segment(self, parentid, segment):
        try:
            exists = Path.query.filter(Path.parentid==int(parentid), Path.segment==segment).one()
        except NoResultFound:
            try:
                parent = Path.query.filter(Path.recid==int(parentid)).one()

                addP = Path(parentid=int(parentid), segment=segment, depth=parent.depth + 1)
                db.session.add(addP)
                db.session.commit()

            except NoResultFound:
                print("Path.add_segment ERROR: invalid parentid: " + str(parentid))

    @hybrid_method
    def inventory(self, recid=None):
        if recid:
            self = Path.query.filter(Path.recid==recid).one()

        os.chdir(self.get_full_path(self.recid))
        for item in os.listdir():
            if os.path.isdir(item):
                Path.add_segment(self.recid, item)
            else:
                Photo.add_photo(self.recid, item)

    @hybrid_property
    def root_path_id(self):
        try:
            return Path.query.filter(Path.depth==0).one().recid
        except NoResultFound:
            rootPath = Path(parentid=None, depth=0, segment=ROOT)
            db.session.add(rootPath)
            db.session.commit()
            return Path.root_path_id

class PhotoMeta(db.Model):
    __tablename__ = 'photo_meta'
    recid = db.Column(db.Integer, primary_key=True)
    photoid = db.Column(db.Integer, db.ForeignKey(Photo.recid))
    classification = db.Column(db.String)
    program = db.Column(db.String)
    submitter = db.Column(db.String)
    status = db.Column(db.String)
    time_touched = db.Column(db.DateTime)
    time_updated = db.Column(db.DateTime)
    
    attrnames = ['fileid','classification','program','submitter','status','time_touched','time_updated']
    display_cols = ['fileid','time_modified','filename','submitter','program','classification','status']

    def __getattr__(self, attrname):
        if not attrname.startswith("_"):
            if self.doc is not None:
                return getattr(self.doc, attrname)
        else:
            raise AttributeError("%r object has no attribute %r" % (self.__class__, attrname))

    @hybrid_method
    def fetch(self, format='df', **filters):
        print("fetch")
        print(filters)
        Q = FTPMeta.query.join(FTPRepo)
        for k,v in filters.items():
            if k=='date_from':
                Q = Q.filter(FTPRepo.date_modified>=v)
            elif k=='within_last':
                ref_date = datetime.date.today() - relativedelta(days=int(v))
                Q = Q.filter(FTPRepo.date_modified>=ref_date)
            else:
                model_attr = getattr(FTPMeta, k)
                Q = Q.filter(model_attr==v)
        results = Q.order_by(FTPRepo.time_modified.desc()).all()
        if format=='df':
            return self.format_df(results)
        elif format=='html':
            return self.format_html(results)
        else:
            return self.format_df(results)

    @hybrid_method
    def insert(self, F):
        exists = FTPMeta.query.filter(FTPMeta.fileid==F.recid).all()
        if exists:
            print("FTPMeta already exists for doc",F.recid,"insert canceled")
            return exists[0]
        meta = GenerateMetaData.generated_metadata(F.recid)
        FM = FTPMeta()
        db.session.add(FM)
        for attrname in self.attrnames:
            print("inserting meta record",getattr(meta, attrname, "WTF" + attrname))
            setattr(FM, attrname, getattr(meta, attrname))
        if not FM.status:
            FM.status='new'
        db.session.commit() 


def choices_for(category):
    choices = []
    if category=='within_last':
        choices = [{'label':'', 'value':''}] + \
            [{'label':'day','value':1}, {'label':'week','value':7}, {'label':'month','value':31}]
    else:
        values = [v[0] for v in db.session.query(FTPColumnValues.value).filter(FTPColumnValues.category==category).order_by(FTPColumnValues.value).all()]
        choices = [{'label':'', 'value':''}] + \
        [{'label':v, 'value':v} for v in values] 
    return choices
