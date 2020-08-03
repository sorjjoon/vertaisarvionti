

$("form#data").submit(function (e) {
  e.preventDefault();
  var formData = new FormData(this);

  $.ajax({
    url: window.location.pathname,
    type: 'POST',
    data: formData,
    success: function (data) {
      alert(data)
    },
    cache: false,
    contentType: false,
    processData: false
  });
});


function toggleInputs() {
  toggleElement("reveal_after", 'reveal_time', 'disabled', 'disabled')
  toggleElement("reveal_after", 'reveal_date', 'disabled', 'disabled')
}

function test_time_format(str) {
  r = RegExp("^([01]?[0-9]|2[0-3])([\.,\:]?)([0-5][0-9])$")
  return r.test(str)
}




function deleteComment(comment_id, url, success_func, error_func) {
  $.ajax({
    url: url + "?" + $.param({ "id": comment_id }),
    type: 'DELETE',


    error: error_func,
    success: success_func,
    cache: false,
    contentType: false,
    processData: false
  });
}

function generateQuill(container = "#editor", previous = null, theme = "snow", placeholder = "Uusi viesti...") {
  let quill = new Quill(container, {
    theme: theme,
    placeholder: placeholder
  });
  if (previous != null) {
    quill.setContents(previous)
  }
  return quill
}

function modifyComment(commentId) {

  let commentContainer = document.getElementById("comment" + commentId)
  $(commentContainer).addClass("mod")
  let quillContainer = document.getElementById(`quill${commentId}`)
  let q = quillContainer.__quill
  q.enable()
  quillContainer.__initialContents = JSON.parse(JSON.stringify(q.getContents())) //To make a copy of the contents
}

function undoMods(commentId) {
  let commentContainer = document.getElementById("comment" + commentId)
  $(commentContainer).removeClass("mod")
  let quillContainer = document.getElementById(`quill${commentId}`)
  q = quillContainer.__quill
  q.enable(false)
  q.setContents(quillContainer.__initialContents)
  let fileList = document.getElementById(commentId + "fileList")
  for (li of $(fileList).children()) {
    checkbox = $(li).children("input")
    $(checkbox).prop("checked", false);
    link = $(li).children("a")
    $(link).css("text-decoration", "");
  }
}

function submitChanges(button) {
  const commentId = button.value
  let url = button.dataset.url
  let target = button.dataset.comment_target

  let quillContainer = document.getElementById(`quill${commentId}`)
  q = quillContainer.__quill
  let newText = JSON.stringify(q.getContents())

  var form = document.getElementById("form" + commentId)

  let formdata = new FormData(form)
  formdata.append("text", newText)


  $.ajax({
    url: url,
    type: 'POST',
    data: formdata,

    error: function (jqXHR, textStatus, errorThrown) {
      let statusElement = document.getElementById("status" + commentId)
      statusElement.className = ""
      $(statusElement).addClass('error_text')
      if (jqXHR.status == 403) {
        statusElement.innerHTML = "Annetut tiedostot [{0}] olivat liian suuria (max 30 MB)".formatString(jqXHR.responseText)
      } else {

        statusElement.innerHTML = "Viestin tallentaminen ei onnistunut (" + jqXHR.status + ")"
      }
    },
    success: function (data, textStattus, jqXHR) {
      clear_old_comments();
      getCommentsJSON(target, onloadFunction);
      resetNewComment();

    },
    cache: false,
    contentType: false,
    processData: false
  });
}
function clear_old_comments() {
  $("#old_comments").empty();
  $("#old_comments").append('<div class="animation_path"><span id="loading_icon" class="shape trail"></span></div>')     
}
function resetNewComment() {
  $("#new_comment").empty()
  const dummyComment = { id: 0, text: "{}" }
  var newComment = createComment(dummyComment, getCommentTarget(), getCommentUrl(), imageUrl = null, addHeader = false)
  $("#new_comment").append(newComment)
  $("#undo0").on("click", function () { $('#new_comment_button').removeClass('d-none') })
  $('#new_comment_button').removeClass('d-none')
}

function createComment(c, commentTarget, commentUrl = "/comment", imageUrl = "/static/images/icons8-settings.svg", addHeader = true) {

  let commentContainer = document.createElement("div");

  let containerId = "comment" + String(c.id);
  commentContainer.id = containerId
  $(commentContainer).addClass("ql-container ql-snow comment");


  if (addHeader) {
    let headerContainer = document.createElement("header");
    $(headerContainer).append("<span id='owner'>" + c.owner_str + "</span>")
    $(headerContainer).append("<span id='date'>" + c.date_str + "</span>")
    if (c.is_owner && imageUrl != null) {

      let tempArr = createDropdown(c.id + "modify", imageUrl)
      let dropdownToggle = tempArr[0]
      let dropdownMenu = tempArr[1]


      let modifyFunc = "modifyComment('{0}')".formatString(String(c.id))

      $(dropdownMenu).append($.parseHTML('<button onclick="{0}" value="{1}" id="{2}" class="dropdown-item">Muokkaa</button>'.formatString(modifyFunc, c.id, "mod" + c.id), keepScripts = true))

      let deleteUrl = commentUrl
      let errorFuncStr = "function(xhr, textStatus, errorThrown){document.getElementById('{0}status').innerHTML='Viestin postaminen ei onnistunut ('+xhr.status+')' }".formatString(c.id)
      let successFuncStr = "function (data, textStattus, jqXHR) {clear_old_comments();getCommentsJSON('{0}', onloadFunction);}".formatString(commentTarget)
      let onclickTemp = "deleteComment('{0}', '{1}', {2}, {3})".formatString(c.id, deleteUrl, successFuncStr, errorFuncStr)

      $(dropdownMenu).append($.parseHTML('<button  class="dropdown-item" onclick="{0}" id="{1}">Poista</button>'.formatString(onclickTemp, "del" + c.id), keepScripts = true))
      let status = document.createElement("span")
      status.id = String(c.id) + "status"
      $(status).addClass("error_text comment_status")

      $(headerContainer).append(dropdownToggle)
      $(headerContainer).append(dropdownMenu)
      $(headerContainer).append(status)
    }

    $(commentContainer).append(headerContainer);
  }

  let textContainer = document.createElement("div");
  textContainer.id = "quill" + String(c.id)
  $(commentContainer).addClass("text");

  $(commentContainer).append(textContainer);
  let tempQuill = generateQuill(textContainer, contents = JSON.parse(c.text))
  tempQuill.enable(false);
  $(tempQuill).addClass("text");

  let footer = document.createElement("footer");
  footer.id = "footer" + c.id
  let footerForm = document.createElement("form");
  footerForm.id = "form" + c.id
  footerForm.enctype = "multipart/form-data";
  footerForm.autocomplete = "off";
  let listWrapper = document.createElement("div");
  $(listWrapper).addClass("file_list")
  if (Array.isArray(c.files) && c.files.length) {
    let listContainer = document.createElement("ul")
    listContainer.id = c.id + "fileList"
    $(listWrapper).append($.parseHTML("<span id='footer_header'>Liiteet:</span>"))


    for (f of c.files) {
      let liContainer = document.createElement("li")

      $(liContainer).append($.parseHTML(f.link))

      let checkbox = document.createElement("input")
      checkbox.type = "checkbox"
      checkbox.id = "checkFile" + f.id
      checkbox.name = "del_files"
      checkbox.value = f.id
      checkbox.onclick = function () {
        toggleProperty(this.id, "file" + this.value, 'text-decoration', 'line-through')
      }

      $(liContainer).append(checkbox)

      $(listContainer).append(liContainer)
    }
    $(listWrapper).append(listContainer)
  }


  $(footerForm).append(listWrapper)


  let utilsWrapper = document.createElement("div");
  $(utilsWrapper).addClass("utils").append('<input class="new_files" type="file" name="files" multiple>').append('<span id="{0}" class="error_text"> </span>'.formatString("status" + c.id)).append('<button type="button" value="{0}" onclick="undoMods(this.value)" class="btn btn-link" id={1}>Peruuta</button>'.formatString(c.id, "undo" + c.id)).append('<button type="button" value="{0}" data-url="{1}" data-comment_target="{2}"  onclick="submitChanges(this)" class="btn btn-primary" id="{3}">Tallenna</button>'.formatString(c.id, commentUrl, commentTarget, "submit" + c.id))
  if (parseInt(c.id) != 0) {
    $(utilsWrapper).append('<input type="hidden" name="comment_id" value="{0}" id="{1}">'.formatString(c.id, "target" + c.id))

  } else {
    $(utilsWrapper).append('<input type="hidden" name="comment_target" value="{0}" id="{1}">'.formatString(commentTarget, "target" + c.id))
  }
  $(utilsWrapper).append('<input type="hidden" name="reveal_after" value="{0}" id="{1}">'.formatString(c.id, "reveal" + c.id))
  $(footerForm).append(utilsWrapper)
  $(footer).append(footerForm)
  $(commentContainer).append(footer);
  return commentContainer
}

