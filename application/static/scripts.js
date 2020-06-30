function toggleElement(checkbox_id, element_to_toggle, attribute, attribute_value) {
    var checkBox = document.getElementById(checkbox_id);    
    var thing = document.getElementById(element_to_toggle);    
    if (checkBox.checked == true){
        thing.setAttribute(attribute,attribute_value);
    } else {
        thing.removeAttribute(attribute)
    }
} 

function toggleProperty(checkbox_id, element_to_toggle, attribute, attribute_value) {
    var stuff = document.getElementById(element_to_toggle);
    
    var checkBox = document.getElementById(checkbox_id);
    if (checkBox.checked == true){
        stuff.style.setProperty(attribute, attribute_value);
    } else {
        stuff.style.removeProperty(attribute)
    }
}

function sendRequest(target, method, data, async) {
    var xhr = new XMLHttpRequest();
    xhr.open(method, target, async);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(data);
    return xhr
}
