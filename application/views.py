
#from application import app, db
from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
import datetime
import pytz
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
            extension = file_name[-1*file_name.rindex("."):]
            if extension not in ["3g2","3ga","3gp","7z","aa","aac","ac","accdb","accdt","ace","adn","ai","aif","aifc","aiff","ait","amr","ani","apk","app","applescript","asax","asc","ascx","asf","ash","ashx","asm","asmx","asp","aspx","asx","au","aup","avi","axd","aze","bak","bash","bat","bin","blank","bmp","bowerrc","bpg","browser","bz2","bzempty","c","cab","cad","caf","cal","cd","cdda","cer","cfg","cfm","cfml","cgi","chm","class","cmd","code-workspace","codekit","coffee","coffeelintignore","com","compile","conf","config","cpp","cptx","cr2","crdownload","crt","crypt","cs","csh","cson","csproj","css","csv","cue","cur","dart","dat","data","db","dbf","deb","default","dgn","dist","diz","dll","dmg","dng","doc","docb","docm","docx","dot","dotm","dotx","download","dpj","ds_store","dsn","dtd","dwg","dxf","editorconfig","el","elf","eml","enc","eot","eps","epub","eslintignore","exe","f4v","fax","fb2","fla","flac","flv","fnt","folder","fon","gadget","gdp","gem","gif","gitattributes","gitignore","go","gpg","gpl","gradle","gz","h","handlebars","hbs","heic","hlp","hs","hsl","htm","html","ibooks","icns","ico","ics","idx","iff","ifo","image","img","iml","in","inc","indd","inf","info","ini","inv","iso","j2","jar","java","jpe","jpeg","jpg","js","json","jsp","jsx","key","kf8","kmk","ksh","kt","kts","kup","less","lex","licx","lisp","lit","lnk","lock","log","lua","m","m2v","m3u","m3u8","m4","m4a","m4r","m4v","map","master","mc","md","mdb","mdf","me","mi","mid","midi","mk","mkv","mm","mng","mo","mobi","mod","mov","mp2","mp3","mp4","mpa","mpd","mpe","mpeg","mpg","mpga","mpp","mpt","msg","msi","msu","nef","nes","nfo","nix","npmignore","ocx","odb","ods","odt","ogg","ogv","ost","otf","ott","ova","ovf","p12","p7b","pages","part","pcd","pdb","pdf","pem","pfx","pgp","ph","phar","php","pid","pkg","pl","plist","pm","png","po","pom","pot","potx","pps","ppsx","ppt","pptm","pptx","prop","ps","ps1","psd","psp","pst","pub","py","pyc","qt","ra","ram","rar","raw","rb","rdf","rdl","reg","resx","retry","rm","rom","rpm","rpt","rsa","rss","rst","rtf","ru","rub","sass","scss","sdf","sed","sh","sit","sitemap","skin","sldm","sldx","sln","sol","sphinx","sql","sqlite","step","stl","svg","swd","swf","swift","swp","sys","tar","tax","tcsh","tex","tfignore","tga","tgz","tif","tiff","tmp","tmx","torrent","tpl","ts","tsv","ttf","twig","txt","udf","vb","vbproj","vbs","vcd","vcf","vcs","vdi","vdx","vmdk","vob","vox","vscodeignore","vsd","vss","vst","vsx","vtx","war","wav","wbk","webinfo","webm","webp","wma","wmf","wmv","woff","woff2","wps","wsf","xaml","xcf","xfl","xlm","xls","xlsm","xlsx","xlt","xltm","xltx","xml","xpi","xps","xrb","xsd","xsl","xspf","xz","yaml","yml","z","zip","zsh"]:
                extension = "download"
        except:
            extension = "download"
        return extension

    def get_deadline_string(deadline):
        if deadline is None:
            return "Ei palautuspäivää"
        now = datetime.datetime.now(pytz.utc)
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
            after = " sitten"
        else:
            after = " jäljellä"
        return first + second+after

    def previous_url(current_url, n):
        try:
            for _ in range(n):
                current_url = current_url[:current_url.rindex("/")]
            
            return current_url
        except:
            return url_for("index")


    return dict(get_file_extension=get_file_extension, previous_url=previous_url, get_deadline_string=get_deadline_string)


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("courses"))
    else:
        return redirect(url_for("login_auth"))
    

@app.route("/enlist", methods = ["GET", "POST"])
@login_required
def enlist_course():
    if current_user.role != "USER":
        return redirect(url_for("index"))
    
    if request.method == "GET":
        return render_template("/student/enlist.html")
    try:
        print("attempting to sign up student "+current_user.get_id()+"for course code "+request.form.get("code"))
        db.enlist_student(request.form.get("code"), current_user.get_id())
        print("successful enlist")
        return redirect(url_for("courses"))
    except ValueError:
        print("invalid code")
        
        return render_template("/student/enlist.html", error="Koodillasi ei löytynyt kurssia")
    except IntegrityError:
        print("duplicate signup")
        return render_template("/student/enlist.html", error="Olet jo ilmoittautunut tälle kurssille")


def set_course_counts(courses:list, counts:list):
    for c in counts:
        id = c[0]
        for course in courses:
            if course.id == id:
                course.count = c[1]
                break

@app.route("/courses")
@login_required
def courses():
    if current_user.role =="TEACHER":
        courses = db.select_courses_teacher(current_user.get_id())
        set_course_counts(courses, db.count_students(current_user.get_id()))
        return render_template("/teacher/teacher_list.html", courses=courses)
    else:
        courses = db.select_courses_student(current_user.get_id())
        return render_template("/student/student_list.html", courses=courses)

@app.route("/view/<course_id>")
@login_required
def view_course(course_id):
    print("user "+str(current_user.get_id())+" accessing index for course "+str(course_id))
    if current_user.role =="USER":
        course = db.select_course_details(course_id, current_user.get_id())
        db.set_assignments(course)
        course.set_timezones("Europe/Helsinki")
        teacher = None
        if course is not None:
            teacher = db.get_user_by_id(course.teacher_id)

        return render_template("/student/course.html", course = course, teacher = teacher)
    elif request.args.get("s")=="1":
        course = db.select_course_details(course_id, current_user.get_id(), is_student=False)
        db.set_assignments(course)
        course.set_timezones("Europe/Helsinki")
        teacher = None
        if course is not None:
            teacher = db.get_user_by_id(course.teacher_id)
            
        return render_template("/student/course.html", course = course, teacher=teacher)
    else:
        course = db.select_course_details(course_id, current_user.get_id(), is_student=False)
        db.set_assignments(course)
        course.set_timezones("Europe/Helsinki")
        teacher = None
        if course is not None:
            teacher = db.get_user_by_id(course.teacher_id)

        return render_template("/teacher/course/course.html", id = course_id, teacher=teacher)




@app.route("/view/<course_id>/students")
@login_required
def view_course_students(course_id):
    students = db.select_students(course_id, current_user.get_id())
    return render_template("/teacher/course/students.html", students = students)
    


    

@app.route("/get/<int:file_id>")
@login_required #TODO validate user has rights to file
def get_file(file_id):         
    bin_file, name = db.get_file(file_id)
    if bin_file is None:
        return Response("", status=204)
    buffer = io.BytesIO()
    buffer.write(bin_file)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, attachment_filename=name)


@app.route("/view/<course_id>/assignment/<assignment_id>")
@login_required
def view_assig(course_id, assignment_id): #TODO rights validations (remember reveal)
    assignment = db.select_assignment(assignment_id)
    db.set_submits(assignment, current_user.get_id())
    assignment.set_timezones("Europe/Helsinki")
    return render_template("/student/assignment/view.html", assignment=assignment, done_string = str(len(assignment.submits))+"/"+str(len(assignment.tasks)))


@app.route("/view/<course_id>/assignment/<assignment_id>/task/<task_id>", methods=["GET", "POST"])
@login_required
def view_task(course_id, assignment_id, task_id):
    if request.method == "GET":
        assignment = db.select_assignment(assignment_id, task_id=task_id)
        
        if assignment.deadline is None:
            deadline_not_passed = True
        else:
            deadline_not_passed = assignment.deadline.astimezone(pytz.utc) > datetime.datetime.now(pytz.utc)
        
        try:
            task = assignment.tasks[0] #all assigs have at least 1 task, so will only happen for manual urls
        except:
            return redirect(url_for("index"))
        
        db.set_submits(assignment,current_user.get_id(), task_id=task.id)
        
        task.files = db.select_file_details(task_id=task.id)
        assignment.set_timezones("Europe/Helsinki")
        return render_template("/student/assignment/view_task.html" ,course_id=course_id, task = task, assignment=assignment, deadline_not_passed=deadline_not_passed)
    else:

        files = request.files.getlist("files")
        db.update_submit(current_user.get_id(),task_id, assignment_id, files)
        return redirect(url_for("view_assig", course_id=course_id, assignment_id=assignment_id))
