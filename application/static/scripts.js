function toggleElement(checkbox_id, element_to_toggle, attribute, attribute_value) {
  const checkBox = document.getElementById(checkbox_id);
  const thing = document.getElementById(element_to_toggle);
  
  if (checkBox.checked == true) {
    thing.setAttribute(attribute, attribute_value);
  } else {
    thing.removeAttribute(attribute)
  }
}

function toggleProperty(checkbox_id, element_to_toggle, attribute, attribute_value) {
  const stuff = document.getElementById(element_to_toggle);

  const checkBox = document.getElementById(checkbox_id);
  
  if (checkBox.checked == true) {
    stuff.style.setProperty(attribute, attribute_value);
    
  } else {
    stuff.style.removeProperty(attribute)
  }
}

function sendRequest(target, method, async) {
  const xhr = new XMLHttpRequest();
  xhr.open(method, target, async);
  xhr.setRequestHeader('Content-Type', 'application/json');
  return xhr
}
function swapClass(element1, element2, cssClass) {
  $(element1).addClass(cssClass);
  $(element2).removeClass(cssClass);
}

function validateAndSendPoints() {
  const current = Number(document.getElementById("grade_points").value)
  const max = Number(document.getElementById("max_points").value)
  const text = document.getElementById("point_status")
  const visible = document.getElementById("grade_visible").checked

  if (isNaN(max)) {
    return
  }

  if (isNaN(current)) {
    text.innerHTML = "pisteiden täytyy olla numero"
    return
  }

  if (max < current) {
    text.innerHTML = "pisteet eivät voi olla maksimipisteitä suurempia"
    return
  }

  text.innerHTML = "päivitetään... (uudet pisteet " + current + ")"
  const submit_id = document.getElementById("submit_id").value
  const data = {
    target: 'feedback',
    submit_id: submit_id,
    update: ["points"],
    points: current,
    visible: visible
  };

  xhr = sendRequest("/update", "PATCH", true)
  xhr.onload = function () {

    if (xhr.status == 200) {
      text.innerHTML = "tallennettu!"
    } else {
      text.innerHTML = "tallennus ei onnistunut"
    }

  }
  xhr.send(JSON.stringify(data));

}

function sendComment(event) {
  const id = event.target.id;
  clear_old_comments()
  if (id === 'send_comment') {
    var status = document.getElementById('comment_submit_status')
    status.innerHTML = "tallennetaan..."
    const txt = document.getElementById('comment_text')
    const target = document.getElementById("comment_target").value
    const data = {
      text: txt.value,
      target: target

    }
    xhr = sendRequest("/comment", "POST", true)

    xhr.onload = function () {

      if (xhr.status == 200) {
        status.innerHTML = "tallennettu!"
        txt.value = ""
        getCommentsJSON(target)
      } else {
        status.innerHTML = "tallennus ei onnistunut"
      }
    }
    xhr.send(JSON.stringify(data));

  }
 
}
function getCommentsHTML(target_id, onloadFunc) {
  xhr = sendRequest("/comment", "GET", true);
  xhr.setRequestHeader('X-Comment-Target', target_id);
  xhr.setRequestHeader("Accept:", "text/html");
  xhr.onload = onloadFunc;
  xhr.send();

}

function getCommentsJSON(target_id, onloadFunc) {
  xhr = sendRequest("/comment", "GET", true)
  xhr.setRequestHeader('X-Comment-Target', target_id);
  xhr.setRequestHeader("Accept", "application/json")
  xhr.onload = onloadFunc
  xhr.send();
}


function parseAddComment(element) {

  const new_comment = `
  
        <tr id="comment_`+ element.id + `">
            <td id="header">
                <p class="pl-1">
                    <b> `+ element.owner_str + `</b>
                </p>
                <p class="mb-0 pl-1">
                    <b> `+ element.date_str + `</b>
                </p>
                </td>
                <td id="comment_text">
                <p style="white-space: pre-wrap;"> `+ element.text + `</p>
                </td>
            </tr>`
  $("#old_comments").append(new_comment);

}

function swapIntoInput(element, new_element_str, target_url, method, status_elemnt, key_to_change) {
  const new_element = document.createElement("div")
  const old_element = element
  $(new_element).html(new_element_str);
  $(element).replaceWith(new_element);
  new_element.onupdate = function () {
    status_elemnt.text = "päivitetään..."
    $(new_element).replaceWith(old_element);
    data = {}
    data[key_to_change] = new_element.text

    xhr = sendRequest(target_url, method, true)
    
    xhr.onload = function () {
      if (xhr.status == 200) {
        status_elemnt.text = "Päivitys onnistui!"
      } else {
        status_elemnt.text = "Päivitys epäonnistui ("+xhr.code+")"
      }
    }
    
    xhr.send(JSON.stringify(data))
  }

}


function createDropdown(id, iconLink) {
  const dropdownToggle = '<a id="'+id+'" class="btn btn-link " role="button" data-toggle="dropdown" aria-haspopup="true"  aria-expanded="false"><img id="settings_icon" src="'+iconLink+'"></a>';
  const drowdownMenu = '<div id="'+id+'" class="dropdown-menu" data-display="static" aria-labelledby="'+id+'"></div>';
  const dropdownToggleHTML = $.parseHTML( dropdownToggle, keepScripts=true)
  const drowdownMenuHTML = $.parseHTML( drowdownMenu, keepScripts=true )
  return [dropdownToggleHTML, drowdownMenuHTML]
}

String.prototype.formatString = String.prototype.formatString ||
function () {
    
    var str = this.toString();
    if (arguments.length) {
        var t = typeof arguments[0];
        var key;
        var args = ("string" === t || "number" === t) ?
            Array.prototype.slice.call(arguments)
            : arguments[0];

        for (key in args) {
            str = str.replace(new RegExp("\\{" + key + "\\}", "gi"), args[key]);
        }
    }

    return str;
};

