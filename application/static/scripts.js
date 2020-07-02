function toggleElement(checkbox_id, element_to_toggle, attribute, attribute_value) {
  var checkBox = document.getElementById(checkbox_id);
  var thing = document.getElementById(element_to_toggle);
  if (checkBox.checked == true) {
    thing.setAttribute(attribute, attribute_value);
  } else {
    thing.removeAttribute(attribute)
  }
}

function toggleProperty(checkbox_id, element_to_toggle, attribute, attribute_value) {
  var stuff = document.getElementById(element_to_toggle);

  var checkBox = document.getElementById(checkbox_id);
  if (checkBox.checked == true) {
    stuff.style.setProperty(attribute, attribute_value);
  } else {
    stuff.style.removeProperty(attribute)
  }
}

function sendRequest(target, method, async) {
  var xhr = new XMLHttpRequest();
  xhr.open(method, target, async);
  xhr.setRequestHeader('Content-Type', 'application/json');


  return xhr
}
function validateAndSendPoints() {
  var current = Number(document.getElementById("grade_points").value)
  var max = Number(document.getElementById("max_points").value)
  var text = document.getElementById("point_status")
  var visible = document.getElementById("grade_visible").checked

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
  var submit_id = document.getElementById("submit_id").value
  var data = {
    target: 'feedback',
    submit_id: submit_id,
    update: ["points"],
    points: current,
    visible: visible
  };

  xhr = sendRequest("/update",  "PATCH", true)
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

  var id = event.target.id;

  if (id === 'send_comment') {
    var status = document.getElementById('comment_submit_status')
    status.innerHTML = "tallennetaan..."
    var txt = document.getElementById('comment_text').value
    var target = document.getElementById("comment_target").value
    var data = {
      text: txt,
      target: target,
      visible: true
 
    }
    console.log(JSON.stringify(data))
    xhr = sendRequest("/comment", "POST", true)
    
    xhr.onload = function () {

      if (xhr.status == 200) {
        status.innerHTML = "tallennettu!"
        getComments(target)
      } else {
        status.innerHTML = "tallennus ei onnistunut"
      }
    }
    xhr.send(JSON.stringify(data));

  }

}

function getComments(target_id) {
  
  console.log("getting comments, target_id: " + target_id)
  
  xhr = sendRequest("/comment", "GET", true)
  xhr.setRequestHeader('Comment-target', target_id);
  xhr.onload = function () {
    if (xhr.status == 200) {
      var comments = JSON.parse(this.responseText);
      $( "#old_comments" ).empty()
      comments.forEach(element => {
        parseAddComment(element)
      });
    } else {
      console.log("Kommenttien haku ei onnistunut")
    }
  }
  xhr.send();
}

function parseAddComment(element) {
  
  var new_comment = `
  
        <tr id="comment_`+element.id+`">
            <td id="header">
                <p class="pl-1">
                    <b> `+element.owner_str+`</b>
                </p>
                <p class="mb-0 pl-1">
                    <b> `+element.date_str+`</b>
                </p>
                </td>
                <td id="comment_text">
                <p style="white-space: pre-wrap;"> `+element.text+`</p>
                </td>
            </tr>

       
  
  `
  $( "#old_comments" ).append( new_comment );
  
}