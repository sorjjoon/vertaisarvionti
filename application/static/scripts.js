function toggleElement(checkbox_id, element_to_toggle, attribute, attribute_value) {
    var checkBox = document.getElementById(checkbox_id);    
    var thing = document.getElementById(element_to_toggle);    
    if (checkBox.checked == true){
        thing.setAttribute(attribute,attribute_value);
    } else {
        thing.removeAttribute(attribute)
    }
} 

