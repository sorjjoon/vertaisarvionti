
#from application import app, db
from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app, g
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
import datetime
import pytz
import json
from timeit import default_timer as timer
from timeit import default_timer as timer
from application.domain.course import Course
from application import db
         # try:
        #     previous = current_url[:current_url.rindex("/")]
        #     with app.test_client() as tc:
        #         response = tc.get(previous)
        #         if response.status_code == 404:
        #             return previous_url(previous)
        #         else:
                    
        #             return previous
@app.context_processor
def utility_processor():
    def get_file_extension(file_name):
        try:
            extension = file_name[file_name.rindex(".")+1:]
            if extension not in ["3g2","3ga","3gp","7z","aa","aac","ac","accdb","accdt","ace","adn","ai","aif","aifc","aiff","ait","amr","ani","apk","app","applescript","asax","asc","ascx","asf","ash","ashx","asm","asmx","asp","aspx","asx","au","aup","avi","axd","aze","bak","bash","bat","bin","blank","bmp","bowerrc","bpg","browser","bz2","bzempty","c","cab","cad","caf","cal","cd","cdda","cer","cfg","cfm","cfml","cgi","chm","class","cmd","code-workspace","codekit","coffee","coffeelintignore","com","compile","conf","config","cpp","cptx","cr2","crdownload","crt","crypt","cs","csh","cson","csproj","css","csv","cue","cur","dart","dat","data","db","dbf","deb","default","dgn","dist","diz","dll","dmg","dng","doc","docb","docm","docx","dot","dotm","dotx","download","dpj","ds_store","dsn","dtd","dwg","dxf","editorconfig","el","elf","eml","enc","eot","eps","epub","eslintignore","exe","f4v","fax","fb2","fla","flac","flv","fnt","folder","fon","gadget","gdp","gem","gif","gitattributes","gitignore","go","gpg","gpl","gradle","gz","h","handlebars","hbs","heic","hlp","hs","hsl","htm","html","ibooks","icns","ico","ics","idx","iff","ifo","image","img","iml","in","inc","indd","inf","info","ini","inv","iso","j2","jar","java","jpe","jpeg","jpg","js","json","jsp","jsx","key","kf8","kmk","ksh","kt","kts","kup","less","lex","licx","lisp","lit","lnk","lock","log","lua","m","m2v","m3u","m3u8","m4","m4a","m4r","m4v","map","master","mc","md","mdb","mdf","me","mi","mid","midi","mk","mkv","mm","mng","mo","mobi","mod","mov","mp2","mp3","mp4","mpa","mpd","mpe","mpeg","mpg","mpga","mpp","mpt","msg","msi","msu","nef","nes","nfo","nix","npmignore","ocx","odb","ods","odt","ogg","ogv","ost","otf","ott","ova","ovf","p12","p7b","pages","part","pcd","pdb","pdf","pem","pfx","pgp","ph","phar","php","pid","pkg","pl","plist","pm","png","po","pom","pot","potx","pps","ppsx","ppt","pptm","pptx","prop","ps","ps1","psd","psp","pst","pub","py","pyc","qt","ra","ram","rar","raw","rb","rdf","rdl","reg","resx","retry","rm","rom","rpm","rpt","rsa","rss","rst","rtf","ru","rub","sass","scss","sdf","sed","sh","sit","sitemap","skin","sldm","sldx","sln","sol","sphinx","sql","sqlite","step","stl","svg","swd","swf","swift","swp","sys","tar","tax","tcsh","tex","tfignore","tga","tgz","tif","tiff","tmp","tmx","torrent","tpl","ts","tsv","ttf","twig","txt","udf","vb","vbproj","vbs","vcd","vcf","vcs","vdi","vdx","vmdk","vob","vox","vscodeignore","vsd","vss","vst","vsx","vtx","war","wav","wbk","webinfo","webm","webp","wma","wmf","wmv","woff","woff2","wps","wsf","xaml","xcf","xfl","xlm","xls","xlsm","xlsx","xlt","xltm","xltx","xml","xpi","xps","xrb","xsd","xsl","xspf","xz","yaml","yml","z","zip","zsh"]:
                
                extension = "download"
                
        except Exception as e:
            
            extension = "download"
        
        return extension

    def get_deadline_string(deadline, now = datetime.datetime.now(pytz.utc), after=" sitten", before=" jäljellä"):
        if deadline is None:
            return "Ei palautuspäivää"
        
        
        deadline_adjusted = deadline.astimezone(pytz.utc)
        if deadline_adjusted > now:
            diff = deadline_adjusted - now
        else:
            diff = now - deadline_adjusted
        hours = diff.seconds // 3600
        
        minutes = (diff.seconds - 3600*hours)//60
        seconds = (diff.seconds -3600*hours - 60*minutes)
        if diff.days > 1:
            first = str(diff.days)+" päivää ja "

            if hours > 1:
                second = str(hours) + " tuntia"
            elif minutes > 1:
                second = str(minutes)+" minuuttia "
            elif seconds > 1:
                second = str(seconds) +" sekuntia"
        if hours > 1:
            first = str(hours) + " tuntia ja "
            if minutes > 1:
                second = str(minutes)+" minuuttia "
            elif seconds > 1:
                second = str(seconds) +" sekuntia"
        else:
            first = str(minutes)+" minuuttia ja "
            second = str(seconds) +" sekuntia"

        

        if now > deadline_adjusted:
            return first + second+after

        else:
            return first + second+before

        
    def previous_url(current_url):
        try:
            current_url = current_url[:current_url.rindex("/")]
            done = False
            while not done:
                last = current_url[current_url.rindex("/")+1:]
                if last=="overview":
                    done=True
                    continue
                try:
                    int(last)
                    done=True
                    continue
                except:
                    pass
                if "." in last:
                    return "/"
                current_url = current_url[:current_url.rindex("/")]

            return current_url
        except Exception as r:          
            return "/"
    return dict(get_file_extension=get_file_extension, previous_url=previous_url, get_deadline_string=get_deadline_string)


@app.before_request
def validate_user_access():
    g.start = timer()
    if not current_user.is_authenticated:
        return None

    url = request.path
    if "static" in url:
        return None
    
    user_id = current_user.get_id()
    role = current_user.role
    app.logger.info("User %s attempted access to %s", user_id, url)
    if "/overview/" in url:
        if role != "TEACHER":
            return redirect(url_for("index"))
    parts = url.split("/")
    assignment_id = None
    task_id = None
    course_id = None
    
    try:
        for i in range(len(parts)):
            part = parts[i]
            if part =="view":
                course_id = int(parts[i+1])
            elif part=="assignment":
                assignment_id = int(parts[i+1])
            elif part == "task":
                task_id = int(parts[i+1])
    except:
        return None
    if not db.check_access_rights(user_id, current_user.role, course_id=course_id, assignment_id=assignment_id, task_id=task_id):
        
        return redirect(url_for("index"))
        
@app.teardown_request 
def cleanup(f):
    end = timer()
    try:
        if g.start:
            duration = (end - g.start)*1000
            app.logger.info("Request to %s took %s ms", request.path, duration)
        else:
            app.logger.warning("g.start not set for some reason, url: %s", request.path)
    except Exception as r:
        app.logger.error("Error in reques teardown", exc_info = True)

@app.route("/update", methods=["UPDATE"])
def update_element():
    try:
        json_dic = json.loads(request.data)
        target = json_dic.get("target")
        if target=="feedback":
            submit_id = int(json_dic["submit_id"])
            points = int(json_dic["points"])
            visible = json_dic["visible"]
            if visible =="false":
                visible=False
            elif visible == "true":
                visible=True
            else:
                visible = bool(visible)
            db.grade_submit(current_user.get_id(), submit_id,points, visible=visible)

            return Response("", 200)
        else:
            return Response("", 400)
    except (KeyError, ValueError) as r:
        app.logger.error(r, exc_info=True)
        return Response("", 400)

@app.route("/get/<int:file_id>")
@login_required
def get_file(file_id):
    if not db.check_user_view_rights(current_user.get_id(),file_id):
        return Response("", status=403)      
    bin_file, name = db.get_file(file_id)
    if bin_file is None:
        return Response("", status=204)
    buffer = io.BytesIO()
    buffer.write(bin_file)
    buffer.seek(0)
    db.insert_file_log([file_id], current_user.get_id(),"download")
    return send_file(buffer, as_attachment=True, attachment_filename=name)


